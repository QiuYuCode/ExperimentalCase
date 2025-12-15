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
- [uv](https://github.com/astral-sh/uv)（推荐，用于快速依赖管理）

### 2. 安装依赖

**方式一：使用 uv（推荐）**

本项目使用 `uv` 进行依赖管理，提供更快的安装速度和更好的依赖解析。

```bash
# 安装 uv（如果尚未安装）
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# 或使用 pip
pip install uv

# 同步项目依赖（根据 pyproject.toml 和 uv.lock）
uv sync

# 或仅安装生产依赖（不包含开发依赖）
uv sync --no-dev
```

**方式二：使用传统 pip**

```bash
# 从 requirements.txt 安装（推荐，自动锁定版本）
pip install -r requirements.txt

# 或根据 pyproject.toml 直接安装所需包
pip install "numpy==1.24" "opencv-python>=4.8.1.78" "pillow>=10.4.0" "pyyaml>=6.0.3"
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

**方式一：使用 uv 运行（推荐）**
```bash
# 命令行版本
cd exp_1
uv run python main.py

# 图形界面版本
cd exp_1
uv run python main_gui.py
```

**方式二：直接使用 Python 运行（传统方式）**
```bash
# 命令行版本
cd exp_1
python main.py

# 图形界面版本
cd exp_1
python main_gui.py
```

> **注意**：使用传统方式运行前，请确保已通过 `pip install -r requirements.txt` 或 `uv sync` 安装所有依赖。

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

| 颜色 | HSV 范围 | 绘制颜色 | 保存文件夹 | 说明 |
|------|---------|--------|----------|------|
| 黄色 | L:[51,49,53]<br/>U:[107,128,233] | [0,0,255] 红色 | yellow_results | 单区间检测 |
| 红色 | L1:[0,43,46] U1:[10,255,255]<br/>L2:[119,63,79] U2:[169,158,255] | [0,255,0] 绿色 | red_results | 双区间检测（跨越HSV边界） |

**参数说明：**
- **HSV 范围**：[H, S, V]，H 范围 0-180，S 和 V 范围 0-255（OpenCV标准）
- **绘制颜色**：BGR 格式 [B, G, R]，用于在结果图上标注检测目标
- **双区间**：红色在 HSV 空间中跨越 H=180 的边界，因此需要两个区间分别检测

可根据实际光照和物体条件调整参数。

## 🔧 二次开发：添加其他颜色识别

本项目支持通过配置文件动态添加新颜色识别，**无需修改代码**。代码会自动读取配置文件中的所有颜色定义，并在 GUI 中自动生成对应的检测按钮。

### 添加新颜色的步骤

#### 方式一：使用 GUI 界面添加（推荐，最简单）

1. 运行 GUI 程序：`python main_gui.py`
2. 切换到"⚙️ 参数调试"页面
3. 调整 HSV 参数找到合适的颜色范围
4. 点击"➕ 添加新颜色"按钮
5. 在对话框中输入颜色信息并保存

详细步骤请参考[如何确定 HSV 参数值 - 方法一](#如何确定-hsv-参数值)。

#### 方式二：手动编辑配置文件

打开 `exp_1/config.yaml`，在 `colors` 部分添加新颜色配置。

#### 选择配置格式

根据颜色在 HSV 空间中的分布，选择单区间或双区间配置：

**方式一：单区间颜色（推荐，适用于大多数颜色）**

适用于 HSV 色相值（H）在一个连续范围内的颜色，如绿色、蓝色、紫色等：

```yaml
colors:
  # ... 现有的 yellow 和 red 配置 ...
  
  green:  # 新颜色名称（可自定义）
    lower: [35, 50, 50]        # HSV 下限 [H, S, V]
    upper: [85, 255, 255]      # HSV 上限
    save_folder: green_results # 结果保存文件夹名
    draw_color: [0, 0, 255]   # BGR 格式的标注颜色（绿色用红色标注）
  
  blue:
    lower: [100, 50, 50]
    upper: [130, 255, 255]
    save_folder: blue_results
    draw_color: [255, 0, 0]   # 蓝色用红色标注
```

**方式二：双区间颜色（适用于跨越 HSV 边界的颜色）**

适用于色相值跨越 H=180 边界的颜色，如红色、橙色等：

```yaml
colors:
  # ... 现有的配置 ...
  
  orange:  # 橙色示例
    lower1: [0, 50, 50]        # 第一个区间下限
    upper1: [25, 255, 255]     # 第一个区间上限
    lower2: [155, 50, 50]      # 第二个区间下限（接近 180）
    upper2: [180, 255, 255]    # 第二个区间上限
    save_folder: orange_results
    draw_color: [0, 165, 255]  # BGR 格式（橙色用蓝色标注）
```

### 配置参数说明

| 参数 | 类型 | 说明 | 必需 |
|------|------|------|------|
| `lower` / `upper` | 数组 `[H, S, V]` | 单区间模式的 HSV 范围 | 单区间模式必需 |
| `lower1` / `upper1` | 数组 `[H, S, V]` | 双区间模式的第一区间 | 双区间模式必需 |
| `lower2` / `upper2` | 数组 `[H, S, V]` | 双区间模式的第二区间 | 双区间模式必需 |
| `save_folder` | 字符串 | 检测结果保存的文件夹名 | 必需 |
| `draw_color` | 数组 `[B, G, R]` | BGR 格式的标注颜色 | 可选（默认绿色） |

**HSV 范围说明：**
- **H (色相)**：0-180（OpenCV 标准，是标准 HSV 0-360 的一半）
- **S (饱和度)**：0-255
- **V (亮度)**：0-255

**BGR 格式说明：**
- `[0, 0, 255]` = 红色
- `[0, 255, 0]` = 绿色
- `[255, 0, 0]` = 蓝色
- `[0, 165, 255]` = 橙色
- `[255, 255, 0]` = 青色

### 如何确定 HSV 参数值

#### 方法一：使用 GUI 参数调试页面（推荐）

**方式 A：直接添加新颜色（最简单）**

1. 运行 GUI 程序：`python main_gui.py`
2. 切换到"⚙️ 参数调试"页面
3. 点击"📸 重新抓拍图像"获取当前画面
4. 调整 HSV 滑块，实时查看效果：
   - **H Min/Max**：调整颜色范围
   - **S Min**：调高可过滤白色/灰色背景
   - **V Min**：调高可过滤黑色背景/阴影
5. 找到合适的参数后，点击"➕ 添加新颜色"按钮
6. 在对话框中输入：
   - **颜色名称**：如 `green`、`blue` 等
   - **保存文件夹名**：如 `green_results`
   - **标注颜色**：BGR 格式，默认绿色 `[0, 255, 0]`
7. 点击"确定"保存，新颜色会自动添加到配置文件
8. 切换到"🔍 智能识别"页面，即可看到新的检测按钮

**方式 B：保存到现有颜色**

1. 运行 GUI 程序：`python main_gui.py`
2. 切换到"⚙️ 参数调试"页面
3. 点击"📸 重新抓拍图像"获取当前画面
4. 调整 HSV 滑块，实时查看效果
5. 在"保存至配置文件"下拉框中选择要更新的颜色
6. 点击"💾 保存参数"更新现有颜色的 HSV 参数

#### 方法二：参考常见颜色的 HSV 范围

| 颜色 | H 范围 | S 范围 | V 范围 | 说明 |
|------|--------|--------|--------|------|
| 红色 | 0-10, 170-180 | 43-255 | 46-255 | 双区间 |
| 橙色 | 5-25 | 50-255 | 50-255 | 单区间 |
| 黄色 | 20-30 | 50-255 | 50-255 | 单区间 |
| 绿色 | 35-85 | 50-255 | 50-255 | 单区间 |
| 青色 | 85-100 | 50-255 | 50-255 | 单区间 |
| 蓝色 | 100-130 | 50-255 | 50-255 | 单区间 |
| 紫色 | 130-160 | 50-255 | 50-255 | 单区间 |

> **注意**：实际参数需要根据光照条件、物体材质和相机设置进行调整。

### 完整示例：添加绿色检测

在 `config.yaml` 中添加：

```yaml
system:
  current_task: 
  save_root: ./saved_images
  show_window: false
  pixels_per_mm: 12.1

colors:
  yellow:
    # ... 现有配置 ...
  red:
    # ... 现有配置 ...
  
  green:  # 新增绿色检测
    lower: [35, 50, 50]
    upper: [85, 255, 255]
    save_folder: green_results
    draw_color: [0, 0, 255]  # 用红色标注绿色目标
```

添加后：
- **命令行版本**：自动识别模式会自动检测绿色，或使用 `mode='green'` 指定检测绿色
- **GUI 版本**：会自动出现"检测 GREEN"按钮，点击即可检测绿色目标
- **结果保存**：检测结果会保存到 `saved_images/green_results/` 文件夹

### 代码实现说明

代码已实现动态读取配置，无需修改：

- **`run_detection_once` 函数**：自动遍历 `cfg['colors']` 中的所有颜色配置
- **`detect_single_color` 函数**：自动判断单区间或双区间模式
- **GUI 界面**：自动读取配置并生成对应的检测按钮

因此，**只需修改配置文件即可添加新颜色识别功能**。

### GUI 界面添加新颜色功能

GUI 参数调试页面提供了便捷的"➕ 添加新颜色"功能，无需手动编辑配置文件：

1. **实时预览**：调整 HSV 滑块时实时查看检测效果
2. **一键添加**：找到合适参数后，点击"➕ 添加新颜色"即可
3. **自动保存**：自动保存到配置文件并刷新界面
4. **即时生效**：添加后立即在"智能识别"页面看到新按钮

**使用流程：**
- 调整 HSV 参数 → 点击"➕ 添加新颜色" → 输入颜色信息 → 确定保存
- 新颜色会自动出现在"智能识别"页面的检测按钮列表中

### 调试技巧

1. **从宽范围开始**：先用较大的 HSV 范围，确保能检测到目标
2. **逐步缩小范围**：逐步缩小范围，减少误检
3. **调整 S 和 V**：如果背景干扰大，适当提高 S Min 和 V Min
4. **使用实时预览**：GUI 的参数调试页面提供实时预览，方便调整
5. **保存多个版本**：可以保存多个参数版本，方便对比效果

## 📝 使用示例

### 基本的颜色检测流程

**示例 1：单区间检测（黄色）**
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

# 颜色分割（黄色）
yellow_cfg = config['colors']['yellow']
lower = tuple(yellow_cfg['lower'])
upper = tuple(yellow_cfg['upper'])
mask = cv2.inRange(hsv, lower, upper)

# 查找轮廓
contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# 绘制结果
draw_color = tuple(yellow_cfg['draw_color'])
cv2.drawContours(frame, contours, -1, draw_color, 2)
cv2.imshow('Yellow Detection', frame)

camera.close()
```

**示例 2：双区间检测（红色）**
```python
# 颜色分割（红色 - 需要两个区间）
red_cfg = config['colors']['red']
lower1 = tuple(red_cfg['lower1'])
upper1 = tuple(red_cfg['upper1'])
lower2 = tuple(red_cfg['lower2'])
upper2 = tuple(red_cfg['upper2'])

# 两个范围的掩码进行 OR 操作
mask1 = cv2.inRange(hsv, lower1, upper1)
mask2 = cv2.inRange(hsv, lower2, upper2)
mask = cv2.bitwise_or(mask1, mask2)

# 后续处理同上
contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
draw_color = tuple(red_cfg['draw_color'])
cv2.drawContours(frame, contours, -1, draw_color, 2)
cv2.imshow('Red Detection', frame)
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

### 生产依赖

| 库 | 版本要求 | 当前锁定版本 | 用途 |
|----|---------|------------|------|
| numpy | ==1.24 | 1.24.0 | 数值计算 |
| opencv-python | >=4.8.1.78 | 4.8.1.78 | 图像处理 |
| pillow | >=10.4.0 | 11.3.0 | 图像 I/O |
| pyyaml | >=6.0.3 | 6.0.3 | 配置文件解析 |

### 开发依赖

| 库 | 版本要求 | 用途 |
|----|---------|------|
| nuitka | >=2.8.9 | Python 代码编译打包 |

### 其他依赖

- **海康 SDK**：由 `common/MvImport/` 文件夹提供，包含相机控制相关的 Python 接口
- **DLL 文件**：由 `common/dll/` 文件夹提供，包含海康 SDK 所需的动态链接库

> **注意**：版本信息基于 `pyproject.toml` 和 `uv.lock`。实际安装的版本可能因依赖解析而略有不同，但会满足版本要求。

## 📦 Nuitka 打包说明

使用 Nuitka 将 Python 程序编译为独立的可执行文件，方便在没有 Python 环境的机器上运行。

### 前置要求

1. **安装 Nuitka**（已包含在开发依赖中）：
```bash
# 使用 uv 安装
uv sync

# 或使用 pip 安装
pip install nuitka>=2.8.9
```

2. **安装 C 编译器**：
   - **Windows**：安装 Visual Studio Build Tools 或 MinGW64（Nuitka 首次运行时会提示下载）
   - **Linux**：`sudo apt-get install gcc`（Ubuntu/Debian）

### 打包命令

**打包命令行版本（main.py）：**
```bash
cd exp_1
python -m nuitka \
    --mode=standalone \
    --output-dir=build \
    --enable-plugin=opencv-python \
    --include-module=common \
    --include-module=common.Camera \
    --include-module=common.MvImport \
    --include-data-dir=../common/dll=common/dll \
    --include-data-file=config.yaml=config.yaml \
    --windows-icon-from-ico=VisionSystem.ico \
    --product-name="ExperimentalCase" \
    --file-version=0.1.0.0 \
    --product-version=0.1.0 \
    --file-description="海康相机颜色检测工具" \
    main.py
```

**打包 GUI 版本（main_gui.py）：**
```bash
cd exp_1
python -m nuitka \
    --mode=standalone \
    --output-dir=build \
    --enable-plugin=opencv-python \
    --enable-plugin=tk-inter \
    --include-module=common \
    --include-module=common.Camera \
    --include-module=common.MvImport \
    --include-data-dir=../common/dll=common/dll \
    --include-data-file=config.yaml=config.yaml \
    --windows-icon-from-ico=VisionSystem.ico \
    --product-name="ExperimentalCase GUI" \
    --file-version=0.1.0.0 \
    --product-version=0.1.0 \
    --file-description="海康相机颜色检测工具（图形界面）" \
    main_gui.py
```

### 打包参数说明

| 参数 | 说明 |
|------|------|
| `--mode=standalone` | 打包为独立文件夹，包含所有依赖 |
| `--output-dir=build` | 输出目录 |
| `--enable-plugin=opencv-python` | 启用 OpenCV 插件 |
| `--enable-plugin=tk-inter` | 启用 Tkinter 插件（GUI 版本需要） |
| `--include-module=common` | 包含 common 模块 |
| `--include-data-dir=../common/dll=common/dll` | 包含 DLL 文件目录 |
| `--include-data-file=config.yaml=config.yaml` | 包含配置文件 |
| `--windows-icon-from-ico=VisionSystem.ico` | 设置 Windows 图标 |
| `--product-name` | 产品名称（显示在文件属性中） |
| `--file-version` | 文件版本号 |
| `--product-version` | 产品版本号 |
| `--file-description` | 文件描述 |

### 打包输出

打包后会生成 `build/main.dist/` 或 `build/main_gui.dist/` 文件夹，包含：
- `main.exe` 或 `main_gui.exe`（可执行文件）
- Python DLL 和所有依赖模块
- `common/dll/` 目录（DLL 文件）
- `config.yaml` 配置文件

### 分发说明

1. 将整个 `.dist` 文件夹复制到目标机器即可运行
2. 确保 `config.yaml` 与可执行文件在同一目录
3. DLL 文件已自动包含在 `.dist` 文件夹中

### 注意事项

- 打包前请确保程序在开发环境中能正常运行
- 首次打包可能需要较长时间（需要下载依赖和编译）
- 如果遇到模块缺失错误，使用 `--include-module=<模块名>` 手动包含
- 将整个 `.dist` 文件夹复制到目标机器即可运行，无需安装 Python 环境

## 🔨 uv 使用说明

本项目使用 `uv` 作为包管理工具，提供更快的依赖安装和更好的版本锁定。

### 常用命令

```bash
# 同步依赖（安装/更新所有依赖）
uv sync

# 添加新依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>

# 移除依赖
uv remove <package-name>

# 更新依赖
uv sync --upgrade

# 运行 Python 脚本（自动使用项目环境）
uv run python <script.py>

# 生成 requirements.txt（用于兼容 pip）
uv pip compile pyproject.toml -o requirements.txt

# 查看已安装的包
uv pip list
```

### 项目文件说明

- `pyproject.toml` - 项目配置和依赖声明
- `uv.lock` - 锁定的依赖版本（确保可重现的构建）
- `requirements.txt` - 由 uv 自动生成，用于兼容传统 pip 工作流

### 优势

- **速度更快**：比 pip 快 10-100 倍
- **依赖解析更可靠**：使用与 Cargo 相同的解析器
- **版本锁定**：`uv.lock` 确保所有环境使用相同版本
- **虚拟环境管理**：自动创建和管理虚拟环境

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
