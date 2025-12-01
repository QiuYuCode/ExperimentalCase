import sys
import os
import time
from pathlib import Path
import cv2
import numpy as np

# 1. 路径设置
current_file_path = Path(__file__).resolve()
# 根目录 D:\ExperimentalCase
root_path = current_file_path.parent.parent
# 当前实验目录 D:\ExperimentalCase\exp_1
exp_dir = current_file_path.parent

sys.path.append(str(root_path))

from common import Camera

# --- 新增：定义保存图片的根目录 ---
# 图片将保存在 D:\ExperimentalCase\exp_1\saved_images 下
SAVE_ROOT_DIR = exp_dir / "saved_images"

def fix_iccp_warning(image):
    """
    【解决 libpng warning 的辅助函数】
    通过将图像编码为内存中的 JPG 再解码回来，去除不标准的 iCCP 为。
    这是一个常见的消除该警告的 trick。
    """
    if image is None: return None
    # 编码成 jpg 格式到内存缓冲
    _, encoded_img = cv2.imencode('.jpg', image)
    # 再从内存缓冲解码回来
    decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
    return decoded_img

def process_and_save_yellow(image_input):
    """
    识别黄色物体，画框，并保存结果图像。
    """
    if image_input is None:
        return None

    # 复制一份图像用于绘图，避免修改原图（如果后续还要识别红色，需要用原图）
    image_to_draw = image_input.copy()

    # --- 1. HSV 转换与阈值设定 ---
    hsv_img = cv2.cvtColor(image_to_draw, cv2.COLOR_BGR2HSV)
    # 黄色阈值 (根据需要调整 S 和 V 的下限)
    lower_yellow = np.array([69, 39, 154])
    upper_yellow = np.array([90, 255, 255])

    # --- 2. 掩膜与形态学操作 ---
    mask = cv2.inRange(hsv_img, lower_yellow, upper_yellow)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # 增加闭运算填充内部

    # --- 3. 查找轮廓 ---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_something = False
    for cnt in contours:
        # 过滤小面积噪点
        if cv2.contourArea(cnt) > 1500:
            detected_something = True
            x, y, w, h = cv2.boundingRect(cnt)
            # 画框 (绿色)
            cv2.rectangle(image_to_draw, (x, y), (x + w, y + h), (0, 0, 255), 3)
            # 写字
            cv2.putText(image_to_draw, "Yellow Detected", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # --- 4. 保存逻辑 (如果检测到了物体) ---
    if detected_something:
        # 定义具体颜色的保存路径: D:\ExperimentalCase\exp_1\saved_images\yellow
        color_save_dir = SAVE_ROOT_DIR / "yellow"
        
        # 关键：自动创建目录（如果不存在），parents=True表示如果父目录不存在也一并创建
        color_save_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名 (使用时间戳)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"yellow_result_{timestamp}.jpg"
        save_path = color_save_dir / filename
        
        # 保存绘制了结果的图像
        # 注意：windows路径有时需要转成字符串给opencv用
        cv2.imwrite(str(save_path), image_to_draw)
        print(f"[保存成功] 已将识别结果保存至: {save_path}")
    else:
        print("[识别结果] 未检测到明显的黄色物体，跳过保存。")

    return image_to_draw

def main():
    # 实例化相机
    hkki_camera = Camera.Camera()
    
    try:
        print("等待相机取图，请按提示输入...")
        raw_image = hkki_camera.getCameraData()

        if raw_image is None:
            print("错误：未获取到图像数据")
            return

        print(f"成功获取图像，原始尺寸: {raw_image.shape}")

        # --- 修复步骤：消除 libpng 警告 ---
        print("正在处理图像数据以消除警告...")
        clean_image = fix_iccp_warning(raw_image)

        # --- 核心步骤：识别黄色并保存 ---
        # 这里传入清洗过的图像
        result_image = process_and_save_yellow(clean_image)

        # (未来扩展：识别红色)
        # 你可以复制 process_and_save_yellow 改名为 process_and_save_red
        # 修改里面的 HSV 阈值和保存路径为 "red"
        # result_image_red = process_and_save_red(clean_image) 

        # 显示结果
        # cv2.namedWindow("Final Result", cv2.WINDOW_NORMAL) 
        # # 将窗口缩小一点，方便查看
        # cv2.resizeWindow("Final Result", 1024, 768)
        # cv2.imshow("Final Result", result_image)
        
        # print("按任意键退出程序...")
        # cv2.waitKey(0)

    except Exception as e:
        print(f"发生严重错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保相机资源被释放
        print("正在关闭相机连接...")
        if hasattr(hkki_camera, 'CloseCamera'):
            hkki_camera.CloseCamera()
        cv2.destroyAllWindows()
        print("程序结束。")

if __name__ == "__main__":
    main()