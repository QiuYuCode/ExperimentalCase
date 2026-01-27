import apiClient from './client';

export const cameraAPI = {
  // 列出所有可用相机
  listCameras: () => apiClient.get('/api/camera/list'),

  // 连接相机
  connectCamera: async (cameraType, config = {}) => {
    return apiClient.post('/api/camera/connect', {
      camera_type: cameraType,
      config: config,
    });
  },

  // 断开相机
  disconnectCamera: () => apiClient.post('/api/camera/disconnect'),

  // 获取相机状态
  getCameraStatus: () => apiClient.get('/api/camera/status'),

  // 获取单帧图像
  getFrame: () => apiClient.get('/api/camera/frame'),

  // 创建WebSocket图像流
  createStream: () => apiClient.createWebSocket('/ws/camera/stream'),
};
