<template>
  <div class="tuning-page">
    <div class="page-header">
      <h2>参数调试</h2>
      <button class="capture-btn" @click="captureFrame" :disabled="!cameraStore.connected">
        📸 重新抓拍图像
      </button>
    </div>

    <div class="content-area">
      <div class="image-section">
        <div class="image-container" @click="handleImageClick" ref="imageContainer">
          <img v-if="currentImage" :src="currentImage" alt="原始图像" class="tuning-image" />
          <img
            v-if="previewImage"
            :src="previewImage"
            alt="处理预览"
            class="preview-overlay"
          />
          <div v-else class="placeholder">点击"重新抓拍图像"获取当前画面</div>
        </div>
        <div v-if="pixelHSV" class="pixel-info">
          <p>点击位置 HSV: [{{ pixelHSV[0] }}, {{ pixelHSV[1] }}, {{ pixelHSV[2] }}]</p>
        </div>
      </div>

      <div class="controls-section">
        <div class="control-group">
          <h3>HSV 参数调节</h3>
          
          <div class="slider-item">
            <label>H Min (颜色起点)</label>
            <input
              type="range"
              v-model.number="hsvLower[0]"
              min="0"
              max="180"
              @input="updatePreview"
            />
            <span>{{ hsvLower[0] }}</span>
          </div>

          <div class="slider-item">
            <label>H Max (颜色终点)</label>
            <input
              type="range"
              v-model.number="hsvUpper[0]"
              min="0"
              max="180"
              @input="updatePreview"
            />
            <span>{{ hsvUpper[0] }}</span>
          </div>

          <div class="slider-item">
            <label>S Min (去白/去灰)</label>
            <input
              type="range"
              v-model.number="hsvLower[1]"
              min="0"
              max="255"
              @input="updatePreview"
            />
            <span>{{ hsvLower[1] }}</span>
          </div>

          <div class="slider-item">
            <label>S Max (饱和度上限)</label>
            <input
              type="range"
              v-model.number="hsvUpper[1]"
              min="0"
              max="255"
              @input="updatePreview"
            />
            <span>{{ hsvUpper[1] }}</span>
          </div>

          <div class="slider-item">
            <label>V Min (去黑/去影)</label>
            <input
              type="range"
              v-model.number="hsvLower[2]"
              min="0"
              max="255"
              @input="updatePreview"
            />
            <span>{{ hsvLower[2] }}</span>
          </div>

          <div class="slider-item">
            <label>V Max (亮度上限)</label>
            <input
              type="range"
              v-model.number="hsvUpper[2]"
              min="0"
              max="255"
              @input="updatePreview"
            />
            <span>{{ hsvUpper[2] }}</span>
          </div>
        </div>

        <div class="control-group">
          <h3>保存参数</h3>
          <select v-model="selectedColor" class="color-select">
            <option value="">选择颜色...</option>
            <option v-for="color in availableColors" :key="color" :value="color">
              {{ color.toUpperCase() }}
            </option>
            <option value="__new__">➕ 添加新颜色</option>
          </select>
          <button class="save-btn" @click="saveParams" :disabled="!selectedColor">
            💾 保存参数
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useCameraStore } from '../stores/camera';
import { useDetectionStore } from '../stores/detection';
import { useConfigStore } from '../stores/config';
import { cameraAPI } from '../api/camera';
import { detectionAPI } from '../api/detection';

const cameraStore = useCameraStore();
const detectionStore = useDetectionStore();
const configStore = useConfigStore();

const currentImage = ref(null);
const previewImage = ref(null);
const pixelHSV = ref(null);
const imageContainer = ref(null);

const hsvLower = ref([0, 0, 0]);
const hsvUpper = ref([180, 255, 255]);
const selectedColor = ref('');
const availableColors = ref([]);

onMounted(async () => {
  await configStore.loadConfig();
  availableColors.value = Object.keys(configStore.config.colors || {});
});

