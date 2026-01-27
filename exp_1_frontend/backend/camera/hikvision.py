# -- coding: utf-8 --

import sys
import logging
from pathlib import Path
from typing import Optional
import numpy as np

# 添加 common 目录到路径
current_dir = Path(__file__).resolve().parent.parent.parent.parent
common_dir = current_dir / "common"
sys.path.insert(0, str(common_dir))

try:
    from common import Camera as HikCamera
except ImportError:
    HikCamera = None

try:
    from .base import CameraBase
except ImportError:
    from camera.base import CameraBase

logger = logging.getLogger(__name__)


class HikvisionCamera(CameraBase):
    """海康工业相机实现"""
    
    def __init__(self, config: dict = None):
        """
        初始化海康相机
        
        Args:
            config: 配置字典，可包含设备索引等
        """
        super().__init__(config)
        self.camera = None
        self.device_index = config.get('device_index', 0) if config else 0
    
    def connect(self) -> bool:
        """连接海康相机"""
        if HikCamera is None:
            logger.error("无法导入海康相机模块，请检查 common/Camera.py 是否存在")
            return False
        
        try:
            self.camera = HikCamera.Camera()
            if self.camera.is_open:
                self._connected = True
                logger.info("海康相机连接成功")
                return True
            else:
                logger.error("海康相机连接失败：相机未打开")
                return False
        except Exception as e:
            logger.error(f"海康相机连接异常: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开海康相机连接"""
        if self.camera and hasattr(self.camera, 'CloseCamera'):
            try:
                self.camera.CloseCamera()
            except Exception as e:
                logger.error(f"关闭海康相机异常: {e}")
        self.camera = None
        self._connected = False
        logger.info("海康相机已断开")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取一帧图像
        
        Returns:
            np.ndarray | None: BGR格式图像，失败返回None
        """
        if not self._connected or self.camera is None:
            logger.warning("相机未连接，无法获取图像")
            return None
        
        try:
            frame = self.camera.getCameraData()
            if frame is None:
                return None
            
            # 确保返回BGR格式（3通道）
            if len(frame.shape) == 2:
                # 灰度图转BGR
                import cv2
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 1:
                # 单通道转BGR
                import cv2
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
            return frame
        except Exception as e:
            logger.error(f"获取海康相机图像异常: {e}")
            return None
    
    def get_info(self) -> dict:
        """获取海康相机信息"""
        return {
            'type': 'hikvision',
            'name': f'Hikvision Camera #{self.device_index}',
            'connected': self._connected,
            'device_index': self.device_index
        }
