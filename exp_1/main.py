import sys
import time
import yaml
import cv2
import numpy as np
from pathlib import Path

# --- 1. 路径设置 ---
current_file_path = Path(__file__).resolve()
root_path = current_file_path.parent.parent
exp_dir = current_file_path.parent
sys.path.append(str(root_path))

try:
    from common import Camera
except ImportError:
    # print 输出会被 C# 捕获，以 ERROR: 开头方便 C# 判断
    print("ERROR: 找不到 common 模块")
    sys.exit(1)

# --- 2. 配置加载 ---
class ConfigManager:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)

    def load_config(self, path):
        if not path.exists():
            print("ERROR: 找不到 config.yaml")
            sys.exit(1)

        with open(path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)

        # 预处理 numpy 数组
        for color_name, params in cfg['colors'].items():
            if 'lower' in params:
                params['lower'] = np.array(params['lower'], dtype=np.uint8)
                params['upper'] = np.array(params['upper'], dtype=np.uint8)
            if 'lower1' in params: # 红色双区间
                params['lower1'] = np.array(params['lower1'], dtype=np.uint8)
                params['upper1'] = np.array(params['upper1'], dtype=np.uint8)
                params['lower2'] = np.array(params['lower2'], dtype=np.uint8)
                params['upper2'] = np.array(params['upper2'], dtype=np.uint8)
            if 'draw_color' in params:
                params['draw_color'] = tuple(params['draw_color'])
        return cfg

# --- 3. 图像处理 ---
def fix_iccp_warning(image):
    if image is None: return None
    _, encoded_img = cv2.imencode('.jpg', image)
    return cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

def run_detection_once(image, cfg):
    """执行一次检测并保存"""
    mode = cfg['system']['current_task'] # 从配置读取当前任务
    colors = cfg['colors']

    if mode not in colors:
        print(f"ERROR: 未知的任务模式 '{mode}'，请检查 yaml 配置")
        return None

    param = colors[mode]
    image_draw = image.copy()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 1. 生成掩膜
    if 'lower1' in param:
        mask1 = cv2.inRange(hsv, param['lower1'], param['upper1'])
        mask2 = cv2.inRange(hsv, param['lower2'], param['upper2'])
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        mask = cv2.inRange(hsv, param['lower'], param['upper'])

    # 2. 查找轮廓
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected = False
    max_area = 0
    best_cnt = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 1500: # 面积阈值
            if area > max_area:
                max_area = area
                best_cnt = cnt
                detected = True

    save_path_str = ""
    
    # 3. 如果识别成功，画图并保存
    if detected and best_cnt is not None:
        x, y, w, h = cv2.boundingRect(best_cnt)
        cv2.rectangle(image_draw, (x, y), (x + w, y + h), param['draw_color'], 3)
        cv2.putText(image_draw, f"{mode.upper()}", (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, param['draw_color'], 2)

        # 构造路径
        save_root = Path(cfg['system']['save_root'])
        sub_folder = param['save_folder']
        save_dir = save_root / sub_folder
        save_dir.mkdir(parents=True, exist_ok=True) # 自动创建文件夹

        filename = f"{mode}.jpg"
        save_full_path = save_dir / filename
        
        cv2.imwrite(str(save_full_path), image_draw)
        save_path_str = str(save_full_path)
    else:
        # 如果没识别到，也可以选择保存一张原图，或者留空
        save_path_str = "NOT_FOUND"

    # 4. 可选：弹窗显示 (调试用)
    if cfg['system']['show_window']:
        cv2.imshow("Result", image_draw)
        cv2.waitKey(2000) # 显示 2 秒后自动关闭
        cv2.destroyAllWindows()

    return save_path_str

# --- 4. 主入口 ---
def main():
    # 1. 读取配置
    config_path = exp_dir / "config.yaml"
    cfg_mgr = ConfigManager(config_path)
    
    # 2. 初始化相机
    hkki_camera = None
    try:
        hkki_camera = Camera.Camera()
        # ⚠️ 重要：海康相机刚启动第一帧可能是黑的或正在自动曝光
        # 建议稍微等一下，或者丢弃前几帧
        time.sleep(0.5) 
    except Exception as e:
        print(f"ERROR: 相机启动失败 - {e}")
        sys.exit(1)

    try:
        # 3. 抓拍一张图片
        raw_image = hkki_camera.getCameraData()
        
        if raw_image is None:
            print("ERROR: 取图失败 (Empty Frame)")
            sys.exit(1)

        image = fix_iccp_warning(raw_image)

        # 4. 识别并处理
        result_path = run_detection_once(image, cfg_mgr.config)

        # 5. 【关键】输出结果给 C#
        # C# 读取 Console.ReadLine() 就能拿到这个路径
        if result_path and result_path != "NOT_FOUND":
            print(f"SUCCESS|{result_path}")
        else:
            print("SUCCESS|NOT_FOUND")

    except Exception as e:
        print(f"ERROR: 处理过程异常 - {e}")
    finally:
        # 6. 必须关闭相机
        if hasattr(hkki_camera, 'CloseCamera'):
            hkki_camera.CloseCamera()

if __name__ == "__main__":
    main()