import apiClient from './client';

export const detectionAPI = {
  // 执行颜色检测
  detect: async (mode = null, useCamera = true) => {
    return apiClient.post('/api/detection/detect', {
      mode: mode,
      use_camera: useCamera,
    });
  },

  // HSV范围检测（用于参数调试）
  detectWithHSV: (hsvLower, hsvUpper, useCamera = true, imageData = null) =>
    apiClient.post('/api/detection/detect-hsv', {
      hsv_lower: hsvLower,
      hsv_upper: hsvUpper,
      use_camera: useCamera,
      image: imageData,
    }),

  // 获取像素HSV值
  getPixelHSV: (x, y, useCamera = true) => {
    const params = new URLSearchParams({ x: x.toString(), y: y.toString(), use_camera: useCamera });
    return apiClient.get(`/api/detection/pixel-hsv?${params}`);
  },
};
