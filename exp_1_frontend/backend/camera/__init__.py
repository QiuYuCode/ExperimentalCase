# -- coding: utf-8 --

try:
    from .base import CameraBase
    from .hikvision import HikvisionCamera
    from .usb import USBCamera
    from .ip import IPCamera
except ImportError:
    from camera.base import CameraBase
    from camera.hikvision import HikvisionCamera
    from camera.usb import USBCamera
    from camera.ip import IPCamera

__all__ = ['CameraBase', 'HikvisionCamera', 'USBCamera', 'IPCamera']
