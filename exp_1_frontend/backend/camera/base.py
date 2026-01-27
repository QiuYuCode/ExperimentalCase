# -- coding: utf-8 --

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class CameraBase(ABC):
    """相机抽象基类"""
    
    def __init__(self, config: dict = None):
        """
        初始化相机
        
        Args:
            config: 相机配置字典
        """
        self.config = config or {}
        self._connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接相机
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取一帧图像（BGR格式）
        
        Returns:
            np.ndarray | None: BGR格式的图像数组，失败返回None
        """
        pass
    
    def is_connected(self) -> bool:
        """
        检查连接状态
        
        Returns:
            bool: 是否已连接
        """
        return self._connected
    
    @abstractmethod
    def get_info(self) -> dict:
        """
        获取相机信息
        
        Returns:
            dict: 包含相机信息的字典，如 {'type': 'hikvision', 'name': '...', 'resolution': '...'}
        """
        pass
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
