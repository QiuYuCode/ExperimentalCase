# ExperimentalCase - 海康相机案例库

基于海康威视工业相机的图像采集、处理和分析的实验项目。本项目包含相机驱动集成、颜色识别、实时视频处理等功能。

## 📋 项目概述

本项目演示了如何使用海康威视 GigE/USB 工业相机进行：
- **实时图像采集**：通过 MvImport SDK 与海康相机通信
- **颜色目标检测**：基于 HSV 颜色空间的多色物体识别（黄色、红色等）
- **图像处理**：使用 OpenCV 进行色彩转换、阈值分割、轮廓检测
- **结果保存**：自动将检测结果保存到指定文件夹

## 📁 项目结构

```
ExperimentalCase/
├── README.md                 # 项目说明文档
├── pyproject.toml           # Python 项目配置文件
├── common/                  # 公共模块
│   ├── Camera.py           # 海康相机驱动封装
│   ├── __init__.py
│   ├── MvImport/           # 海康 SDK Python 接口
│   │   ├── MvCameraControl_class.py
│   │   ├── CameraParams_const.py
│   │   ├── CameraParams_header.py
│   │   ├── MvErrorDefine_const.py
│   │   ├── PixelType_header.py
│   │   └── __pycache__/
│   └── dll/                # 海康 SDK DLL 文件及依赖
│       ├── MvDSS.ax
│       ├── MvDSS2.ax
│       ├── MvProducerGEV.cti
│       ├── MvProducerU3V.cti
│       └── Microsoft.VC90.*.manifest
├── exp_1/                  # 实验 1：颜色检测实验
│   ├── main.py            # 主程序（命令行版本）
│   ├── main_gui.py        # GUI 程序（图形界面版本）
│   ├── config.yaml        # 颜色识别参数配置
│   ├── __pycache__/
│   └── saved_images/      # 保存的检测结果
│       ├── red_results/
│       └── yellow_results/
```

## 🚀 快速开始

### 1. 环境要求

- Python >= 3.8
- Windows 系统（海康 SDK 依赖）
- 海康威视 GigE 或 USB 工业相机

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或直接安装所需包：

```bash
pip install numpy>=2.0.2 opencv-python>=4.11.0.86 pillow>=11.3.0 pyyaml>=6.0.3
```

### 3. 配置相机参数

编辑 `exp_1/config.yaml`，设置颜色识别参数：

```yaml
system:
  current_task: yellow          # 当前任务：yellow 或 red
  save_root: ./saved_images     # 结果保存路径
  show_window: false            # 是否显示窗口

colors:
  yellow:
    lower: [51, 49, 53]        # HSV 下限
    upper: [107, 128, 233]     # HSV 上限
    save_folder: yellow_results
    draw_color: [0, 0, 255]    # BGR 绘制颜色
```

### 4. 运行程序

**命令行版本（推荐）：**
```bash
cd exp_1
python main.py
```

**图形界面版本：**
```bash
cd exp_1
python main_gui.py
```

## 🔧 功能说明

### Camera 类（`common/Camera.py`）

海康相机的核心驱动封装：

```python
from common import Camera

# 初始化相机（自动连接和开始取流）
camera = Camera()

# 获取一帧图像
frame = camera.get_frame()

# 关闭相机
camera.close()
```

**主要方法：**
- `get_frame(timeout=1000)` - 获取实时图像帧
- `close()` - 关闭相机连接
- `get_exposure()` / `set_exposure(value)` - 曝光度控制
- `get_gain()` / `set_gain(value)` - 增益控制

### 配置管理（`ConfigManager`）

- 支持 YAML 配置文件加载
- 自动 NumPy 数组转换
- 支持多颜色/多区间检测

### 图像处理流程

1. **读取相机帧** → HSV 色彩空间转换
2. **颜色分割** → 基于 HSV 范围的阈值处理
3. **形态学处理** → 腐蚀/膨胀降噪
4. **轮廓检测** → 提取目标物体轮廓
5. **结果保存** → 标注图像并保存

## 📊 支持的颜色检测

项目配置中内置了以下颜色检测：

| 颜色 | HSV 下限 | HSV 上限 | 用途 |
|------|---------|---------|------|
| 黄色 | [51, 49, 53] | [107, 128, 233] | 黄色物体识别 |
| 红色 | 两个区间 | 两个区间 | 红色物体识别（跨越HSV边界） |

可根据实际需求调整参数。

## 📝 使用示例

### 基本的颜色检测流程

```python
import cv2
from pathlib import Path
import yaml
from common import Camera

# 初始化相机
camera = Camera()

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 获取一帧
frame = camera.get_frame()

# HSV 转换
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# 颜色分割
lower = tuple(config['colors']['yellow']['lower'])
upper = tuple(config['colors']['yellow']['upper'])
mask = cv2.inRange(hsv, lower, upper)

# 查找轮廓
contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# 绘制结果
cv2.drawContours(frame, contours, -1, (0, 0, 255), 2)
cv2.imshow('Result', frame)

camera.close()
```

## 🛠️ 常见问题

### Q: 如何调试颜色参数？

A: 使用 HSV 滑块手动调整（示例）：
```python
def nothing(x):
    pass

cv2.namedWindow('HSV Trackbar')
cv2.createTrackbar('H_lower', 'HSV Trackbar', 0, 180, nothing)
cv2.createTrackbar('S_lower', 'HSV Trackbar', 0, 255, nothing)
# ... 读取滑块值并实时显示效果
```

### Q: 相机连接失败怎么办？

A: 检查以下项目：
1. 相机是否连接到电脑
2. 网络配置是否正确（GigE 相机）
3. 驱动程序是否正确安装
4. `MvImport` 文件夹是否完整

## 📦 依赖说明

| 库 | 版本 | 用途 |
|----|------|------|
| numpy | >=2.0.2 | 数值计算 |
| opencv-python | >=4.11.0.86 | 图像处理 |
| pillow | >=11.3.0 | 图像 I/O |
| pyyaml | >=6.0.3 | 配置文件解析 |

海康 SDK：由 `MvImport` 文件夹提供

## 📄 许可证

本项目仅供学习和研究使用。

## 👨‍💻 开发信息

- **项目名称**：ExperimentalCase
- **版本**：0.1.0
- **Python 版本**：3.8+
- **操作系统**：Windows

## 📞 技术支持

如有问题或建议，请检查：
1. 相机硬件连接和驱动
2. Python 环境和依赖库版本
3. 配置文件参数设置
4. 控制台输出信息和错误日志
