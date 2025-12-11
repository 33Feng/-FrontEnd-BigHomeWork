<template>
  <div id="app" class="container">
    <h1 class="title">知识图谱驱动的前端技术知识问答与推荐系统</h1>
    
    <el-row :gutter="20" class="main-layout">
      <!-- 问答与推荐面板（左侧，保留原span12样式） -->
      <el-col :span="12" class="panel-col">
        <div class="panel qa-panel">
          <h2>问答与推荐</h2>
          <!-- 问答面板 -->
          <QaPanel 
            @update:mainEntity="handleMainEntityChange" 
            :current-entity="currentEntity"
            style="margin-bottom: 20px;"
          />
          <!-- 推荐面板（滚动条控制显示区域，嵌入原有面板内） -->
          <div class="recommend-container">
            <h3 style="font-size: 16px; margin: 0 0 10px 0; color: #333; border-bottom: 1px solid #e6e6e6; padding-bottom: 8px;">
              相关实体推荐
              <span v-if="currentEntity" style="font-size: 12px; color: #409EFF; margin-left: 10px;">
                （当前：{{ currentEntity }}）
              </span>
            </h3>
            <RecommendPanel 
              :recommend-data="recommendData"
              :current-entity="currentEntity"
              :loading="recommendLoading"
              @recommend-click="handleRecommendClick"
              style="width: 100%; height: 280px;"
            />
          </div>
        </div>
      </el-col>
      
      <!-- 图谱面板（右侧，保留原span12样式） -->
      <el-col :span="12" class="panel-col">
        <div class="panel graph-panel">
          <h2>知识图谱可视化 
            <span v-if="currentEntity" style="font-size: 14px; color: #409EFF;">
              （当前聚焦：{{ currentEntity }}）
            </span>
          </h2>
          <!-- 图谱容器加载状态 -->
          <div v-if="!graphLoaded" class="graph-loading">
            <el-loading indicator="加载中..." />
          </div>
          <GraphVisual 
            :main-entity="mainEntity" 
            @update:currentEntity="handleCurrentEntityChange"
            @graph-loaded="graphLoaded = true"
            @getRecommendData="fetchRecommendData"
            style="width: 100%; height: 550px;"
          />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElRow, ElCol, ElLoading } from 'element-plus';
// 引入组件
import QaPanel from './components/QaPanel.vue';
import GraphVisual from './components/GraphVisual.vue';
import RecommendPanel from './components/RecommendPanel.vue';

// 核心实体状态（联动问答和图谱）
const mainEntity = ref(''); // 来自问答面板
const currentEntity = ref(''); // 来自图谱面板/推荐面板
const graphLoaded = ref(false); // 图谱容器加载状态

// 推荐面板相关状态
const recommendData = ref([]);
const recommendLoading = ref(false);

// 处理问答面板实体变化
const handleMainEntityChange = (entity) => {
  mainEntity.value = entity;
  if (!currentEntity.value) {
    currentEntity.value = entity;
    // 触发推荐数据加载
    fetchRecommendData(entity);
  }
};

// 处理图谱面板实体变化
const handleCurrentEntityChange = (entity) => {
  currentEntity.value = entity;
};

// 获取推荐数据（模拟接口请求）
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

    // 赋值推荐数据（若没有对应实体，默认显示前端开发的推荐）
    recommendData.value = mockRecommendData[entity] || mockRecommendData['前端开发'];
  } catch (error) {
    console.error('获取推荐数据失败：', error);
    recommendData.value = [];
  } finally {
    recommendLoading.value = false;
  }
};

// 处理推荐面板项点击
const handleRecommendClick = (label) => {
  if (!label) return;
  // 更新当前实体
  currentEntity.value = label;
  mainEntity.value = label;
  // 触发图谱更新（通过GraphVisual的搜索功能）
  const graphElement = document.querySelector('.graph-panel').__vue__?.$refs.graphRef;
  if (graphElement && graphElement.handleSearch) {
    graphElement.searchEntity = label;
    graphElement.handleSearch();
  }
  // 重新加载推荐数据
  fetchRecommendData(label);
};
</script>

<style>
/* 保留原有所有样式，未做修改 */
#app {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  font-family: Avenir, Helvetica, Arial, sans-serif;
}

.title {
  text-align: center;
  color: #409EFF;
  margin-bottom: 30px;
}

.main-layout {
  width: 100%;
  min-height: 700px;
  display: flex;
}

.panel-col {
  height: 100%;
  display: flex;
  box-sizing: border-box;
  padding: 0 10px;
}

.panel {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.qa-panel {
  height: 650px;
  display: flex;
  flex-direction: column;
}

.graph-panel {
  height: 650px;
  display: flex;
  flex-direction: column;
}

.panel h2 {
  margin-top: 0;
  color: #333;
  border-bottom: 1px solid #e6e6e6;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

/* 图谱加载样式 */
.graph-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #666;
  z-index: 5;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .main-layout {
    flex-direction: column;
  }
  
  .el-col {
    width: 100% !important;
    margin-bottom: 20px;
  }
  
  .qa-panel, .graph-panel {
    height: auto;
    min-height: 600px;
  }
}

/* 推荐容器样式（仅补充，不修改原有样式） */
.recommend-container {
  width: 100%;
  flex: 1;
  box-sizing: border-box;
}
</style>