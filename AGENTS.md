# AGENTS.md - Development Guidelines for ExperimentalCase

This file contains development guidelines for agentic coding agents working on the ExperimentalCase project - a Hikvision camera-based computer vision system for color detection and image processing.

## Project Overview

This is a Python 3.8+ project that integrates Hikvision industrial cameras with OpenCV for real-time color detection. The project includes both CLI and GUI interfaces and uses `uv` for dependency management.

## Build, Test, and Development Commands

### Environment Setup
```bash
# Primary method - using uv (recommended)
uv sync                    # Install all dependencies
uv sync --no-dev          # Install only production dependencies

# Alternative - using pip
pip install -r requirements.txt

# Verify environment
uv run python --version   # Check Python version
```

### Running Applications
```bash
# CLI version
cd exp_1
uv run python main.py

# GUI version  
cd exp_1
uv run python main_gui.py

# Alternative (without uv)
cd exp_1
python main.py
python main_gui.py
```

### Development Commands
```bash
# Add new dependencies
uv add <package-name>          # Production dependency
uv add --dev <package-name>     # Development dependency

# Update dependencies
uv sync --upgrade

# Generate requirements.txt for pip compatibility
uv pip compile pyproject.toml -o requirements.txt

# List installed packages
uv pip list

# Run with specific Python version (if needed)
uv run --python 3.8 python main.py
```

### Testing Commands
```bash
# Run specific test file (when tests are available)
cd exp_1
uv run python -m pytest tests/test_camera.py -v

# Run all tests
uv run python -m pytest

# Run tests with coverage
uv run python -m pytest --cov=common --cov=exp_1

# Run single test function
uv run python -m pytest tests/test_camera.py::test_camera_connection -v
```

### Code Quality Commands
```bash
# Type checking (if mypy is added)
uv run python -m mypy common/ exp_1/

# Linting (if flake8 is added)  
uv run python -m flake8 common/ exp_1/ --max-line-length=100

# Format code (if black is added)
uv run python -m black common/ exp_1/ --line-length=100

# Import sorting (if isort is added)
uv run python -m isort common/ exp_1/ --profile black
```

### Packaging (Nuitka)
```bash
# Package CLI version
cd exp_1
python -m nuitka \
    --mode=standalone \
    --output-dir=build \
    --enable-plugin=opencv-python \
    --include-module=common \
    --include-data-dir=../common/dll=common/dll \
    --include-data-file=config.yaml=config.yaml \
    --windows-icon-from-ico=VisionSystem.ico \
    main.py

# Package GUI version
python -m nuitka \
    --mode=standalone \
    --output-dir=build \
    --enable-plugin=opencv-python \
    --enable-plugin=tk-inter \
    --include-module=common \
    --include-data-dir=../common/dll=common/dll \
    --include-data-file=config.yaml=config.yaml \
    --windows-icon-from-ico=VisionSystem.ico \
    main_gui.py
```

## Code Style Guidelines

### Python Version and Encoding
- **Python Version**: 3.8+ (required by project)
- **File Encoding**: UTF-8 with BOM (`# -- coding: utf-8 --` at file top)
- **Line Endings**: CRLF (Windows) or LF (Linux) - maintain consistency

### Import Organization
```python
# Standard library imports first
import sys
import os
import time
import logging
from pathlib import Path
from ctypes import *

# Third-party imports next
import numpy as np
import cv2 as cv
import yaml
from PIL import Image, ImageTk

# Local imports last (with relative imports when possible)
from common import Camera
from main import run_detection_once, fix_iccp_warning
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `Camera`, `ConfigManager`, `ModernApp`)
- **Functions/Methods**: `snake_case` (e.g., `get_frame()`, `load_config()`, `run_detection_once()`)
- **Variables**: `snake_case` (e.g., `camera_data`, `save_path_str`, `max_area`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `COLORS`, `DEFAULT_TIMEOUT`)
- **Private Members**: Prefix with `_` (e.g., `_connect_and_start()`, `_convert_image()`)

### Type Hints and Documentation
```python
def detect_single_color(
    image: np.ndarray, 
    hsv: np.ndarray, 
    color_name: str, 
    param: dict
) -> tuple[int, np.ndarray, str, dict]:
    """
    检测单一颜色，返回 (面积, 轮廓, 颜色名, 参数)
    
    Args:
        image: 原始BGR图像
        hsv: HSV色彩空间图像
        color_name: 颜色名称
        param: 颜色参数配置
        
    Returns:
        Tuple of (max_area, best_contour, detected_color, parameters)
    """
```

### Error Handling Patterns
```python
# 1. File operations with explicit error messages
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error(f"配置文件不存在: {config_path}")
    sys.exit(1)
except yaml.YAMLError as e:
    logger.error(f"配置文件解析错误: {e}")
    sys.exit(1)

# 2. Camera operations with graceful degradation
try:
    raw_image = camera.getCameraData()
    if raw_image is None:
        print("ERROR: 取图失败 (Empty Frame)")
        return None
except Exception as e:
    logger.error(f"相机取图异常: {e}")
    return None

# 3. Resource cleanup using try/finally
camera = None
try:
    camera = Camera()
    # ... camera operations ...
finally:
    if camera and hasattr(camera, 'CloseCamera'):
        camera.CloseCamera()
