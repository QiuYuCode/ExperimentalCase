# -- coding: utf-8 --

import cv2
import numpy as np
import math
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from .image_utils import ensure_numpy, draw_rotated_text


@dataclass
class DetectionResult:
    """检测结果数据类"""
    detected: bool
    color_name: Optional[str] = None
    center: Optional[Tuple[int, int]] = None
    size_mm: Optional[Tuple[float, float]] = None  # (length, width)
    area: float = 0.0
    image_path: Optional[str] = None
    annotated_image: Optional[np.ndarray] = None


class ColorDetector:
    """颜色检测器"""
    
    def __init__(self, config: Dict[str, Any], save_root: Optional[Path] = None):
        """
        初始化颜色检测器
        
        Args:
            config: 配置字典，包含 'colors' 和 'system' 键
            save_root: 结果保存根目录，如果为None则使用config中的save_root
        """
        self.config = config
        self.colors = config.get('colors', {})
        self.system_config = config.get('system', {})
        
        if save_root is None:
            save_root_str = self.system_config.get('save_root', './saved_images')
            if save_root_str.startswith('.'):
                # 相对路径，相对于当前工作目录
                self.save_root = Path(save_root_str).resolve()
            else:
                self.save_root = Path(save_root_str)
        else:
            self.save_root = save_root
        
        self.pixels_per_mm = self.system_config.get('pixels_per_mm', 1.0)
        if self.pixels_per_mm <= 0:
            self.pixels_per_mm = 1.0
    
    def detect_single_color(self, image: np.ndarray, hsv: np.ndarray, 
                           color_name: str, param: Dict[str, Any]) -> Tuple[float, Optional[np.ndarray], str, Dict]:
        """
        检测单一颜色
        
        Args:
            image: 原始BGR图像
            hsv: HSV色彩空间图像
            color_name: 颜色名称
            param: 颜色参数配置
            
        Returns:
            Tuple[面积, 轮廓, 颜色名, 参数]
        """
        # 判断是单区间还是双区间检测
        if 'lower1' in param:
            # 双区间检测（如红色）
            l1 = ensure_numpy(param['lower1'])
            u1 = ensure_numpy(param['upper1'])
            l2 = ensure_numpy(param['lower2'])
            u2 = ensure_numpy(param['upper2'])
            mask = cv2.bitwise_or(
                cv2.inRange(hsv, l1, u1),
                cv2.inRange(hsv, l2, u2)
            )
        else:
            # 单区间检测
            l = ensure_numpy(param['lower'])
            u = ensure_numpy(param['upper'])
            mask = cv2.inRange(hsv, l, u)
        
        # 形态学处理：开运算去噪
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 轮廓检测
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 找出面积最大的轮廓
        max_area = 0
        best_cnt = None
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1500 and area > max_area:
                max_area = area
                best_cnt = cnt
        
        return max_area, best_cnt, color_name, param
    
    def detect(self, image: np.ndarray, mode: Optional[str] = None) -> DetectionResult:
        """
        执行颜色检测
        
        Args:
            image: 输入图像（BGR格式）
            mode: 检测模式，None表示自动识别所有颜色中面积最大的，否则检测指定颜色
            
        Returns:
            DetectionResult: 检测结果
        """
        if image is None or image.size == 0:
            return DetectionResult(detected=False)
        
        # 转换为HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 确定候选颜色
        if mode is not None:
            if mode not in self.colors:
                return DetectionResult(detected=False)
            candidates = [(mode, self.colors[mode])]
        else:
            # 自动识别模式：遍历所有颜色
            candidates = list(self.colors.items())
        
        # 对所有候选颜色进行检测，找出面积最大的
        best_result = (0, None, None, None)  # (面积, 轮廓, 颜色名, 参数)
        for color_name, param in candidates:
            result = self.detect_single_color(image, hsv, color_name, param)
            if result[0] > best_result[0]:
                best_result = result
        
        max_area, best_cnt, detected_color, param = best_result
        detected = best_cnt is not None
        
        if not detected:
            return DetectionResult(detected=False)
        
        # 绘制检测结果
        image_draw = image.copy()
        draw_color = tuple(map(int, param.get('draw_color', [0, 255, 0])))
        
        # 计算最小外接矩形
        rect = cv2.minAreaRect(best_cnt)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        
        # 中心点
        cx, cy = int(rect[0][0]), int(rect[0][1])
        
        # 计算长宽（像素 -> mm）
        dim1, dim2 = rect[1]
        pixel_len = max(dim1, dim2)
        pixel_wid = min(dim1, dim2)
        real_len = pixel_len / self.pixels_per_mm
        real_wid = pixel_wid / self.pixels_per_mm
        
        # 绘制矩形框和中心标记
        cv2.drawContours(image_draw, [box], 0, draw_color, 3)
        cv2.drawMarker(image_draw, (cx, cy), draw_color, cv2.MARKER_CROSS, 20, 3)
        
        # 绘制长宽文字（沿边旋转）
        drawn_len = False
        drawn_wid = False
        for i in range(4):
            p1 = box[i]
            p2 = box[(i + 1) % 4]
            edge_len = np.linalg.norm(p1 - p2)
            mid_x = int((p1[0] + p2[0]) / 2)
            mid_y = int((p1[1] + p2[1]) / 2)
            
            # 计算文字位置：向外偏移
            vec_x, vec_y = mid_x - cx, mid_y - cy
            vec_len = math.sqrt(vec_x**2 + vec_y**2)
            if vec_len < 1e-3:
                vec_len = 1
            shift_dist = 40
            text_cx = int(mid_x + vec_x / vec_len * shift_dist)
            text_cy = int(mid_y + vec_y / vec_len * shift_dist)
            
            # 计算旋转角度
            angle_rad = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            text_angle = angle_rad * 180 / math.pi
            if text_angle < -90:
                text_angle += 180
            elif text_angle > 90:
                text_angle -= 180
            
            if not drawn_len and abs(edge_len - pixel_len) < 10:
                draw_rotated_text(image_draw, f"L:{real_len:.1f}", 
                                 (text_cx, text_cy), text_angle, draw_color, 0.7, 2)
                drawn_len = True
            elif not drawn_wid and abs(edge_len - pixel_wid) < 10:
                draw_rotated_text(image_draw, f"W:{real_wid:.1f}", 
                                 (text_cx, text_cy), text_angle, draw_color, 0.7, 2)
                drawn_wid = True
        
        # 绘制颜色标签
        top_point = min(box, key=lambda p: p[1])
        label_x = top_point[0] - 20
        label_y = max(40, top_point[1] - 20)
        cv2.putText(image_draw, detected_color.upper(), (label_x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, draw_color, 2)
        
        # 保存图片
        save_folder = param.get('save_folder', 'results')
        save_dir = self.save_root / save_folder
        save_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{detected_color}.jpg"
        save_full_path = save_dir / filename
        cv2.imwrite(str(save_full_path), image_draw)
        
        return DetectionResult(
            detected=True,
            color_name=detected_color,
            center=(cx, cy),
            size_mm=(real_len, real_wid),
            area=max_area,
            image_path=str(save_full_path),
            annotated_image=image_draw
        )
    
    def detect_with_hsv(self, image: np.ndarray, hsv_lower: np.ndarray, 
                       hsv_upper: np.ndarray) -> np.ndarray:
        """
        使用指定的HSV范围进行检测，返回掩码（用于参数调试）
        
        Args:
            image: 输入图像
            hsv_lower: HSV下限
            hsv_upper: HSV上限
            
        Returns:
            np.ndarray: 二值掩码
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
        
        # 形态学处理
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask
