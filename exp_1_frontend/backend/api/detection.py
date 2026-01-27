# -- coding: utf-8 --

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import logging
import base64
import cv2
import numpy as np

try:
    from ..detection import ColorDetector, fix_iccp_warning
    from ..api.camera import _current_camera
except ImportError:
    from backend.detection import ColorDetector, fix_iccp_warning
    from backend.api.camera import _current_camera

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/detection", tags=["detection"])

# 全局检测器实例
_detector: Optional[ColorDetector] = None


def set_detector(detector: ColorDetector):
    """设置检测器实例"""
    global _detector
    _detector = detector


@router.post("/detect")
async def detect_color(request: Dict[str, Any] = None) -> Dict[str, Any]:
    if request is None:
        request = {}
    mode = request.get('mode')
    use_camera = request.get('use_camera', True)
    """
    执行颜色检测
    
    Args:
        mode: 检测模式，None表示自动识别
        use_camera: 是否使用相机获取图像，False则需要在请求体中提供图像
    """
    global _detector, _current_camera
    
    if _detector is None:
        raise HTTPException(status_code=500, detail="检测器未初始化")
    
    try:
        # 获取图像
        if use_camera:
            if _current_camera is None or not _current_camera.is_connected():
                raise HTTPException(status_code=400, detail="相机未连接")
            image = _current_camera.get_frame()
            if image is None:
                raise HTTPException(status_code=500, detail="获取图像失败")
        else:
            # 从请求体获取图像（Base64）
            raise HTTPException(status_code=501, detail="暂不支持从请求体获取图像")
        
        # 修复ICCP警告
        image = fix_iccp_warning(image)
        
        # 执行检测
        result = _detector.detect(image, mode=mode)
        
        # 编码结果图像
        result_image_base64 = None
        if result.annotated_image is not None:
            _, buffer = cv2.imencode('.jpg', result.annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            result_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'success': result.detected,
            'detected': result.detected,
            'color_name': result.color_name,
            'center': result.center,
            'size_mm': result.size_mm,
            'area': result.area,
            'image_path': result.image_path,
            'annotated_image': f'data:image/jpeg;base64,{result_image_base64}' if result_image_base64 else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检测异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-hsv")
async def detect_with_hsv(request: Dict[str, Any]) -> Dict[str, Any]:
    hsv_lower = request.get('hsv_lower', [0, 0, 0])
    hsv_upper = request.get('hsv_upper', [180, 255, 255])
    use_camera = request.get('use_camera', True)
    """
    使用指定的HSV范围进行检测（用于参数调试）
    
    Args:
        hsv_lower: HSV下限 [H, S, V]
        hsv_upper: HSV上限 [H, S, V]
        use_camera: 是否使用相机获取图像
    """
    global _current_camera
    
    image_base64 = request.get('image')  # 可选：从请求体获取图像
    
    if use_camera:
        if _current_camera is None or not _current_camera.is_connected():
            raise HTTPException(status_code=400, detail="相机未连接")
        image = _current_camera.get_frame()
        if image is None:
            raise HTTPException(status_code=500, detail="获取图像失败")
    elif image_base64:
        # 从Base64解码图像
        import base64
        image_data = base64.b64decode(image_base64.split(',')[-1] if ',' in image_base64 else image_base64)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="图像解码失败")
    else:
        raise HTTPException(status_code=400, detail="需要提供相机或图像数据")
    
    try:
        hsv_lower = np.array(hsv_lower, dtype=np.uint8)
        hsv_upper = np.array(hsv_upper, dtype=np.uint8)
        
        mask = _detector.detect_with_hsv(image, hsv_lower, hsv_upper)
        
        # 创建预览图像（掩码叠加）
        preview = cv2.bitwise_and(image, image, mask=mask)
        
        # 编码结果
        _, buffer = cv2.imencode('.jpg', preview, [cv2.IMWRITE_JPEG_QUALITY, 85])
        preview_base64 = base64.b64encode(buffer).decode('utf-8')
        
        _, buffer_mask = cv2.imencode('.jpg', mask, [cv2.IMWRITE_JPEG_QUALITY, 85])
        mask_base64 = base64.b64encode(buffer_mask).decode('utf-8')
        
        return {
            'success': True,
            'preview': f'data:image/jpeg;base64,{preview_base64}',
            'mask': f'data:image/jpeg;base64,{mask_base64}'
        }
    except Exception as e:
        logger.error(f"HSV检测异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pixel-hsv")
async def get_pixel_hsv(x: int, y: int, use_camera: bool = True) -> Dict[str, Any]:
    # 注意：这里use_camera参数实际上应该从请求体获取，但为了兼容GET请求，保留为查询参数
    """
    获取图像指定像素的HSV值
    
    Args:
        x: 像素X坐标
        y: 像素Y坐标
        use_camera: 是否使用相机获取图像
    """
    global _current_camera
    
    if use_camera:
        if _current_camera is None or not _current_camera.is_connected():
            raise HTTPException(status_code=400, detail="相机未连接")
        image = _current_camera.get_frame()
        if image is None:
            raise HTTPException(status_code=500, detail="获取图像失败")
    else:
        raise HTTPException(status_code=501, detail="暂不支持从请求体获取图像")
    
    try:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        if y >= hsv.shape[0] or x >= hsv.shape[1]:
            raise HTTPException(status_code=400, detail="坐标超出图像范围")
        
        h, s, v = hsv[y, x].tolist()
        
        return {
            'success': True,
            'hsv': [int(h), int(s), int(v)],
            'bgr': image[y, x].tolist()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取像素HSV异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))
