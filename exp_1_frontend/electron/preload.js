const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // Python后端健康检查
  checkPythonHealth: () => ipcRenderer.invoke('python-bridge:check-health'),
  
  // 可以添加更多IPC通信接口
});
