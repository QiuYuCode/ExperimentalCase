import { defineStore } from 'pinia';
import { configAPI } from '../api/config';

export const useConfigStore = defineStore('config', {
  state: () => ({
    config: {
      system: {
        save_root: './saved_images',
        pixels_per_mm: 12.1,
      },
      colors: {},
    },
    loading: false,
  }),

  actions: {
    async loadConfig() {
      this.loading = true;
      try {
        const config = await configAPI.getConfig();
        this.config = config;
      } catch (error) {
        console.error('加载配置失败:', error);
      } finally {
        this.loading = false;
      }
    },

    async updateColor(colorName, params) {
      try {
        await configAPI.updateColor(colorName, params);
        await this.loadConfig(); // 重新加载配置
      } catch (error) {
        console.error('更新颜色配置失败:', error);
        throw error;
      }
    },

    async updateSystem(systemConfig) {
      try {
        await configAPI.updateSystem(systemConfig);
        await this.loadConfig(); // 重新加载配置
      } catch (error) {
        console.error('更新系统配置失败:', error);
        throw error;
      }
    },

    async updateCalibration(pixelsPerMm) {
      try {
        await configAPI.updateCalibration(pixelsPerMm);
        await this.loadConfig(); // 重新加载配置
      } catch (error) {
        console.error('更新标定系数失败:', error);
        throw error;
      }
    },
  },
});
