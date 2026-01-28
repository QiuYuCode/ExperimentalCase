const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn, spawnSync } = require('child_process');
const { PythonBridge } = require('./python-bridge');

let mainWindow = null;
let pythonProcess = null;
let pythonBridge = null;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function commandExists(cmd, args = ['--version']) {
  try {
    const result = spawnSync(cmd, args, { stdio: 'ignore' });
    return result.status === 0;
  } catch {
    return false;
  }
}

function getPythonCommand() {
  // Windows 通常是 python；Linux/macOS 通常是 python3
  if (process.platform === 'win32') return 'python';
  if (commandExists('python3', ['--version'])) return 'python3';
  return 'python';
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, '../build/icon.png'),
  });

  if (isDev) {
    // 开发模式：连接到Vite开发服务器
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    // 生产模式：加载打包后的文件
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startPythonBackend() {
  const backendDir = path.join(__dirname, '../backend');
  
  if (isDev) {
    // 开发模式：优先 uv；若不存在则回退到 python 直接运行 run.py
    const runScript = path.join(backendDir, 'run.py');
    if (commandExists('uv', ['--version'])) {
      pythonProcess = spawn('uv', ['run', 'python', runScript], {
        cwd: backendDir,
        stdio: 'inherit',
      });
    } else {
      const py = getPythonCommand();
      pythonProcess = spawn(py, [runScript], {
        cwd: backendDir,
        stdio: 'inherit',
      });
    }
  } else {
    // 生产模式：使用打包后的Python可执行文件
    const exeName = process.platform === 'win32' ? 'main.exe' : 'main';
    const pythonExe = path.join(backendDir, 'dist', exeName);
    pythonProcess = spawn(pythonExe, [], {
      cwd: backendDir,
      stdio: 'inherit',
    });
  }

  pythonProcess.on('error', (error) => {
    console.error('Python后端启动失败:', error);
  });

  pythonProcess.on('exit', (code) => {
    console.log(`Python后端进程退出，代码: ${code}`);
  });

  // 初始化Python桥接
  pythonBridge = new PythonBridge();
}

app.whenReady().then(() => {
  createWindow();
  startPythonBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // 关闭Python后端
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // 确保Python进程被终止
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
  }
});

// IPC处理
ipcMain.handle('python-bridge:check-health', async () => {
  if (pythonBridge) {
    return await pythonBridge.checkHealth();
  }
  return { status: 'not_initialized' };
});
