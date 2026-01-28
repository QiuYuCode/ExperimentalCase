# -- coding: utf-8 --

import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 确保backend目录的父目录在Python路径中（这样backend可以作为包导入）
backend_dir = Path(__file__).resolve().parent
parent_dir = backend_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    # 尝试相对导入（当作为包的一部分运行时，如 uvicorn backend.main:app）
    from .api import camera, detection, config
    from .config import ConfigManager
    from .detection import ColorDetector
except ImportError:
    # 如果相对导入失败，使用绝对导入（直接运行时）
    from backend.api import camera, detection, config
    from backend.config import ConfigManager
    from backend.detection import ColorDetector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="工业视觉检测系统 API", version="1.0.0")

# 配置CORS（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    # 注意：allow_origins=["*"] 时不能同时 allow_credentials=True（浏览器会拒绝）
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(camera.router)
app.include_router(detection.router)
app.include_router(config.router)


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    # 确定配置文件路径
    candidates = []
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        candidates.extend([
            exe_dir / "config.yaml",
            exe_dir / "shared" / "config.yaml",
        ])
    else:
        # 开发模式：exp_1_frontend/shared/config.yaml
        candidates.extend([
            backend_dir.parent / "shared" / "config.yaml",
            # 兼容旧路径（若有人把shared放在仓库根）
            backend_dir.parent.parent / "shared" / "config.yaml",
        ])

    config_path = next((p for p in candidates if p.exists()), candidates[0])
    
    # 如果配置文件不存在，尝试从exp_1目录复制
    if not config_path.exists():
        exp1_config = backend_dir.parent.parent / "exp_1" / "config.yaml"
        if exp1_config.exists():
            import shutil
            config_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(exp1_config, config_path)
            logger.info(f"从exp_1复制配置文件到: {config_path}")
        else:
            logger.warning(f"配置文件不存在: {config_path}，将使用默认配置")
            # 创建默认配置
            config_path.parent.mkdir(parents=True, exist_ok=True)
            import yaml
            default_config = {
                'system': {
                    'save_root': './saved_images',
                    'pixels_per_mm': 12.1
                },
                'colors': {}
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True)
    
    # 初始化配置管理器
    try:
        config_manager = ConfigManager(config_path)
        config.set_config_manager(config_manager)
        logger.info("配置管理器初始化成功")
    except Exception as e:
        logger.error(f"配置管理器初始化失败: {e}")
        config_manager = None
    
    # 初始化检测器
    if config_manager:
        try:
            detector = ColorDetector(config_manager.config, save_root=base_dir / "saved_images")
            detection.set_detector(detector)
            logger.info("检测器初始化成功")
        except Exception as e:
            logger.error(f"检测器初始化失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    # 断开相机连接
    try:
        from .api.camera import _current_camera
    except ImportError:
        from backend.api.camera import _current_camera
    if _current_camera is not None:
        try:
            _current_camera.disconnect()
        except:
            pass
    logger.info("应用关闭，资源已清理")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "工业视觉检测系统 API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


def main():
    """主函数"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
