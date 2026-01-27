# -- coding: utf-8 --

import logging
from typing import Optional
import numpy as np
import cv2

try:
    from .base import CameraBase
except ImportError:
    from camera.base import CameraBase

logger = logging.getLogger(__name__)


class USBCamera(CameraBase):
    """USB摄像头实现（使用OpenCV VideoCapture）"""
    
    def __init__(self, config: dict = None):
        """
        初始化USB摄像头
        
        Args:
            config: 配置字典，包含 'index' 键指定摄像头索引（默认0）
        """
        super().__init__(config)
        self.cap = None
        self.device_index = config.get('index', 0) if config else 0
        self.width = config.get('width', None) if config else None
        self.height = config.get('height', None) if config else None
    
    def connect(self) -> bool:
        """连接USB摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.device_index)
            if not self.cap.isOpened():
                logger.error(f"无法打开USB摄像头 #{self.device_index}")
                self._connected = False
                return False
            
            # 设置分辨率（如果指定）
            if self.width:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            if self.height:
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # 测试读取一帧
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.error(f"USB摄像头 #{self.device_index} 无法读取图像")
                self.cap.release()
                self.cap = None
                self._connected = False
                return False
            
            self._connected = True
            logger.info(f"USB摄像头 #{self.device_index} 连接成功")
            return True
        except Exception as e:
            logger.error(f"USB摄像头连接异常: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开USB摄像头连接"""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                logger.error(f"关闭USB摄像头异常: {e}")
        self.cap = None
        self._connected = False
        logger.info(f"USB摄像头 #{self.device_index} 已断开")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取一帧图像
        
        Returns:
            np.ndarray | None: BGR格式图像，失败返回None
        """
        if not self._connected or self.cap is None:
            logger.warning("摄像头未连接，无法获取图像")
            return None
        
        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.warning("读取USB摄像头图像失败")
                return None
            
            # 确保返回BGR格式
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
            return frame
        except Exception as e:
            logger.error(f"获取USB摄像头图像异常: {e}")
            return None
    
    def get_info(self) -> dict:
        """获取USB摄像头信息"""
        info = {
            'type': 'usb',
            'name': f'USB Camera #{self.device_index}',
            'connected': self._connected,
            'device_index': self.device_index
        }
        
        if self.cap is not None:
            try:
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info['resolution'] = f'{width}x{height}'
            except:
                pass
        
        return info
    
    @staticmethod
    def list_devices() -> list:
        """
        列出所有可用的USB摄像头设备
        
        Returns:
            list: 可用设备索引列表
        """
        devices = []
        for i in range(10):  # 检查前10个设备索引
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                devices.append(i)
                cap.release()
        return devices
