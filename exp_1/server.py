import sys
import time
from pathlib import Path
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# --- 1. 路径设置 (保持不变) ---
current_file_path = Path(__file__).resolve()
root_path = current_file_path.parent.parent
exp_dir = current_file_path.parent
sys.path.append(str(root_path))
SAVE_ROOT_DIR = exp_dir / "saved_images"

from common import Camera

# --- 2. 初始化 FastAPI 应用 ---
app = FastAPI()

# 全局变量，用于保持相机连接
global_camera = None

# 定义返回给 C# 的数据格式
class DetectionResult(BaseModel):
    success: bool          # 接口调用是否成功
    message: str           # 提示信息
    object_detected: bool  # 是否识别到物体
    center_x: int = 0      # 物体中心 X
    center_y: int = 0      # 物体中心 Y
    saved_path: str = ""   # 图片保存路径

# --- 3. 辅助函数 (复用之前的逻辑) ---
def fix_iccp_warning(image):
    if image is None: return None
    _, encoded_img = cv2.imencode('.jpg', image)
    return cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

def process_image(image, color_mode="yellow"):
    """
    通用图像处理逻辑
    color_mode: "yellow" 或 "red"
    """
    if image is None: return False, 0, 0, None

    image_draw = image.copy()
    hsv_img = cv2.cvtColor(image_draw, cv2.COLOR_BGR2HSV)

    # 根据 C# 传来的参数决定识别什么颜色
    if color_mode == "yellow":
        lower = np.array([69, 39, 154]) # 你的参数
        upper = np.array([90, 255, 255])
        color_bgr = (0, 255, 255) # 画框用黄色
    elif color_mode == "red":
        # 红色有两个区间，这里简化写一个示例
        lower = np.array([0, 43, 46])
        upper = np.array([10, 255, 255])
        color_bgr = (0, 0, 255)   # 画框用红色
    else:
        return False, 0, 0, image_draw

    mask = cv2.inRange(hsv_img, lower, upper)
    # 形态学操作...
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected = False
    cx, cy = 0, 0
    max_area = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 1500: # 过滤噪点
            # 找最大的那个物体
            if area > max_area:
                max_area = area
                detected = True
                x, y, w, h = cv2.boundingRect(cnt)
                cx, cy = x + w//2, y + h//2
                # 画框
                cv2.rectangle(image_draw, (x, y), (x + w, y + h), color_bgr, 3)

    return detected, cx, cy, image_draw

# --- 4. API 接口定义 ---

@app.on_event("startup")
def startup_event():
    """服务启动时自动连接相机"""
    global global_camera
    print("正在初始化相机连接...")
    try:
        global_camera = Camera.Camera()
        # 这里可能需要根据你的 Camera 类稍作修改，如果它在构造函数里没有connect，需要手动connect
        # 假设你的 Camera 类在构造时就让用户输入或者自动连接了第0个
        # 为了自动化，最好修改 Camera 类使其能自动连接 index 0，而不是 input()
        pass 
    except Exception as e:
        print(f"相机初始化失败: {e}")

@app.on_event("shutdown")
def shutdown_event():
    """服务停止时关闭相机"""
    global global_camera
    if hasattr(global_camera, 'CloseCamera'):
        global_camera.CloseCamera()
    print("相机已断开。")

@app.post("/detect/{color}", response_model=DetectionResult)
async def detect_object(color: str):
    """
    C# 调用的主接口
    例如: POST http://localhost:8000/detect/yellow
    """
    global global_camera
    if global_camera is None:
        return DetectionResult(success=False, message="相机未连接", object_detected=False)

    try:
        # 1. 取图
        raw_image = global_camera.getCameraData()
        if raw_image is None:
            return DetectionResult(success=False, message="取图失败", object_detected=False)
        
        image = fix_iccp_warning(raw_image)

        # 2. 识别
        detected, cx, cy, result_img = process_image(image, color)

        save_path_str = ""
        # 3. 如果识别到了，保存图片
        if detected:
            save_dir = SAVE_ROOT_DIR / color
            save_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{color}_{timestamp}.jpg"
            save_path = save_dir / filename
            cv2.imwrite(str(save_path), result_img)
            save_path_str = str(save_path)
            msg = f"成功识别到 {color} 物体"
        else:
            msg = "未识别到物体"

        # 4. 返回 JSON 结果给 C#
        return DetectionResult(
            success=True,
            message=msg,
            object_detected=detected,
            center_x=cx,
            center_y=cy,
            saved_path=save_path_str
        )

    except Exception as e:
        return DetectionResult(success=False, message=str(e), object_detected=False)

if __name__ == "__main__":
    # 启动服务器，监听 8000 端口
    # 在 C# 端访问 http://127.0.0.1:8000/detect/yellow
    uvicorn.run(app, host="127.0.0.1", port=8000)