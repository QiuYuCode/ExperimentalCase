# 工业视觉检测系统 - 前端应用

基于 Vue 3 + Electron + Python FastAPI 的现代化工业视觉检测系统。

## 技术栈

- **前端**: Vue 3 (Composition API) + Pinia
- **桌面框架**: Electron
- **后端**: Python FastAPI + OpenCV
- **构建工具**: Vite + Electron Builder

## 功能特性

- ✅ 支持多种相机类型（海康工业相机、USB摄像头、IP网络相机）
- ✅ 实时图像流显示（WebSocket）
- ✅ 颜色检测（单区间/双区间）
- ✅ HSV参数实时调试
- ✅ 尺寸标定功能
- ✅ 现代化UI设计

## 开发环境设置

### 前置要求

- Node.js 18+
- Python 3.8+
- uv (Python包管理器，可选)

### 安装依赖

```bash
# 安装Node.js依赖
npm install

# 安装Python后端依赖
cd backend
pip install -r requirements.txt
# 或使用uv
uv pip install -r requirements.txt
```

### 开发模式运行

```bash
# 启动Vite开发服务器和Electron
npm run electron:dev

# 或者分别启动：
# 终端1: 启动Vite
npm run dev

# 终端2: 启动Python后端
cd backend
python -m uvicorn main:app --reload

# 终端3: 启动Electron
electron .
```

## 项目结构

```
exp_1_frontend/
├── electron/          # Electron主进程
├── src/               # Vue前端源码
│   ├── components/    # 组件
│   ├── views/         # 页面视图
│   ├── stores/        # Pinia状态管理
│   └── api/           # API客户端
├── backend/           # Python后端
│   ├── camera/        # 相机抽象层
│   ├── detection/      # 检测模块
│   └── api/           # FastAPI路由
└── shared/            # 共享资源（配置文件等）
```

## 打包发布

```bash
# 构建前端
npm run build

# 打包Electron应用
npm run electron:build

# 仅打包（不创建安装程序）
npm run electron:pack
```

## 配置说明

配置文件位于 `shared/config.yaml`，格式与原始项目兼容。

## 许可证

MIT
