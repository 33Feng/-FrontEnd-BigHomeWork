<template>
  <div id="app" class="container">
    <h1 class="title">知识图谱驱动的前端技术知识问答与推荐系统</h1>
    
    <el-row :gutter="20" class="main-layout">
      <!-- 问答面板 -->
      <el-col :span="12" class="panel-col">
        <div class="panel qa-panel">
          <h2>问答与推荐</h2>
          <QaPanel 
            @update:mainEntity="handleMainEntityChange" 
            :current-entity="currentEntity"
          />
        </div>
      </el-col>
      
      <!-- 图谱面板 -->
      <el-col :span="12" class="panel-col">
        <div class="panel graph-panel">
          <h2>知识图谱可视化 
            <span v-if="currentEntity" style="font-size: 14px; color: #409EFF;">
              （当前聚焦：{{ currentEntity }}）
            </span>
          </h2>
          <GraphVisual 
            :main-entity="mainEntity" 
            @update:currentEntity="handleCurrentEntityChange"
          />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElRow, ElCol } from 'element-plus';
import QaPanel from './components/QaPanel.vue';
import GraphVisual from './components/GraphVisual.vue';

// 核心实体状态（联动问答和图谱）
const mainEntity = ref(''); // 来自问答面板
const currentEntity = ref(''); // 来自图谱面板

// 处理问答面板实体变化
const handleMainEntityChange = (entity) => {
  mainEntity.value = entity;
  if (!currentEntity.value) {
    currentEntity.value = entity;
  }
};

// 处理图谱面板实体变化
const handleCurrentEntityChange = (entity) => {
  currentEntity.value = entity;
};
</script>

<style>
/* 基础样式 */
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

/* 布局样式：确保子元素有足够空间 */
.main-layout {
  width: 100%;
  min-height: 700px; /* 父容器最小高度 */
  display: flex;
}

.panel-col {
  height: 100%;
  display: flex;
}

/* 面板样式：固定高度，避免挤压 */
.panel {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  width: 100%;
  box-sizing: border-box; /* 关键：padding不影响整体尺寸 */
}

/* 问答面板高度 */
.qa-panel {
  height: 650px;
}

/* 图谱面板高度（与问答面板一致） */
.graph-panel {
  height: 650px;
}

.panel h2 {
  margin-top: 0;
  color: #333;
  border-bottom: 1px solid #e6e6e6;
  padding-bottom: 10px;
  margin-bottom: 20px;
}
</style>