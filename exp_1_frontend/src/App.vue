<template>
  <div class="app-container">
    <Sidebar @navigate="handleNavigate" />
    <main class="main-content">
      <DetectionPage v-if="currentPage === 'detection'" />
      <TuningPage v-if="currentPage === 'tuning'" />
      <CalibrationPage v-if="currentPage === 'calibration'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Sidebar from './components/Sidebar.vue';
import DetectionPage from './views/DetectionPage.vue';
import TuningPage from './views/TuningPage.vue';
import CalibrationPage from './views/CalibrationPage.vue';

const currentPage = ref('detection');

const handleNavigate = (page) => {
  currentPage.value = page;
};
</script>

<style scoped>
.app-container {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow: auto;
  background: #0f1629;
}
</style>
