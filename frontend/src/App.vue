<template>
  <div id="app" class="app-container">
    <header class="app-header glass-header">
      <div class="header-content">
        <div class="brand-container">
          <div>
            <img 
              src="./assets/nankai.png" 
              alt="Logo" 
              class="logo-img" />
          </div>
          <div class="brand-text">
            <h1 class="main-title">南开大学软件学院前端技术知识问答与推荐系统</h1>
            <span class="sub-title">Knowledge Graph RAG System of Nankai University Software College</span>
          </div>
        </div>
      </div>
    </header>
    
    <main class="main-layout">
      <aside class="layout-left glass-card">
        <QaPanel 
          @update:mainEntity="handleMainEntityChange" 
          :current-entity="currentEntity"
          style="width: 100%; height: 100%;"
        />
      </aside>
      
      <section class="layout-right glass-card">
        <div v-if="!graphLoaded" class="graph-loading-overlay">
          <div class="loading-content">
             <el-icon class="is-loading"><Loading /></el-icon>
             <span>知识网络构建中...</span>
          </div>
        </div>
        <GraphVisual 
          :main-entity="mainEntity" 
          @update:currentEntity="handleCurrentEntityChange"
          @graph-loaded="graphLoaded = true"
          @getRecommendData="fetchRecommendData"
          style="width: 100%; height: 100%;"
        />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Loading, Share } from '@element-plus/icons-vue'; // 引入 Share 图标作为Logo
// 引入组件
import QaPanel from './components/QaPanel.vue';
import GraphVisual from './components/GraphVisual.vue';

// --- 核心逻辑保持不变 ---
const mainEntity = ref(''); 
const currentEntity = ref(''); 
const graphLoaded = ref(false); 
const recommendData = ref([]);
const recommendLoading = ref(false);

const handleMainEntityChange = (entity) => {
  mainEntity.value = entity;
  if (!currentEntity.value) {
    currentEntity.value = entity;
    fetchRecommendData(entity);
  }
};

const handleCurrentEntityChange = (entity) => {
  currentEntity.value = entity;
};

const fetchRecommendData = async (entity) => {
  if (!entity) { recommendData.value = []; return; }
  recommendLoading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 800));
    // 模拟数据...
    const mockRecommendData = { '前端开发': [{ label: 'Vue3', desc: '渐进式框架' }] };
    recommendData.value = mockRecommendData[entity] || [];
  } catch (error) {
    console.error(error);
  } finally {
    recommendLoading.value = false;
  }
};
</script>

<style>
/* --- 全局变量 --- */
:root {
  --primary-color: #4F46E5; 
  --primary-hover: #4338CA;
  --bg-color: #F8FAFC; 
  --text-main: #0F172A; /* 更深的黑色 */
  --text-sub: #64748B;  
  --border-color: #CBD5E1;
  --card-radius: 16px;     
  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

body {
  margin: 0;
  background-color: var(--bg-color);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--text-main);
  height: 100vh;
  overflow: hidden; 
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  /* 移除原本的 padding，让 header 顶满最上方 */
  padding: 0; 
  box-sizing: border-box;
}

.logo-img {
  width: 55px; /* 根据需要调整大小 */
  height: 55px;
  object-fit: contain; /* 保持图片比例 */
}

/* --- 顶部导航栏升级设计 --- */
.app-header.glass-header {
  height: 64px; /* 稍微加高 */
  width: 100%;
  background: rgba(255, 255, 255, 0.8); /* 半透明白 */
  backdrop-filter: blur(12px); /* 磨砂玻璃效果 */
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: center; /* 内容居中或两侧对齐 */
  z-index: 50;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01);
}

.header-content {
  width: 100%;
  max-width: 1600px; /* 限制内容最大宽度，防止在大屏上太散 */
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.brand-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 品牌 Logo 图标 */
/*暂时没用了，先留着看后面还会不会用到*/
.brand-logo {
  width: 36px;
  height: 36px;
  border-radius: 10px; /* 圆角矩形 */
  background: linear-gradient(135deg, var(--primary-color), #818CF8);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
}

/* 品牌文字 */
.brand-text {
  display: flex;
  flex-direction: column;
  justify-content: center;
  line-height: 1.2;
}

.main-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.02em;
}

.sub-title {
  font-size: 11px;
  color: var(--text-sub);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* --- 主布局 --- */
.main-layout {
  flex: 1;
  display: flex;
  gap: 24px; 
  padding: 20px 24px 24px 24px; 
  overflow: hidden; 
}

.layout-left {
  flex: 0 0 40%; 
  display: flex;
  flex-direction: column;
  min-width: 350px;
}

.layout-right {
  flex: 0 0 60%;
  display: flex;
  flex-direction: column;
  position: relative; 
}

/* 卡片样式 */
.glass-card {
  background: #FFFFFF;
  border-radius: var(--card-radius);
  box-shadow: var(--shadow-md);
  border: 1px solid #CBD5E1; 
  overflow: hidden; 
  display: flex;
  flex-direction: column;
}

/* Loading 遮罩 */
.graph-loading-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
}
.loading-content {
  display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--primary-color);
}

/* Element 覆盖 */
.el-button--primary {
  --el-button-bg-color: var(--primary-color) !important;
  --el-button-border-color: var(--primary-color) !important;
  --el-button-hover-bg-color: var(--primary-hover) !important;
}

@media (max-width: 1024px) {
  .main-layout {
    flex-direction: column;
    overflow-y: auto;
  }
  .layout-left, .layout-right {
    flex: none;
    height: 600px; 
    width: 100%;
  }
  body { overflow: auto; height: auto; }
}
</style>