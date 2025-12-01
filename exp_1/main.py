import sys
import cv2
import numpy as np
import time
from pathlib import Path

# --- 1. 路径设置 ---
current_file_path = Path(__file__).resolve()
# 根目录 D:\ExperimentalCase
root_path = current_file_path.parent.parent
# 当前实验目录 D:\ExperimentalCase\exp_1
exp_dir = current_file_path.parent

sys.path.append(str(root_path))

try:
    from common import Camera
except ImportError:
    print("【错误】找不到 common 模块，请检查路径设置。")
    sys.exit()

# --- 2. 核心处理逻辑 ---

def fix_iccp_warning(image):
    """消除 libpng warning"""
    if image is None: return None
    _, encoded_img = cv2.imencode('.jpg', image)
    return cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

def detect_color(image, mode="yellow"):
    """
    检测指定颜色的物体并画框
    mode: "yellow" 或 "red"
    """
    image_draw = image.copy()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    mask = None

    # --- 颜色阈值配置 ---
    if mode == "yellow":
        # 使用您之前测定的偏绿黄色的值
        lower = np.array([69, 39, 154])
        upper = np.array([90, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        color_bgr = (0, 255, 255) # 黄色框
        label = "Yellow"

    elif mode == "red":
        # 红色比较特殊，跨越了 0/180，需要两个区间合并
        # 区间1: 0-10
        lower1 = np.array([0, 43, 46])
        upper1 = np.array([10, 255, 255])
        # 区间2: 156-180
        lower2 = np.array([156, 43, 46])
        upper2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        color_bgr = (0, 0, 255)   # 红色框
        label = "Red"
    
    else:
        return image_draw

    # --- 形态学处理 (去噪) ---
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # --- 轮廓查找 ---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 2000: # 面积阈值，太小的忽略
            x, y, w, h = cv2.boundingRect(cnt)
            # 画框
            cv2.rectangle(image_draw, (x, y), (x + w, y + h), color_bgr, 3)
            # 写字
            cv2.putText(image_draw, f"{label} Detected", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_bgr, 2)

    return image_draw

# --- 3. 主程序循环 ---

def main():
    print("=== 海康相机本地调试工具 ===")
    
    # 1. 实例化相机 (新版 Camera 类会自动连接，不需要 input 了)
    try:
        hkki_camera = Camera.Camera()
    except Exception as e:
        print(f"相机初始化失败: {e}")
        return

    # 等待相机稍微稳定一下
    time.sleep(1)

    print("\n【操作说明】")
    print("  按 'y' -> 切换到 黄色识别模式")
    print("  按 'r' -> 切换到 红色识别模式")
    print("  按 'n' -> 不识别，仅显示原图")
    print("  按 'q' -> 退出程序")
    
    current_mode = "yellow" # 默认模式
    
    cv2.namedWindow("Debug Window", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Debug Window", 1024, 768)

    try:
        while True:
            # 2. 获取图像 (现在是非阻塞的，非常快)
            raw_image = hkki_camera.getCameraData()
            
            if raw_image is None:
                print("等待图像中...")
                time.sleep(0.1)
                continue

            # 消除警告
            image = fix_iccp_warning(raw_image)

            # 3. 根据当前模式处理图像
            if current_mode == "none":
                display_img = image
                cv2.putText(display_img, "Raw Mode", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                display_img = detect_color(image, mode=current_mode)
                # 在左上角显示当前模式
                cv2.putText(display_img, f"Mode: {current_mode.upper()}", (30, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 4. 显示
            cv2.imshow("Debug Window", display_img)

            # 5. 按键响应
            key = cv2.waitKey(20) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('y'):
                current_mode = "yellow"
                print("切换到: 黄色识别")
            elif key == ord('r'):
                current_mode = "red"
                print("切换到: 红色识别")
            elif key == ord('n'):
                current_mode = "none"
                print("切换到: 原图模式")

    except KeyboardInterrupt:
        print("用户强制停止")
    finally:
        # 6. 清理资源
        print("正在关闭相机...")
        if hasattr(hkki_camera, 'CloseCamera'):
            hkki_camera.CloseCamera()
        cv2.destroyAllWindows()
        print("程序已退出")

if __name__ == "__main__":
    main()