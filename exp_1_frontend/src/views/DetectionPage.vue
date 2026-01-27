<template>
  <div class="detection-page">
    <div class="page-header">
      <h2>智能识别</h2>
      <div class="controls">
        <button
          v-for="color in availableColors"
          :key="color"
          class="detect-btn"
          @click="handleDetect(color)"
          :disabled="detectionStore.detecting || !cameraStore.connected"
        >
          检测 {{ color.toUpperCase() }}
        </button>
        <button
          class="detect-btn auto"
          @click="handleDetect(null)"
          :disabled="detectionStore.detecting || !cameraStore.connected"
        >
          🔍 自动识别
        </button>
      </div>
    </div>

    <div class="content-area">
      <div class="image-container">
        <img
          v-if="currentImage"
          :src="currentImage"
          alt="相机图像"
          class="camera-image"
        />
        <div v-else class="placeholder">
          <p>{{ cameraStore.connected ? '等待图像...' : '相机未连接' }}</p>
        </div>
      </div>

      <div class="result-panel" v-if="detectionStore.lastResult">
        <h3>检测结果</h3>
        <div v-if="detectionStore.lastResult.detected" class="result-success">
          <p><strong>颜色:</strong> {{ detectionStore.lastResult.color_name?.toUpperCase() }}</p>
          <p v-if="detectionStore.lastResult.center">
            <strong>中心坐标:</strong> ({{ detectionStore.lastResult.center[0] }},
            {{ detectionStore.lastResult.center[1] }})
          </p>
          <p v-if="detectionStore.lastResult.size_mm">
            <strong>尺寸:</strong> {{ detectionStore.lastResult.size_mm[0].toFixed(1) }}mm ×
            {{ detectionStore.lastResult.size_mm[1].toFixed(1) }}mm
          </p>
          <img
            v-if="detectionStore.lastResult.annotated_image"
            :src="detectionStore.lastResult.annotated_image"
            alt="检测结果"
            class="result-image"
          />
        </div>
        <div v-else class="result-fail">
          <p>未检测到目标</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useCameraStore } from '../stores/camera';
import { useDetectionStore } from '../stores/detection';
import { useConfigStore } from '../stores/config';

const cameraStore = useCameraStore();
const detectionStore = useDetectionStore();
const configStore = useConfigStore();

const currentImage = ref(null);
const availableColors = ref([]);

let streamInterval = null;

onMounted(async () => {
  await configStore.loadConfig();
  availableColors.value = Object.keys(configStore.config.colors || {});
  
  if (cameraStore.connected) {
    startStream();
  }
  
  // 监听相机连接状态变化
  const checkConnection = setInterval(async () => {
    const status = await cameraStore.checkStatus();
    if (status.connected && !streamInterval) {
      startStream();
    } else if (!status.connected && streamInterval) {
      stopStream();
    }
  }, 2000);
  
  onUnmounted(() => {
    clearInterval(checkConnection);
    stopStream();
  });
});

onUnmounted(() => {
  stopStream();
});

const startStream = () => {
  if (streamInterval) return;
  
  cameraStore.openStream((data) => {
    if (data.image) {
      currentImage.value = data.image;
    }
  });
  
  // 备用方案：轮询获取图像（如果WebSocket不可用）
  // streamInterval = setInterval(async () => {
  //   try {
  //     const result = await cameraAPI.getFrame();
  //     if (result?.success && result.image) {
  //       currentImage.value = result.image;
  //     }
  //   } catch (error) {
  //     console.error('获取图像失败:', error);
  //   }
  // }, 100);
};

const stopStream = () => {
  cameraStore.closeStream();
  if (streamInterval) {
    clearInterval(streamInterval);
    streamInterval = null;
  }
};

const handleDetect = async (mode) => {
  try {
    await detectionStore.detect(mode);
    // 如果检测成功，更新显示的图像
    if (detectionStore.lastResult?.annotated_image) {
      currentImage.value = detectionStore.lastResult.annotated_image;
    }
  } catch (error) {
    console.error('检测失败:', error);
  }
};
</script>

<style scoped>
.detection-page {
  padding: 2rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h2 {
  font-size: 1.75rem;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.controls {
  display: flex;
  gap: 1rem;
}

.detect-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.detect-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

.detect-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.detect-btn.auto {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.content-area {
  flex: 1;
  display: flex;
  gap: 2rem;
}

.image-container {
  flex: 2;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 500px;
}

.camera-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.placeholder {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.25rem;
}

.result-panel {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
}

.result-panel h3 {
  margin-bottom: 1rem;
  color: rgba(255, 255, 255, 0.9);
}

.result-success p {
  margin-bottom: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
}

.result-image {
  width: 100%;
  margin-top: 1rem;
  border-radius: 8px;
}

.result-fail {
  color: rgba(255, 255, 255, 0.6);
}
</style>
