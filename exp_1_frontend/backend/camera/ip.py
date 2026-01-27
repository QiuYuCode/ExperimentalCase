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


class IPCamera(CameraBase):
    """IP网络相机实现（支持RTSP/HTTP）"""
    
    def __init__(self, config: dict = None):
        """
        初始化IP相机
        
        Args:
            config: 配置字典，必须包含 'url' 键指定RTSP/HTTP URL
                    可选 'username' 和 'password' 用于认证
        """
        super().__init__(config)
        self.cap = None
        self.url = config.get('url', '') if config else ''
        self.username = config.get('username', '') if config else ''
        self.password = config.get('password', '') if config else ''
        
        if not self.url:
            raise ValueError("IP相机配置必须包含 'url' 参数")
    
    def _build_url(self) -> str:
        """构建带认证信息的URL"""
        if self.username and self.password:
            # 解析URL并插入认证信息
            if '://' in self.url:
                protocol, rest = self.url.split('://', 1)
                return f"{protocol}://{self.username}:{self.password}@{rest}"
        return self.url
    
    def connect(self) -> bool:
        """连接IP相机"""
        if not self.url:
            logger.error("IP相机URL未配置")
            self._connected = False
            return False
        
        try:
            full_url = self._build_url()
            self.cap = cv2.VideoCapture(full_url)
            
            # 设置缓冲区大小（减少延迟）
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.cap.isOpened():
                logger.error(f"无法打开IP相机: {self.url}")
                self._connected = False
                return False
            
            # 测试读取一帧（设置超时）
            self.cap.set(cv2.CAP_PROP_TIMEOUT, 5000)  # 5秒超时
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.error(f"IP相机无法读取图像: {self.url}")
                self.cap.release()
                self.cap = None
                self._connected = False
                return False
            
            self._connected = True
            logger.info(f"IP相机连接成功: {self.url}")
            return True
        except Exception as e:
            logger.error(f"IP相机连接异常: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开IP相机连接"""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                logger.error(f"关闭IP相机异常: {e}")
        self.cap = None
        self._connected = False
        logger.info(f"IP相机已断开: {self.url}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取一帧图像
        
        Returns:
            np.ndarray | None: BGR格式图像，失败返回None
        """
        if not self._connected or self.cap is None:
            logger.warning("IP相机未连接，无法获取图像")
            return None
        
        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.warning("读取IP相机图像失败")
                return None
            
            # 确保返回BGR格式
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            
            return frame
        except Exception as e:
            logger.error(f"获取IP相机图像异常: {e}")
            return None
    
    def get_info(self) -> dict:
        """获取IP相机信息"""
        info = {
            'type': 'ip',
            'name': f'IP Camera ({self.url})',
            'connected': self._connected,
            'url': self.url
        }
        
        if self.cap is not None:
            try:
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info['resolution'] = f'{width}x{height}'
            except:
                pass
        
        return info
