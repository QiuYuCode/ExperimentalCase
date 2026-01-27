import { defineStore } from 'pinia';
import { cameraAPI } from '../api/camera';

export const useCameraStore = defineStore('camera', {
  state: () => ({
    connected: false,
    cameraType: null,
    cameraInfo: null,
    availableCameras: [],
    streamSocket: null,
  }),

  actions: {
    async fetchAvailableCameras() {
      try {
        const result = await cameraAPI.listCameras();
        this.availableCameras = result.cameras || [];
      } catch (error) {
        console.error('获取相机列表失败:', error);
        this.availableCameras = [];
      }
    },

    async connect(cameraType, config = {}) {
      try {
        const result = await cameraAPI.connectCamera(cameraType, config);
        if (result.success) {
          this.connected = true;
          this.cameraType = cameraType;
          this.cameraInfo = result.info;
          return true;
        }
        return false;
      } catch (error) {
        console.error('连接相机失败:', error);
        return false;
      }
    },

    async disconnect() {
      try {
        await cameraAPI.disconnectCamera();
        this.connected = false;
        this.cameraType = null;
        this.cameraInfo = null;
        this.closeStream();
      } catch (error) {
        console.error('断开相机失败:', error);
      }
    },

    async checkStatus() {
      try {
        const status = await cameraAPI.getCameraStatus();
        this.connected = status.connected;
        this.cameraInfo = status.info;
        return status;
      } catch (error) {
        console.error('获取相机状态失败:', error);
        this.connected = false;
        return { connected: false };
      }
    },

    openStream(onMessage) {
      if (this.streamSocket) {
        this.closeStream();
      }

      const ws = cameraAPI.createStream();
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (onMessage) {
          onMessage(data);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
      };

      ws.onclose = () => {
        this.streamSocket = null;
      };

      this.streamSocket = ws;
    },

    closeStream() {
      if (this.streamSocket) {
        this.streamSocket.close();
        this.streamSocket = null;
      }
    },
  },
});
