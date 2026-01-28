# -- coding: utf-8 --

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import numpy as np

try:
    from ..config import ConfigManager
except ImportError:
    from backend.config import ConfigManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])

# 全局配置管理器
_config_manager: ConfigManager = None


def set_config_manager(manager: ConfigManager):
    """设置配置管理器实例"""
    global _config_manager
    _config_manager = manager


def _to_jsonable(obj: Any) -> Any:
    """
    将配置对象转换为可 JSON 序列化的结构，且不污染内部状态。
    - numpy.ndarray -> list
    - tuple -> list
    - dict/list -> 递归处理
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, tuple):
        return list(obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    return obj


@router.get("")
async def get_config() -> Dict[str, Any]:
    """获取配置"""
    if _config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")

    return _to_jsonable(_config_manager.config)


@router.post("")
async def update_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """更新配置"""
    if _config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")
    
    try:
        _config_manager.save_config(config)
        return {'success': True}
    except Exception as e:
        logger.error(f"更新配置异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/color/{color_name}")
async def update_color(color_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """更新颜色配置"""
    if _config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")
    
    try:
        _config_manager.update_color(color_name, params)
        return {'success': True}
    except Exception as e:
        logger.error(f"更新颜色配置异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system")
async def update_system(system_config: Dict[str, Any]) -> Dict[str, Any]:
    """更新系统配置"""
    if _config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")
    
    try:
        _config_manager.update_system(system_config)
        return {'success': True}
    except Exception as e:
        logger.error(f"更新系统配置异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calibration")
async def update_calibration(request: Dict[str, Any]) -> Dict[str, Any]:
    pixels_per_mm = request.get('pixels_per_mm')
    if pixels_per_mm is None:
        raise HTTPException(status_code=400, detail="缺少pixels_per_mm参数")
    """更新标定系数"""
    if _config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")
    
    try:
        _config_manager.update_system({'pixels_per_mm': pixels_per_mm})
        return {'success': True}
    except Exception as e:
        logger.error(f"更新标定系数异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))
