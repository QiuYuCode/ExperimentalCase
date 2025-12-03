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

        # 预处理 numpy 数组 (这是给 main.py 独立运行用的)
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

# --- 新增：辅助函数，确保列表转为 Numpy 数组 ---
def ensure_numpy(val):
    """如果输入是 list，强制转为 np.array，防止 OpenCV 报错"""
    if isinstance(val, list):
        return np.array(val, dtype=np.uint8)
    return val

def run_detection_once(image, cfg):
    """
    执行一次检测并保存
    返回: (save_path_str, center_x, center_y)
    """
    mode = cfg['system']['current_task'] # 从配置读取当前任务
    colors = cfg['colors']

    if mode not in colors:
        print(f"ERROR: 未知的任务模式 '{mode}'，请检查 yaml 配置")
        return None, 0, 0

    param = colors[mode]
    image_draw = image.copy()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # --- 关键修复：在这里进行数据类型转换 ---
    # 无论传入的是 list 还是 numpy array，这里都统一转为 numpy array
    if 'lower1' in param:
        # 双区间处理 (如红色)
        l1 = ensure_numpy(param['lower1'])
        u1 = ensure_numpy(param['upper1'])
        l2 = ensure_numpy(param['lower2'])
        u2 = ensure_numpy(param['upper2'])
        
        mask1 = cv2.inRange(hsv, l1, u1)
        mask2 = cv2.inRange(hsv, l2, u2)
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        # 单区间处理 (如黄色)
        l = ensure_numpy(param['lower'])
        u = ensure_numpy(param['upper'])
        
        mask = cv2.inRange(hsv, l, u)

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
    cx, cy = 0, 0
    
    # 确保颜色也是 tuple 格式 (OpenCV 画图需要 tuple)
    draw_color = tuple(param.get('draw_color', [0, 255, 0]))

    if detected and best_cnt is not None:
        # 获取最小外接旋转矩形
        rect = cv2.minAreaRect(best_cnt)
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        # 计算中心点
        cx_float, cy_float = rect[0]
        cx = int(cx_float)
        cy = int(cy_float)
        
        # 绘制
        cv2.drawContours(image_draw, [box], 0, draw_color, 3)
        cv2.drawMarker(image_draw, (cx, cy), draw_color, cv2.MARKER_CROSS, 20, 3)
        cv2.putText(image_draw, f"({cx},{cy})", (cx + 15, cy), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, draw_color, 2)
        
        top_point = min(box, key=lambda p: p[1])
        cv2.putText(image_draw, f"{mode.upper()}", (top_point[0], top_point[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, draw_color, 2)

        save_root = Path(cfg['system']['save_root'])
        sub_folder = param['save_folder']
        save_dir = save_root / sub_folder
        save_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{mode}.jpg"
        save_full_path = save_dir / filename
        
        cv2.imwrite(str(save_full_path), image_draw)
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