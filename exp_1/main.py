import sys
import time
import yaml
import cv2
import numpy as np
import math  # 需要导入 math 库计算角度
from pathlib import Path

# --- 1. 路径设置 ---
current_file_path = Path(__file__).resolve()
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

# --- 【新增】绘制旋转文字的辅助函数 ---
def draw_rotated_text(img, text, center, angle, color, scale, thickness):
    """
    在图像上绘制旋转的文字
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    # 1. 获取文字大小
    text_size, baseline = cv2.getTextSize(text, font, scale, thickness)
    w, h = text_size
    
    # 2. 创建一个足够大的临时画布 (为了容纳旋转后的文字)
    # 画布大小设为文字宽度的1.5倍，确保旋转不出界
    canvas_w = int(w * 1.5) + 20
    canvas_h = int(w * 1.5) + 20
    
    # 创建纯黑背景画布
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
    
    # 3. 在画布中心绘制文字
    tx = (canvas_w - w) // 2
    ty = (canvas_h + h) // 2a
    cv2.putText(canvas, text, (tx, ty), font, scale, color, thickness)
    
    # 4. 计算旋转矩阵 (围绕画布中心旋转)
    M = cv2.getRotationMatrix2D((canvas_w // 2, canvas_h // 2), angle, 1.0)
    
    # 5. 旋转画布
    rotated_canvas = cv2.warpAffine(canvas, M, (canvas_w, canvas_h))
    
    # 6. 将旋转后的文字融合到原图上
    # 计算原图上的粘贴位置 (以 center 为中心)
    x_start = int(center[0] - canvas_w // 2)
    y_start = int(center[1] - canvas_h // 2)
    x_end = x_start + canvas_w
    y_end = y_start + canvas_h
    
    # 边界检查，防止越界
    if x_start < 0 or y_start < 0 or x_end > img.shape[1] or y_end > img.shape[0]:
        return # 如果文字出界就不画了，防止报错

    # 提取 ROI (感兴趣区域)
    roi = img[y_start:y_end, x_start:x_end]
    
    # 创建掩膜：只有文字部分是白色的
    img2gray = cv2.cvtColor(rotated_canvas, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)
    
    # 抠图与融合
    img_bg = cv2.bitwise_and(roi, roi, mask=mask_inv) # 原图背景
    img_fg = cv2.bitwise_and(rotated_canvas, rotated_canvas, mask=mask) # 文字前景
    dst = cv2.add(img_bg, img_fg)
    
    # 放回原图
    img[y_start:y_end, x_start:x_end] = dst

def run_detection_once(image, cfg):
    mode = cfg['system']['current_task']
    colors = cfg['colors']

    if mode not in colors:
        print(f"ERROR: 未知的任务模式 '{mode}'")
        return None, 0, 0

    param = colors[mode]
    image_draw = image.copy()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 掩膜处理
    if 'lower1' in param:
        l1 = ensure_numpy(param['lower1']); u1 = ensure_numpy(param['upper1'])
        l2 = ensure_numpy(param['lower2']); u2 = ensure_numpy(param['upper2'])
        mask = cv2.bitwise_or(cv2.inRange(hsv, l1, u1), cv2.inRange(hsv, l2, u2))
    else:
        l = ensure_numpy(param['lower']); u = ensure_numpy(param['upper'])
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
        
        # 计算尺寸
        dim1, dim2 = rect[1]
        pixel_len = max(dim1, dim2)
        pixel_wid = min(dim1, dim2)
        
        scale = cfg['system'].get('pixels_per_mm', 1.0)
        if scale <= 0: scale = 1.0
        real_len = pixel_len / scale
        real_wid = pixel_wid / scale

        # 绘图
        cv2.drawContours(image_draw, [box], 0, draw_color, 3)
        cv2.drawMarker(image_draw, (cx, cy), draw_color, cv2.MARKER_CROSS, 20, 3)

        # --- 【关键修改：计算角度并绘制旋转文字，且向外偏移】 ---
        drawn_len = False
        drawn_wid = False

        for i in range(4):
            p1 = box[i]
            p2 = box[(i + 1) % 4]

            edge_len = np.linalg.norm(p1 - p2)
            mid_x = int((p1[0] + p2[0]) / 2)
            mid_y = int((p1[1] + p2[1]) / 2)
            
            # --- 新增：计算向外偏移后的文字中心点 ---
            # 1. 计算从矩形中心指向边中点的向量
            vec_x = mid_x - cx
            vec_y = mid_y - cy
            
            # 2. 归一化向量 (得到指向外侧的单位方向向量)
            vec_len = math.sqrt(vec_x**2 + vec_y**2)
            if vec_len < 1e-3: vec_len = 1 # 防止除零
            norm_x = vec_x / vec_len
            norm_y = vec_y / vec_len
            
            # 3. 向外偏移一定距离 (例如 35 像素，可根据需要调整)
            shift_dist = 35 
            text_cx = int(mid_x + norm_x * shift_dist)
            text_cy = int(mid_y + norm_y * shift_dist)
            text_center = (text_cx, text_cy)
            # ------------------------------------

            # 计算边的角度
            angle_rad = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            angle_deg = angle_rad * 180 / math.pi
            
            # 调整角度，保证文字便于阅读
            text_angle = angle_deg
            if text_angle < -90: text_angle += 180
            elif text_angle > 90: text_angle -= 180
            
            # 判断这条边是"长"还是"宽"
            if not drawn_len and abs(edge_len - pixel_len) < 10:
                text = f"H:{real_len:.1f}"
                # 使用计算出的新的、向外偏移的中心点
                draw_rotated_text(image_draw, text, text_center, text_angle, draw_color, 0.6, 2)
                drawn_len = True

            elif not drawn_wid and abs(edge_len - pixel_wid) < 10:
                text = f"W:{real_wid:.1f}"
                # 使用计算出的新的、向外偏移的中心点
                draw_rotated_text(image_draw, text, text_center, text_angle, draw_color, 0.6, 2)
                drawn_wid = True

        # 保存图片
        raw_root = cfg['system']['save_root']
        if raw_root.startswith("."):
            save_root = (exp_dir / raw_root).resolve()
        else:
            save_root = Path(raw_root)

        sub_folder = param['save_folder']
        save_dir = save_root / sub_folder
        save_dir.mkdir(parents=True, exist_ok=True)

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
            print("ERROR: 取图失败")
            sys.exit(1)

        image = fix_iccp_warning(raw_image)
        result_path, center_x, center_y = run_detection_once(image, cfg_mgr.config)

        if result_path and result_path != "NOT_FOUND":
            print(f"SUCCESS|{result_path}|{center_x}|{center_y}")
        else:
            print("SUCCESS|NOT_FOUND|0|0")

    except Exception as e:
        print(f"ERROR: 处理异常 - {e}")
    finally:
        if hasattr(hkki_camera, 'CloseCamera'):
            hkki_camera.CloseCamera()

if __name__ == "__main__":
    main()