watch([hsvLower, hsvUpper], () => {
  updatePreview();
}, { deep: true });

const captureFrame = async () => {
  try {
    const result = await cameraAPI.getFrame();
    if (result.success && result.image) {
      currentImage.value = result.image;
      updatePreview();
    }
  } catch (error) {
    console.error('抓拍图像失败:', error);
  }
};

const updatePreview = async () => {
  if (!currentImage.value) return;

  try {
    // 提取Base64数据部分
    const imageData = currentImage.value.includes(',') 
      ? currentImage.value.split(',')[1] 
      : currentImage.value;
    
    const result = await detectionAPI.detectWithHSV(
      hsvLower.value,
      hsvUpper.value,
      false, // 不使用相机
      imageData // 传递图像数据
    );
    if (result.success && result.preview) {
      previewImage.value = result.preview;
    }
  } catch (error) {
    console.error('更新预览失败:', error);
  }
};

const handleImageClick = async (event) => {
  if (!currentImage.value || !imageContainer.value) return;

  const img = new Image();
  img.src = currentImage.value;
  await new Promise((resolve) => {
    img.onload = resolve;
  });

  const rect = imageContainer.value.getBoundingClientRect();
  const scaleX = img.width / rect.width;
  const scaleY = img.height / rect.height;
  const x = Math.floor((event.clientX - rect.left) * scaleX);
  const y = Math.floor((event.clientY - rect.top) * scaleY);

  try {
    // 需要先抓拍当前图像，然后获取像素HSV
    // 这里简化处理，直接使用当前图像
    const result = await detectionAPI.getPixelHSV(x, y, true);
    if (result.success && result.hsv) {
      pixelHSV.value = result.hsv;
      // 自动设置HSV范围（±20）
      hsvLower.value = [
        Math.max(0, result.hsv[0] - 20),
        Math.max(0, result.hsv[1] - 20),
        Math.max(0, result.hsv[2] - 20),
      ];
      hsvUpper.value = [
        Math.min(180, result.hsv[0] + 20),
        Math.min(255, result.hsv[1] + 20),
        Math.min(255, result.hsv[2] + 20),
      ];
    }
  } catch (error) {
    console.error('获取像素HSV失败:', error);
  }
};

const saveParams = async () => {
  if (!selectedColor.value) return;

  let colorName = selectedColor.value;
  if (colorName === '__new__') {
    colorName = prompt('请输入新颜色名称:');
    if (!colorName) return;
  }

  try {
    const params = {
      lower: hsvLower.value,
      upper: hsvUpper.value,
      save_folder: `${colorName}_results`,
      draw_color: [0, 255, 0], // 默认绿色
    };

    await configStore.updateColor(colorName, params);
    alert('参数保存成功！');
    
    // 更新颜色列表
    await configStore.loadConfig();
    availableColors.value = Object.keys(configStore.config.colors || {});
    selectedColor.value = '';
  } catch (error) {
    console.error('保存参数失败:', error);
    alert('保存失败: ' + error.message);
  }
};
</script>

<style scoped>
.tuning-page {
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
  display: flex;
  flex-direction: column;
}

.image-container {
  flex: 1;
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

.tuning-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  opacity: 0.7;
  pointer-events: none;
}

.placeholder {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.25rem;
}

.pixel-info {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
}

.controls-section {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
  overflow-y: auto;
}

.control-group {
  margin-bottom: 2rem;
}

.control-group h3 {
  margin-bottom: 1rem;
  color: rgba(255, 255, 255, 0.9);
}

.slider-item {
  margin-bottom: 1.5rem;
}

.slider-item label {
  display: block;
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.875rem;
}

.slider-item input[type="range"] {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.1);
  outline: none;
  -webkit-appearance: none;
}

.slider-item input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
}

.slider-item span {
  display: inline-block;
  margin-left: 1rem;
  color: #667eea;
  font-weight: 600;
  min-width: 40px;
}

.color-select {
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  margin-bottom: 1rem;
}

.save-btn {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
