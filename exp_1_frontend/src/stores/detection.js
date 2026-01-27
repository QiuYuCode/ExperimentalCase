import { defineStore } from 'pinia';
import { detectionAPI } from '../api/detection';

export const useDetectionStore = defineStore('detection', {
  state: () => ({
    detecting: false,
    lastResult: null,
  }),

  actions: {
    async detect(mode = null) {
      this.detecting = true;
      try {
        const result = await detectionAPI.detect(mode, true);
        this.lastResult = result;
        return result;
      } catch (error) {
        console.error('检测失败:', error);
        throw error;
      } finally {
        this.detecting = false;
      }
    },

    async detectWithHSV(hsvLower, hsvUpper) {
      try {
        const result = await detectionAPI.detectWithHSV(hsvLower, hsvUpper, true);
        return result;
      } catch (error) {
        console.error('HSV检测失败:', error);
        throw error;
      }
    },

    async getPixelHSV(x, y) {
      try {
        const result = await detectionAPI.getPixelHSV(x, y, true);
        return result;
      } catch (error) {
        console.error('获取像素HSV失败:', error);
        throw error;
      }
    },
  },
});
