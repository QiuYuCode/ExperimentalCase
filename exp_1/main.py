import sys
import time
import yaml
import cv2
import numpy as np
from pathlib import Path

# --- 1. 路径设置 (绝对路径锚点) ---
current_file_path = Path(__file__).resolve()
# exp_dir 就是 D:\ExperimentalCase\exp_1 (脚本所在的文件夹)
exp_dir = current_file_path.parent
root_path = current_file_path.parent.parent
sys.path.append(str(root_path))

try:
    from common import Camera
except ImportError:
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
            if 'lower1' in params: 
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

def ensure_numpy(val):
    if isinstance(val, list):
        return np.array(val, dtype=np.uint8)
    return val

def run_detection_once(image, cfg):
    """
    执行一次检测并保存
    返回: (save_path_str, center_x, center_y)
    """
    mode = cfg['system']['current_task']
    colors = cfg['colors']

    if mode not in colors:
        print(f"ERROR: 未知的任务模式 '{mode}'")
        return None, 0, 0

    param = colors[mode]
    image_draw = image.copy()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 生成掩膜
    if 'lower1' in param:
        l1 = ensure_numpy(param['lower1'])
        u1 = ensure_numpy(param['upper1'])
        l2 = ensure_numpy(param['lower2'])
        u2 = ensure_numpy(param['upper2'])
        mask1 = cv2.inRange(hsv, l1, u1)
        mask2 = cv2.inRange(hsv, l2, u2)
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        l = ensure_numpy(param['lower'])
        u = ensure_numpy(param['upper'])
        mask = cv2.inRange(hsv, l, u)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected = False
    max_area = 0
    best_cnt = None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 1500:
            if area > max_area:
                max_area = area
                best_cnt = cnt
                detected = True

    save_path_str = ""
    cx, cy = 0, 0
    draw_color = tuple(param.get('draw_color', [0, 255, 0]))
    
    if detected and best_cnt is not None:
        rect = cv2.minAreaRect(best_cnt)
        box = cv2.boxPoints(rect)
        box = np.intp(box)

        cx_float, cy_float = rect[0]
        cx = int(cx_float)
        cy = int(cy_float)
        
        cv2.drawContours(image_draw, [box], 0, draw_color, 3)
        cv2.drawMarker(image_draw, (cx, cy), draw_color, cv2.MARKER_CROSS, 20, 3)
        cv2.putText(image_draw, f"({cx},{cy})", (cx + 15, cy), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)
        
        top_point = min(box, key=lambda p: p[1])
        cv2.putText(image_draw, f"{mode.upper()}", (top_point[0], top_point[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, draw_color, 2)

        # --- 【关键修复：路径强制锚定】---
        # 读取配置中的保存路径 (例如 "./saved_images")
        raw_root = cfg['system']['save_root']
        
        # 强制转换为基于 exp_dir 的绝对路径
        if raw_root.startswith("."):
            # 将 "./saved_images" 拼接在 "D:\ExperimentalCase\exp_1" 后面
            save_root = (exp_dir / raw_root).resolve()
        else:
            save_root = Path(raw_root)

        sub_folder = param['save_folder']
        save_dir = save_root / sub_folder
        save_dir.mkdir(parents=True, exist_ok=True) # 自动创建所有不存在的父级目录

        filename = f"{mode}.jpg"
        save_full_path = save_dir / filename
        
        cv2.imwrite(str(save_full_path), image_draw)
        
        # 返回绝对路径字符串，方便 C# 读取
        save_path_str = str(save_full_path)
    else:
        save_path_str = "NOT_FOUND"

    if cfg['system']['show_window']:
        cv2.imshow("Result", image_draw)
        cv2.waitKey(2000)
        cv2.destroyAllWindows()

    return save_path_str, cx, cy

# --- 4. 主入口 ---
def main():
    config_path = exp_dir / "config.yaml"
    cfg_mgr = ConfigManager(config_path)
    
    hkki_camera = None
    try:
        hkki_camera = Camera.Camera()
        time.sleep(0.5) 
    except Exception as e:
        print(f"ERROR: 相机启动失败 - {e}")
        sys.exit(1)

    try:
        raw_image = hkki_camera.getCameraData()
        if raw_image is None:
            print("ERROR: 取图失败 (Empty Frame)")
            sys.exit(1)

        image = fix_iccp_warning(raw_image)

        result_path, center_x, center_y = run_detection_once(image, cfg_mgr.config)

        # 输出绝对路径，确保 C# 能找到文件
        if result_path and result_path != "NOT_FOUND":
            print(f"SUCCESS|{result_path}|{center_x}|{center_y}")
        else:
            print("SUCCESS|NOT_FOUND|0|0")

    except Exception as e:
        print(f"ERROR: 处理过程异常 - {e}")
    finally:
        if hasattr(hkki_camera, 'CloseCamera'):
            hkki_camera.CloseCamera()

if __name__ == "__main__":
    main()