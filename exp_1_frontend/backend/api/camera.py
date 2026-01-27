# -- coding: utf-8 --

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
import logging
import asyncio
import base64
import cv2
import numpy as np

try:
    from ..camera import CameraBase, HikvisionCamera, USBCamera, IPCamera
except ImportError:
    from backend.camera import CameraBase, HikvisionCamera, USBCamera, IPCamera

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/camera", tags=["camera"])

# 全局相机实例
_current_camera: Optional[CameraBase] = None
_camera_type: Optional[str] = None
_camera_config: Optional[Dict[str, Any]] = None


@router.get("/list")
async def list_cameras() -> Dict[str, Any]:
    """列出所有可用的相机"""
    cameras = []
    
    # 1. 检查海康相机
    try:
        try:
            from ..camera import HikvisionCamera
        except ImportError:
            from backend.camera import HikvisionCamera
        # 尝试连接第一台海康相机
        hik_cam = HikvisionCamera({'device_index': 0})
        if hik_cam.connect():
            cameras.append({
                'type': 'hikvision',
                'id': 'hikvision_0',
                'name': 'Hikvision Camera #0',
                'info': hik_cam.get_info()
            })
            hik_cam.disconnect()
    except Exception as e:
        logger.debug(f"海康相机检查失败: {e}")
    
    # 2. 检查USB摄像头
    try:
        usb_devices = USBCamera.list_devices()
        for idx in usb_devices:
            cameras.append({
                'type': 'usb',
                'id': f'usb_{idx}',
                'name': f'USB Camera #{idx}',
                'info': {'device_index': idx}
            })
    except Exception as e:
        logger.debug(f"USB摄像头检查失败: {e}")
    
    return {'cameras': cameras}


@router.post("/connect")
async def connect_camera(request: Dict[str, Any]) -> Dict[str, Any]:
    camera_type = request.get('camera_type')
    if not camera_type:
        return {'success': False, 'error': '缺少camera_type参数'}
    config = request.get('config', {})
    """连接指定类型的相机"""
    global _current_camera, _camera_type, _camera_config
    
    # 断开现有连接
    if _current_camera is not None:
        try:
            _current_camera.disconnect()
        except:
            pass
    
    _camera_type = camera_type
    _camera_config = config if config else {}
    
    try:
        if camera_type == 'hikvision':
            _current_camera = HikvisionCamera(_camera_config)
        elif camera_type == 'usb':
            _current_camera = USBCamera(_camera_config)
        elif camera_type == 'ip':
            _current_camera = IPCamera(_camera_config)
        else:
            return {'success': False, 'error': f'未知的相机类型: {camera_type}'}
        
        if _current_camera.connect():
            return {
                'success': True,
                'info': _current_camera.get_info()
            }
        else:
            return {'success': False, 'error': '相机连接失败'}
    except Exception as e:
        logger.error(f"连接相机异常: {e}")
        return {'success': False, 'error': str(e)}


@router.post("/disconnect")
async def disconnect_camera() -> Dict[str, Any]:
    """断开相机连接"""
    global _current_camera
    
    if _current_camera is not None:
        try:
            _current_camera.disconnect()
        except Exception as e:
            logger.error(f"断开相机异常: {e}")
        _current_camera = None
    
    return {'success': True}


@router.get("/status")
async def get_camera_status() -> Dict[str, Any]:
    """获取相机状态"""
    global _current_camera
    
    if _current_camera is None:
        return {'connected': False}
    
    return {
        'connected': _current_camera.is_connected(),
        'info': _current_camera.get_info() if _current_camera.is_connected() else None
    }


@router.get("/frame")
async def get_frame() -> Dict[str, Any]:
    """获取单帧图像（Base64编码）"""
    global _current_camera
    
    if _current_camera is None or not _current_camera.is_connected():
        return {'success': False, 'error': '相机未连接'}
    
    try:
        frame = _current_camera.get_frame()
        if frame is None:
            return {'success': False, 'error': '获取图像失败'}
        
        # 编码为JPEG Base64
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'success': True,
            'image': f'data:image/jpeg;base64,{img_base64}',
            'width': int(frame.shape[1]),
            'height': int(frame.shape[0])
        }
    except Exception as e:
        logger.error(f"获取图像异常: {e}")
        return {'success': False, 'error': str(e)}


@router.websocket("/stream")
async def camera_stream(websocket: WebSocket):
    """WebSocket实时图像流"""
    global _current_camera
    
    await websocket.accept()
    
    if _current_camera is None or not _current_camera.is_connected():
        await websocket.send_json({'error': '相机未连接'})
        await websocket.close()
        return
    
    try:
        while True:
            frame = _current_camera.get_frame()
            if frame is None:
                await asyncio.sleep(0.1)
                continue
            
            # 编码为JPEG Base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            await websocket.send_json({
                'image': f'data:image/jpeg;base64,{img_base64}',
                'width': int(frame.shape[1]),
                'height': int(frame.shape[0])
            })
            
            # 控制帧率（约30fps）
            await asyncio.sleep(1/30)
    except WebSocketDisconnect:
        logger.info("WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket流异常: {e}")
        try:
            await websocket.send_json({'error': str(e)})
        except:
            pass
