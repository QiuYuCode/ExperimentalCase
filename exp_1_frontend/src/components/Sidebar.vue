<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1 class="logo">VISION</h1>
      <p class="subtitle">工业视觉系统</p>
    </div>
    <nav class="nav-menu">
      <button
        v-for="item in menuItems"
        :key="item.id"
        :class="['nav-item', { active: currentPage === item.id }]"
        @click="handleNavigate(item.id)"
      >
        <span class="icon">{{ item.icon }}</span>
        <span class="label">{{ item.label }}</span>
      </button>
    </nav>
    <div class="sidebar-footer">
      <div class="camera-status" :class="{ connected: cameraStore.connected }">
        <span class="status-dot"></span>
        <span>{{ cameraStore.connected ? '相机已连接' : '相机未连接' }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useCameraStore } from '../stores/camera';

const emit = defineEmits(['navigate']);

const cameraStore = useCameraStore();
const currentPage = ref('detection');

const handleNavigate = (page) => {
  currentPage.value = page;
  emit('navigate', page);
};

const menuItems = [
  { id: 'detection', icon: '🔍', label: '智能识别' },
  { id: 'tuning', icon: '⚙️', label: '参数调试' },
  { id: 'calibration', icon: '📏', label: '尺寸标定' },
];

onMounted(() => {
  cameraStore.checkStatus();
});
</script>

<style scoped>
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1a1f3a 0%, #0f1629 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  padding: 2rem 0;
}

.sidebar-header {
  padding: 0 2rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 2rem;
}

.logo {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
}

.nav-menu {
  flex: 1;
  padding: 0 1rem;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  margin-bottom: 0.5rem;
  background: transparent;
  border: none;
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
  transform: translateX(4px);
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  color: #fff;
  border-left: 3px solid #667eea;
}

.icon {
  font-size: 1.25rem;
}

.sidebar-footer {
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.camera-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  transition: background 0.3s;
}

.camera-status.connected .status-dot {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}
</style>