```

### Code Structure and Patterns
```python
# Class structure (Camera.py example)
class Camera:
    def __init__(self):
        """初始化时自动连接第一台相机并开始取流"""
        self.cam = MvCamera()
        self.nPayloadSize = 0
        self.buf_cache = None
        self.is_open = False
        self._connect_and_start()

    def _private_method(self):
        """私有方法用下划线前缀"""
        pass

    def public_method(self):
        """公共方法"""
        return self._private_method()

    def __del__(self):
        """析构函数确保资源释放"""
        self.CloseCamera()
```

### OpenCV and NumPy Patterns
```python
# Image processing pipeline
def process_image(image: np.ndarray) -> np.ndarray:
    """图像处理的标准流程"""
    # 1. 颜色空间转换
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 2. 颜色分割
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    
    # 3. 形态学操作
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 4. 轮廓检测
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    # 5. 结果绘制
    result = image.copy()
    cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
    
    return result

# NumPy array handling
def ensure_numpy(val) -> np.ndarray:
    """确保输入为numpy数组"""
    if isinstance(val, list):
        return np.array(val, dtype=np.uint8)
    return val
```

### Configuration Management
```python
# ConfigManager pattern
class ConfigManager:
    def __init__(self, config_path: Path):
        self.config = self.load_config(config_path)

    def load_config(self, path: Path) -> dict:
        """加载并预处理配置文件"""
        with open(path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        
        # 预处理numpy数组
        for color_name, params in cfg['colors'].items():
            if 'lower' in params:
                params['lower'] = np.array(params['lower'], dtype=np.uint8)
                params['upper'] = np.array(params['upper'], dtype=np.uint8)
                
        return cfg
```

### GUI Patterns (tkinter)
```python
# Modern GUI class structure
class ModernApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_variables()
        self.setup_layout()
        self.connect_events()

    def setup_window(self):
        """窗口初始化"""
        self.title("应用标题")
        self.geometry("1200x800")

    def setup_variables(self):
        """变量初始化"""
        self.camera = None
        self.config_data = {}

    def create_nav_btn(self, text: str, command):
        """创建导航按钮的辅助方法"""
        btn = ttk.Button(
            self.sidebar, 
            text=text, 
            command=command,
            style="Nav.TButton"
        )
        btn.pack(fill=tk.X, padx=10, pady=5)
        return btn
```

### Logging Configuration
```python
# 日志配置模式
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)  # 默认只显示CRITICAL级别

# 在需要详细调试时可以动态调整
def enable_debug_logging():
    """启用调试日志"""
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
```

### File I/O Patterns
```python
# 路径处理（使用pathlib）
def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).resolve().parent.parent

def get_save_path(cfg: dict, color_name: str) -> Path:
    """构建保存路径"""
    exp_dir = Path(__file__).resolve().parent
    save_root = exp_dir / cfg['system']['save_root']
    save_folder = cfg['colors'][color_name]['save_folder']
    return save_root / save_folder

# 图像保存
def save_result_image(image: np.ndarray, save_path: Path):
    """保存检测结果图像"""
    save_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(save_path), image)
```

## Project-Specific Guidelines

### Camera Integration
- Always check `camera.is_open` before using camera methods
- Use try/finally blocks to ensure camera cleanup
- Handle connection failures gracefully with user-friendly messages
- Support both GUI and CLI modes for the same functionality

### Color Detection
- Use HSV color space for detection (H: 0-180, S/V: 0-255 in OpenCV)
- Support both single-range and dual-range color detection (for colors like red)
- Always validate color parameters from config files
- Use morphological operations to reduce noise

### Configuration Files
- YAML format with UTF-8 encoding
- System settings under `system:` key
- Color definitions under `colors:` key
- Support both `lower`/`upper` (single range) and `lower1`/`upper1`, `lower2`/`upper2` (dual range)
- Always convert config lists to numpy arrays with proper dtype

### GUI Development
- Use tkinter with modern styling via ttk
- Implement threaded camera operations to prevent UI freezing
- Provide real-time preview for parameter tuning
- Use consistent color scheme (defined in COLORS dict)
- Support both docked and floating window layouts

### Platform Considerations
- Primary target: Windows (Hikvision SDK dependency)
- Use pathlib for cross-platform path handling
- Handle both development and packaged execution modes
- Include DLL files in packaging (common/dll/ directory)

## Dependency Management
- **Primary**: Use `uv` for dependency management
- **Production**: numpy==1.24, opencv-python>=4.8.1.78, pillow>=10.4.0, pyyaml>=6.0.3
- **Development**: nuitka>=2.8.9 (for packaging)
- **Version Locking**: Use uv.lock for reproducible builds
- **Fallback**: requirements.txt generated from pyproject.toml

## Performance Considerations
- Cache numpy arrays for image conversion (`buf_cache` in Camera class)
- Use efficient contour detection with CHAIN_APPROX_SIMPLE
- Implement proper memory management for camera buffers
- Use threading for non-blocking camera operations

## Testing Strategy
- Unit tests for image processing functions
- Integration tests for camera operations  
- GUI tests for user workflows
- Configuration validation tests
- Mock camera hardware for CI/CD

## Common Issues and Solutions
- **Camera Connection**: Check DLL files in common/dll/ directory
- **Import Errors**: Ensure MvImport/ directory is in Python path
- **Memory Leaks**: Always close camera connections in finally blocks
- **Config Loading**: Use UTF-8 encoding and proper error handling
- **Packaging**: Include all required DLL files and config files