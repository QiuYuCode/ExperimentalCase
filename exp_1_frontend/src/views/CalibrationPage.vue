<template>
  <div class="calibration-page">
    <div class="page-header">
      <h2>尺寸标定</h2>
      <button class="capture-btn" @click="captureFrame" :disabled="!cameraStore.connected">
        📸 重新抓拍图像
      </button>
    </div>

    <div class="content-area">
      <div class="image-section">
        <div class="image-container" @click="handleImageClick" ref="imageContainer">
          <img v-if="currentImage" :src="currentImage" alt="标定图像" class="calibration-image" />
          <div v-else class="placeholder">点击"重新抓拍图像"获取当前画面</div>
          
          <!-- 绘制标定点 -->
          <svg v-if="currentImage" class="overlay-svg">
            <circle
              v-if="point1"
              :cx="point1.x"
              :cy="point1.y"
              r="8"
              fill="#10b981"
              stroke="#fff"
              stroke-width="2"
            />
            <circle
              v-if="point2"
              :cx="point2.x"
              :cy="point2.y"
              r="8"
              fill="#10b981"
              stroke="#fff"
              stroke-width="2"
            />
            <line
              v-if="point1 && point2"
              :x1="point1.x"
              :y1="point1.y"
              :x2="point2.x"
              :y2="point2.y"
              stroke="#10b981"
              stroke-width="2"
              stroke-dasharray="5,5"
            />
          </svg>
        </div>
      </div>

      <div class="controls-section">
        <div class="info-panel">
          <h3>标定说明</h3>
          <ol>
            <li>放置已知尺寸的标定物体（如标尺）</li>
            <li>点击"重新抓拍图像"获取当前画面</li>
            <li>在图像上点击标定物体的两个端点</li>
            <li>输入实际距离（毫米）</li>
            <li>点击"计算标定系数"完成标定</li>
          </ol>
        </div>

        <div class="calibration-panel">
          <h3>标定参数</h3>
          
          <div class="info-item" v-if="point1 && point2">
            <label>像素距离:</label>
            <span>{{ pixelDistance.toFixed(2) }} px</span>
          </div>

          <div class="input-group">
            <label>实际距离 (mm):</label>
            <input
              type="number"
              v-model.number="realDistance"
              placeholder="输入实际距离"
              step="0.1"
              min="0"
            />
          </div>

          <div class="info-item" v-if="calibrationFactor > 0">
            <label>标定系数:</label>
            <span>{{ calibrationFactor.toFixed(2) }} px/mm</span>
          </div>

          <button
            class="calculate-btn"
            @click="calculateCalibration"
            :disabled="!point1 || !point2 || !realDistance || realDistance <= 0"
          >
            📐 计算标定系数
          </button>

          <button
            class="save-btn"
            @click="saveCalibration"
            :disabled="calibrationFactor <= 0"
          >
            💾 保存标定结果
          </button>

          <button class="reset-btn" @click="resetPoints">
            🔄 重置标定点
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useCameraStore } from '../stores/camera';
import { useConfigStore } from '../stores/config';
import { cameraAPI } from '../api/camera';
import { configAPI } from '../api/config';

const cameraStore = useCameraStore();
const configStore = useConfigStore();

const currentImage = ref(null);
const imageContainer = ref(null);
const point1 = ref(null);
const point2 = ref(null);
const realDistance = ref(0);

const pixelDistance = computed(() => {
  if (!point1 || !point2) return 0;
  const dx = point2.value.x - point1.value.x;
  const dy = point2.value.y - point1.value.y;
  return Math.sqrt(dx * dx + dy * dy);
});

const calibrationFactor = computed(() => {
  if (!realDistance.value || realDistance.value <= 0) return 0;
  return pixelDistance.value / realDistance.value;
});

onMounted(async () => {
  await configStore.loadConfig();
  if (configStore.config.system?.pixels_per_mm) {
    realDistance.value = 100; // 默认值，用于显示当前系数
  }
});

const captureFrame = async () => {
  try {
    const result = await cameraAPI.getFrame();
    if (result.success && result.image) {
      currentImage.value = result.image;
      resetPoints();
    }
  } catch (error) {
    console.error('抓拍图像失败:', error);
  }
};

const handleImageClick = (event) => {
  if (!currentImage.value || !imageContainer.value) return;

  const rect = imageContainer.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  if (!point1.value) {
    point1.value = { x, y };
  } else if (!point2.value) {
    point2.value = { x, y };
  } else {
    // 重新开始
    point1.value = { x, y };
    point2.value = null;
  }
};

const calculateCalibration = () => {
  if (calibrationFactor.value > 0) {
    alert(`标定系数: ${calibrationFactor.value.toFixed(2)} px/mm`);
  }
};

const saveCalibration = async () => {
  if (calibrationFactor.value <= 0) return;

  try {
    await configStore.updateCalibration(calibrationFactor.value);
    alert(`标定系数已保存: ${calibrationFactor.value.toFixed(2)} px/mm`);
  } catch (error) {
    console.error('保存标定失败:', error);
    alert('保存失败: ' + error.message);
  }
};

const resetPoints = () => {
  point1.value = null;
  point2.value = null;
  realDistance.value = 0;
};
</script>

<style scoped>
.calibration-page {
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

.capture-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.capture-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
}

.capture-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.content-area {
  flex: 1;
  display: flex;
  gap: 2rem;
}

.image-section {
  flex: 2;
}

.image-container {
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  cursor: crosshair;
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.calibration-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.overlay-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.placeholder {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.25rem;
}

.controls-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-panel,
.calibration-panel {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
}

.info-panel h3,
.calibration-panel h3 {
  margin-bottom: 1rem;
  color: rgba(255, 255, 255, 0.9);
}

.info-panel ol {
  margin-left: 1.5rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.8;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.info-item label {
  font-weight: 500;
}

.info-item span {
  color: #10b981;
  font-weight: 600;
}

.input-group {
  margin: 1rem 0;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.7);
}

.input-group input {
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 1rem;
}

.input-group input:focus {
  outline: none;
  border-color: #667eea;
}

.calculate-btn,
.save-btn,
.reset-btn {
  width: 100%;
  padding: 0.75rem;
  margin-top: 1rem;
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.calculate-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.save-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.reset-btn {
  background: rgba(255, 255, 255, 0.1);
}

.calculate-btn:hover:not(:disabled),
.save-btn:hover:not(:disabled),
.reset-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

.calculate-btn:disabled,
.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
