import sys
from pathlib import Path
import cv2
import numpy as np

# --- 关键修复：添加根目录到搜索路径 ---
# 获取当前文件的目录 (D:\ExperimentalCase\exp_1)
current_dir = Path(__file__).resolve().parent
# 获取根目录 (D:\ExperimentalCase)
root_path = current_dir.parent
# 将根目录加入 Python 搜索路径
sys.path.append(str(root_path))
# -----------------------------------

# 现在可以正常导入 common 了
from common import Camera

def pick_color(event, x, y, flags, param):
    """
    鼠标回调函数：点击图片显示 HSV 值
    """
    if event == cv2.EVENT_LBUTTONDOWN:
        frame = param
        # 1. 转换到 HSV 空间
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 2. 获取点击点的 HSV 值
        hsv_value = hsv_frame[y, x]
        h_val, s_val, v_val = hsv_value[0], hsv_value[1], hsv_value[2]
        
        print("-" * 40)
        print(f"点击坐标: ({x}, {y})")
        print(f"当前点 HSV: H={h_val}, S={s_val}, V={v_val}")
        
        # 3. 智能推荐阈值 (比当前值稍微宽容一点)
        rec_lower = f"[{max(0, h_val-5)}, {max(0, s_val-30)}, {max(0, v_val-30)}]"
        rec_upper = f"[{min(180, h_val+5)}, 255, 255]"
        print(f"建议 lower_yellow 参考值: np.array({rec_lower})")
        print("-" * 40)

def fix_iccp_warning(image):
    if image is None: return None
    _, encoded_img = cv2.imencode('.jpg', image)
    decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
    return decoded_img

def main():
    hkki_camera = Camera.Camera()
    print("正在获取图像用于取色...")
    try:
        # 获取图像
        raw_image = hkki_camera.getCameraData()
        if raw_image is None:
            print("未获取到图像")
            return
        # 消除警告
        image = fix_iccp_warning(raw_image)
    except Exception as e:
        print(f"相机出错: {e}")
        return
    finally:
        # 记得关闭相机，防止下次占用
         if hasattr(hkki_camera, 'CloseCamera'):
            hkki_camera.CloseCamera()

    # 创建窗口
    win_name = "Color Picker (Click Yellow Object)"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 1024, 768)
    
    # 设置鼠标回调
    cv2.setMouseCallback(win_name, pick_color, image)

    print("\n" + "="*50)
    print("【操作指南】")
    print("1. 图像窗口已打开。")
    print("2. 请用鼠标左键点击图中【黄色物体最暗】的地方。")
    print("3. 看控制台输出的 HSV 数值。")
    print("4.按任意键退出程序。")
    print("="*50 + "\n")

    cv2.imshow(win_name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()