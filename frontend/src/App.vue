<template>
  <div id="app" class="app-container">
    <header class="app-header">
      <div class="header-left">
        <h1 class="title">知识图谱驱动的前端技术知识问答与推荐系统</h1>
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
import { Loading } from '@element-plus/icons-vue';
// 引入组件
import QaPanel from './components/QaPanel.vue';
// 注释：GraphVisual组件根据项目实际路径引入
import GraphVisual from './components/GraphVisual.vue';

// 核心实体状态（联动问答和图谱）
const mainEntity = ref(''); // 来自问答面板
const currentEntity = ref(''); // 来自图谱面板/推荐面板
const graphLoaded = ref(false); // 图谱容器加载状态

// 推荐面板相关状态（仅用于图谱相关推荐）
const recommendData = ref([]);
const recommendLoading = ref(false);

// 处理问答面板实体变化
const handleMainEntityChange = (entity) => {
  mainEntity.value = entity;
  if (!currentEntity.value) {
    currentEntity.value = entity;
    fetchRecommendData(entity);
  }
};

// 处理图谱面板实体变化
const handleCurrentEntityChange = (entity) => {
  currentEntity.value = entity;
};

// 获取推荐数据（供图谱使用）
const fetchRecommendData = async (entity) => {
  if (!entity) {
    recommendData.value = [];
    return;
  }

  recommendLoading.value = true;
  try {
    // 模拟API请求延迟
    await new Promise(resolve => setTimeout(resolve, 800));

    // 模拟推荐数据
    const mockRecommendData = {
      '前端开发': [
        { label: 'Vue3', desc: '渐进式JavaScript框架，最新版本' },
        { label: 'React18', desc: '用于构建用户界面的JavaScript库' },
        { label: 'TypeScript', desc: '强类型的JavaScript超集' },
        { label: 'Vite', desc: '新一代前端构建工具' },
        { label: 'Tailwind CSS', desc: '实用优先的CSS框架' }
      ],
      'Vue': [
        { label: 'Vue Router', desc: 'Vue的官方路由管理器' },
        { label: 'Pinia', desc: 'Vue的新一代状态管理库' },
        { label: 'Vite', desc: 'Vue作者开发的构建工具' },
        { label: 'Nuxt.js', desc: 'Vue的服务端渲染框架' }
      ],
      'JavaScript': [
        { label: 'ES6+', desc: 'JavaScript的新一代标准' },
        { label: 'Node.js', desc: '服务端JavaScript运行时' },
        { label: 'Webpack', desc: 'JavaScript模块打包工具' }
      ],
      'Vue3': [
        { label: 'Composition API', desc: 'Vue3的核心语法糖，提供更灵活的代码组织方式' },
        { label: 'Teleport', desc: 'Vue3的内置组件，用于将组件渲染到指定DOM节点' },
        { label: 'Suspense', desc: 'Vue3的内置组件，用于处理异步组件加载状态' }
      ]
    };

    recommendData.value = mockRecommendData[entity] || mockRecommendData['前端开发'];
  } catch (error) {
    console.error('获取推荐数据失败：', error);
    recommendData.value = [];
  } finally {
    recommendLoading.value = false;
  }
};
</script>

<style>
:root {
  /* 主色调：Indigo (靛青色) */
  --primary-color: #4F46E5; 
  --primary-hover: #4338CA;
  
  /* 背景色：极淡的灰蓝色 */
  --bg-color: #F8FAFC; 
  
  /* 文字颜色 */
  --text-main: #1E293B; /* 深灰 */
  --text-sub: #64748B;  /* 浅灰 */
  
  /* 边框与圆角 */
  --border-color: #CBD5E1;
  --card-radius: 12px; 
  
  /* 柔和阴影 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

body {
  margin: 0;
  background-color: var(--bg-color);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--text-main);
  height: 100vh;
  overflow: hidden; 
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 16px 24px;
  box-sizing: border-box;
  gap: 16px;
}

/* 顶部栏样式 */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 48px;
  flex-shrink: 0;
  padding: 0 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-main);
  letter-spacing: -0.5px;
}
/* 主布局：Flexbox 实现严格分栏 */
.main-layout {
  flex: 1;
  display: flex;
  gap: 24px; /* 左右卡片间距 */
  overflow: hidden; 
}

/* 左侧：固定 40% */
.layout-left {
  flex: 0 0 40%; 
  display: flex;
  flex-direction: column;
  min-width: 350px;
}

/* 右侧：固定 60% */
.layout-right {
  flex: 0 0 60%;
  display: flex;
  flex-direction: column;
  position: relative; 
}

.glass-card {
  background: #FFFFFF;
  border-radius: var(--card-radius);
  box-shadow: var(--shadow-md);
  border: 2px solid var(--border-color); 
  overflow: hidden; 
  display: flex;       /* 确保子元素填充 */
  flex-direction: column;
}

/* 图谱加载时的遮罩层 */
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
.el-button--primary {
  --el-button-bg-color: var(--primary-color) !important;
  --el-button-border-color: var(--primary-color) !important;
  --el-button-hover-bg-color: var(--primary-hover) !important;
}

/* 响应式适配 */
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