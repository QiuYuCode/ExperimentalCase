# -- coding: utf-8 --

import sys
import os
import time
from pathlib import Path
from ctypes import *
import numpy as np
import cv2 as cv

# --- 1. 路径修复优化 ---
# 获取当前脚本的绝对路径 (D:\ExperimentalCase\common)
current_dir = Path(__file__).resolve().parent
# 拼接 SDK 目录
dll_path = current_dir / "MvImport"

# 检查路径是否存在
if not dll_path.exists():
    print(f"Error: SDK路径不存在 -> {dll_path}")
else:
    sys.path.append(str(dll_path))

try:
    from MvCameraControl_class import *
except ImportError:
    print("错误：无法导入 MvCameraControl_class，请检查 MvImport 文件夹位置。")
    sys.exit()

class Camera:
    def __init__(self):
        """
        初始化时自动连接第一台相机并开始取流
        """
        self.cam = MvCamera()
        self.nPayloadSize = 0
        self.buf_cache = None # 用于缓存数据 buffer
        self.is_open = False  # 标记相机是否正常打开

        print("正在初始化相机...")
        self._connect_and_start()

    def _connect_and_start(self):
        """内部方法：执行连接、打开、配置、开始取流"""
        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        # 1. 枚举设备
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        if ret != 0:
            print(f"枚举设备失败! ret[0x{ret:x}]")
            return

        if deviceList.nDeviceNum == 0:
            print("未发现任何相机设备！")
            return

        print(f"发现 {deviceList.nDeviceNum} 个设备，默认连接第 [0] 个...")

        # 2. 创建句柄 (自动选择索引 0)
        stDeviceList = cast(deviceList.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents
        ret = self.cam.MV_CC_CreateHandle(stDeviceList)
        if ret != 0:
            print(f"创建句柄失败! ret[0x{ret:x}]")
            return

        # 3. 打开设备
        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print(f"打开设备失败! ret[0x{ret:x}]")
            return
        
        # 4. (GigE相机) 网络包大小探测
        if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
            nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)

        # 5. 关闭触发模式 (设置为连续采集)
        self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)

        # 6. 获取 PayloadSize
        stParam = MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
        ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
        if ret != 0:
            print(f"获取 PayloadSize 失败! ret[0x{ret:x}]")
            return
        self.nPayloadSize = stParam.nCurValue

        # 7. 开始取流
        ret = self.cam.MV_CC_StartGrabbing()
        if ret != 0:
            print(f"开始取流失败! ret[0x{ret:x}]")
            return

        self.is_open = True
        print("相机初始化成功，正在连续取流中...")

    # --- 图像转换辅助函数 (修复了参数 self 问题) ---
    def Mono_numpy(self, data, nWidth, nHeight):
        data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
        data_mono_arr = data_.reshape(nHeight, nWidth)
        numArray = np.zeros([nHeight, nWidth, 1], "uint8")
        numArray[:, :, 0] = data_mono_arr
        return numArray

    def Color_numpy(self, data, nWidth, nHeight):
        data_ = np.frombuffer(data, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
        data_r = data_[0:nWidth * nHeight * 3:3]
        data_g = data_[1:nWidth * nHeight * 3:3]
        data_b = data_[2:nWidth * nHeight * 3:3]
        
        data_r_arr = data_r.reshape(nHeight, nWidth)
        data_g_arr = data_g.reshape(nHeight, nWidth)
        data_b_arr = data_b.reshape(nHeight, nWidth)
        
        numArray = np.zeros([nHeight, nWidth, 3], "uint8")
        numArray[:, :, 2] = data_r_arr
        numArray[:, :, 1] = data_g_arr
        numArray[:, :, 0] = data_b_arr
        return numArray

    def Is_mono_data(self, enGvspPixelType):
        return enGvspPixelType in [
            PixelType_Gvsp_Mono8, PixelType_Gvsp_Mono10, PixelType_Gvsp_Mono10_Packed,
            PixelType_Gvsp_Mono12, PixelType_Gvsp_Mono12_Packed
        ]

    def Is_color_data(self, enGvspPixelType):
        # 简化判断逻辑，包含常见的彩色格式
        return not self.Is_mono_data(enGvspPixelType)

    # --- 核心取图方法 ---
    def getCameraData(self):
        """
        获取一帧图像。
        注意：现在这个函数非常快，因为它不需要重新连接相机。
        """
        if not self.is_open:
            print("错误：相机未连接，无法获取图像")
            return None

        pData = (c_ubyte * self.nPayloadSize)()
        stFrameInfo = MV_FRAME_OUT_INFO_EX()
        memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
        
        # 超时时间设为 1000ms
        ret = self.cam.MV_CC_GetOneFrameTimeout(byref(pData), self.nPayloadSize, stFrameInfo, 1000)
        
        if ret == 0:
            # 取图成功，转换格式
            #print(f"Get One Frame: Width[{stFrameInfo.nWidth}], Height[{stFrameInfo.nHeight}], Type[0x{stFrameInfo.enPixelType:x}]")
            return self._convert_image(pData, stFrameInfo)
        else:
            print(f"获取图像超时或失败! ret[0x{ret:x}]")
            return None

    def _convert_image(self, pData, stFrameInfo):
        """内部转换逻辑，修复了内存拷贝和 self 参数传递 BUG"""
        
        # 1. 如果是 Mono8，直接转换
        if PixelType_Gvsp_Mono8 == stFrameInfo.enPixelType:
            return self.Mono_numpy(pData, stFrameInfo.nWidth, stFrameInfo.nHeight)
        
        # 2. 如果是 RGB8 Packed，直接转换
        elif PixelType_Gvsp_RGB8_Packed == stFrameInfo.enPixelType:
            return self.Color_numpy(pData, stFrameInfo.nWidth, stFrameInfo.nHeight)

        # 3. 其他格式 (需要 SDK 内部 ConvertPixelType)
        nConvertSize = stFrameInfo.nWidth * stFrameInfo.nHeight * 3
        if self.buf_cache is None: # 避免每次都分配内存
            self.buf_cache = (c_ubyte * nConvertSize)()

        stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
        memset(byref(stConvertParam), 0, sizeof(stConvertParam))
        stConvertParam.nWidth = stFrameInfo.nWidth
        stConvertParam.nHeight = stFrameInfo.nHeight
        stConvertParam.pSrcData = pData
        stConvertParam.nSrcDataLen = stFrameInfo.nFrameLen
        stConvertParam.enSrcPixelType = stFrameInfo.enPixelType
        
        # 判断目标格式
        if self.Is_mono_data(stFrameInfo.enPixelType):
            stConvertParam.enDstPixelType = PixelType_Gvsp_Mono8
            stConvertParam.pDstBuffer = self.buf_cache
            stConvertParam.nDstBufferSize = nConvertSize # Mono 其实不需要这么大，但用这个安全
            self.cam.MV_CC_ConvertPixelType(stConvertParam)
            return self.Mono_numpy(self.buf_cache, stFrameInfo.nWidth, stFrameInfo.nHeight)
        else:
            # 默认转为 RGB8
            stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed
            stConvertParam.pDstBuffer = self.buf_cache
            stConvertParam.nDstBufferSize = nConvertSize
            ret = self.cam.MV_CC_ConvertPixelType(stConvertParam)
            if ret != 0:
                print("像素格式转换失败！")
                return None
            return self.Color_numpy(self.buf_cache, stFrameInfo.nWidth, stFrameInfo.nHeight)

    def CloseCamera(self):
        """主动关闭相机资源"""
        if self.is_open:
            self.cam.MV_CC_StopGrabbing()
            self.cam.MV_CC_CloseDevice()
            self.cam.MV_CC_DestroyHandle()
            self.is_open = False
            print("相机已关闭")

    def __del__(self):
        """对象销毁时确保关闭"""
        self.CloseCamera()