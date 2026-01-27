# -- coding: utf-8 --

import cv2
import numpy as np
from typing import Union


def fix_iccp_warning(image: np.ndarray) -> np.ndarray:
    """
    修复 ICCP 警告（通过编码/解码）
    
    Args:
        image: 输入图像
        
    Returns:
        np.ndarray: 处理后的图像
    """
    if image is None:
        return None
    _, encoded_img = cv2.imencode('.jpg', image)
    return cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)


def ensure_numpy(val: Union[list, np.ndarray]) -> np.ndarray:
    """
    确保输入为numpy数组
    
    Args:
        val: 列表或numpy数组
        
    Returns:
        np.ndarray: numpy数组
    """
    if isinstance(val, list):
        return np.array(val, dtype=np.uint8)
    return val


def draw_rotated_text(img: np.ndarray, text: str, center: tuple, angle: float, 
                      color: tuple, scale: float, thickness: int):
    """
    在图像上绘制旋转文字（带边界检查）
    
    Args:
        img: 目标图像
        text: 要绘制的文字
        center: 文字中心坐标 (x, y)
        angle: 旋转角度（度）
        color: 文字颜色 (B, G, R)
        scale: 文字缩放比例
        thickness: 文字粗细
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size, baseline = cv2.getTextSize(text, font, scale, thickness)
    w, h = text_size
    
    canvas_w = int(w * 1.5) + 20
    canvas_h = int(w * 1.5) + 20
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
    
    tx = (canvas_w - w) // 2
    ty = (canvas_h + h) // 2
    cv2.putText(canvas, text, (tx, ty), font, scale, color, thickness)
    
    M = cv2.getRotationMatrix2D((canvas_w // 2, canvas_h // 2), angle, 1.0)
    rotated_canvas = cv2.warpAffine(canvas, M, (canvas_w, canvas_h))
    
    x_start = int(center[0] - canvas_w // 2)
    y_start = int(center[1] - canvas_h // 2)
    x_end = x_start + canvas_w
    y_end = y_start + canvas_h
    
    if x_start >= img.shape[1] or y_start >= img.shape[0] or x_end <= 0 or y_end <= 0:
        return
    
    x1 = max(0, x_start)
    y1 = max(0, y_start)
    x2 = min(img.shape[1], x_end)
    y2 = min(img.shape[0], y_end)
    
    canvas_x1 = x1 - x_start
    canvas_y1 = y1 - y_start
    canvas_x2 = canvas_x1 + (x2 - x1)
    canvas_y2 = canvas_y1 + (y2 - y1)
    
    roi = img[y1:y2, x1:x2]
    rotated_crop = rotated_canvas[canvas_y1:canvas_y2, canvas_x1:canvas_x2]
    
    img2gray = cv2.cvtColor(rotated_crop, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(img2gray, 1, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)
    
    img_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
    img_fg = cv2.bitwise_and(rotated_crop, rotated_crop, mask=mask)
    dst = cv2.add(img_bg, img_fg)
    
    img[y1:y2, x1:x2] = dst
