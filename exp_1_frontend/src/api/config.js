import apiClient from './client';

export const configAPI = {
  // 获取配置
  getConfig: () => apiClient.get('/api/config'),

  // 更新配置
  updateConfig: (config) => apiClient.post('/api/config', config),

  // 更新颜色配置
  updateColor: (colorName, params) =>
    apiClient.post(`/api/config/color/${colorName}`, params),

  // 更新系统配置
  updateSystem: (systemConfig) =>
    apiClient.post('/api/config/system', systemConfig),

  // 更新标定系数
  updateCalibration: (pixelsPerMm) => {
    return apiClient.post('/api/config/calibration', {
      pixels_per_mm: pixelsPerMm,
    });
  },
};
