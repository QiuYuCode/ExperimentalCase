# -- coding: utf-8 --

import yaml
import numpy as np
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Path):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = self.load_config(self.config_path)
    
    def load_config(self, path: Path) -> Dict[str, Any]:
        """
        加载YAML配置文件
        
        Args:
            path: 配置文件路径
            
        Returns:
            dict: 配置字典
        """
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        
        if cfg is None:
            cfg = {'colors': {}, 'system': {}}
        
        # 预处理 numpy 数组
        if 'colors' in cfg:
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
                    # 强制转换为 int tuple，防止颜色显示异常
                    params['draw_color'] = tuple(map(int, params['draw_color']))
        
        return cfg
    
    def save_config(self, config: Dict[str, Any] = None):
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置，如果为None则保存当前配置
        """
        if config is None:
            config = self.config
        
        # 转换numpy数组为列表以便YAML序列化
        config_to_save = self._prepare_for_yaml(config.copy())
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_to_save, f, allow_unicode=True, default_flow_style=False)
        
        # 重新加载以更新numpy数组
        self.config = self.load_config(self.config_path)
    
    def _prepare_for_yaml(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """准备配置以便YAML序列化（转换numpy数组为列表）"""
        if 'colors' in config:
            for color_name, params in config['colors'].items():
                for key in ['lower', 'upper', 'lower1', 'upper1', 'lower2', 'upper2']:
                    if key in params and isinstance(params[key], np.ndarray):
                        params[key] = params[key].tolist()
                if 'draw_color' in params and isinstance(params['draw_color'], tuple):
                    params['draw_color'] = list(params['draw_color'])
        return config
    
    def update_color(self, color_name: str, params: Dict[str, Any]):
        """
        更新颜色配置
        
        Args:
            color_name: 颜色名称
            params: 颜色参数
        """
        if 'colors' not in self.config:
            self.config['colors'] = {}
        
        # 转换列表为numpy数组
        if 'lower' in params:
            params['lower'] = np.array(params['lower'], dtype=np.uint8)
            params['upper'] = np.array(params['upper'], dtype=np.uint8)
        if 'lower1' in params:
            params['lower1'] = np.array(params['lower1'], dtype=np.uint8)
            params['upper1'] = np.array(params['upper1'], dtype=np.uint8)
            params['lower2'] = np.array(params['lower2'], dtype=np.uint8)
            params['upper2'] = np.array(params['upper2'], dtype=np.uint8)
        if 'draw_color' in params:
            params['draw_color'] = tuple(map(int, params['draw_color']))
        
        self.config['colors'][color_name] = params
        self.save_config()
    
    def update_system(self, system_config: Dict[str, Any]):
        """
        更新系统配置
        
        Args:
            system_config: 系统配置
        """
        if 'system' not in self.config:
            self.config['system'] = {}
        self.config['system'].update(system_config)
        self.save_config()
