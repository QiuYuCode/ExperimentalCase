# -- coding: utf-8 --
"""
独立的运行脚本，用于直接运行FastAPI应用
"""
import sys
import os
from pathlib import Path

# 添加backend目录的父目录到Python路径（这样camera可以作为包导入）
backend_dir = Path(__file__).resolve().parent
parent_dir = backend_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# 设置工作目录为backend
os.chdir(backend_dir)

# 现在可以导入main模块（使用绝对导入）
from backend.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
