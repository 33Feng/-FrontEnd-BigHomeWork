<template>
  <div class="recommend-panel-container">
    <div class="panel-header">
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'path' }" 
        @click="activeTab = 'path'"
      >
        <el-icon><Guide /></el-icon> 智能路径
      </div>
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'related' }" 
        @click="activeTab = 'related'"
      >
        <el-icon><Connection /></el-icon> 关联推荐
      </div>
      <div 
        class="tab-item" 
        :class="{ active: activeTab === 'history' }" 
        @click="activeTab = 'history'"
      >
        <el-icon><Time /></el-icon> 历史记录
      </div>
    </div>

    <div class="panel-body">
      
      <div v-if="activeTab === 'path'" class="path-view">
        
        <el-empty 
          v-if="!currentEntity" 
          description="请在左侧图谱点击一个节点" 
          :image-size="80"
        ></el-empty>
        
        <div v-else-if="!learningPath && !loadingPath" class="start-plan-box">
          <div class="plan-icon-wrapper">
            <el-icon class="plan-icon"><Cpu /></el-icon>
          </div>
          <h3>准备规划：{{ currentEntity }}</h3>
          <p>AI 将分析图谱结构，为您生成专属学习路线。</p>
          <el-button type="primary" size="large" round @click="fetchLearningPath">
            <el-icon class="el-icon--left"><MagicStick /></el-icon>
            开始智能规划
          </el-button>
        </div>

        <div v-else-if="loadingPath" class="loading-box">
          <div class="spinner"></div>
          <p>DeepSeek 正在深度思考...</p>
          <p class="sub-text">分析 {{ currentEntity }} 的前置与进阶知识</p>
        </div>
        
        <div v-else-if="learningPath" class="path-timeline-box">
          <div class="path-title">
            <span>🎓 {{ learningPath.core?.name }} 学习路线</span>
            <el-button link type="primary" size="small" @click="fetchLearningPath">重新规划</el-button>
          </div>

          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in learningPath.prerequisites"
              :key="'pre'+index"
              type="info"
              hollow
              center
              placement="top"
            >
              <el-card class="path-card pre-card" shadow="hover">
                <div class="card-header">
                  <el-tag type="info" size="small" effect="dark">前置基础</el-tag>
                  <span class="card-title">{{ item.name }}</span>
                  <el-button link type="info" @click="openSearch(item.name)">
                    <el-icon><Search /></el-icon>
                  </el-button>
                </div>
                <p class="card-desc">{{ item.desc }}</p>
              </el-card>
            </el-timeline-item>

            <el-timeline-item
              center
              placement="top"
              type="primary"
              size="large"
              icon="StarFilled"
            >
              <el-card class="path-card core-card" shadow="always">
                <div class="card-header">
                  <el-tag type="primary" effect="dark">核心重点</el-tag>
                  <span class="card-title main-title">{{ learningPath.core?.name }}</span>
                </div>
                <p class="card-desc main-desc">{{ learningPath.core?.desc }}</p>
              </el-card>
            </el-timeline-item>

            <el-timeline-item
              v-for="(item, index) in learningPath.next_steps"
              :key="'next'+index"
              type="success"
              hollow
              center
              placement="top"
            >
              <el-card class="path-card next-card" shadow="hover">
                <div class="card-header">
                  <el-tag type="success" size="small" effect="dark">进阶方向</el-tag>
                  <span class="card-title">{{ item.name }}</span>
                  <el-button link type="success" @click="openSearch(item.name)">
                    <el-icon><Right /></el-icon>
                  </el-button>
                </div>
                <p class="card-desc">{{ item.desc }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>

      <div v-else-if="activeTab === 'related'" class="list-view">
        <el-empty v-if="!recommendations.length" description="暂无关联数据" :image-size="60"></el-empty>
        <div v-else class="list-container">
          <div v-for="(item, index) in recommendations" :key="'rel'+index" class="list-item">
            <div class="list-icon bg-blue"><el-icon><Connection /></el-icon></div>
            <div class="list-info">
              <div class="list-top">
                <span class="list-name" @click="openSearch(item.entity || item.label)">
                  {{ item.entity || item.label }}
                </span>
                <el-rate :model-value="Number(item.weight)" disabled size="small" :max="5"></el-rate>
              </div>
              <div class="list-desc">{{ item.reason || item.desc }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'history'" class="list-view">
        <el-empty v-if="!historyRecommendations.length" description="暂无搜索历史" :image-size="60"></el-empty>
        <div v-else class="list-container">
          <div v-for="(item, index) in historyRecommendations" :key="'his'+index" class="list-item">
            <div class="list-icon bg-gray"><el-icon><Time /></el-icon></div>
            <div class="list-info">
              <span class="list-name" @click="openSearch(item)">{{ item }}</span>
              <span class="list-time">最近搜索</span>
            </div>
            <el-button type="danger" link icon="Delete" @click="handleDeleteHistory(index)"></el-button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, watch } from 'vue';
import { api } from '../api/index';
import { ElMessage } from 'element-plus';
import { Guide, Connection, Time, Search, Right, Delete, MagicStick, Cpu, StarFilled } from '@element-plus/icons-vue';

const props = defineProps({
  recommendations: { type: Array, default: () => [] },
  historyRecommendations: { type: Array, default: () => [] },
  currentEntity: { type: String, default: '' }
});

const emit = defineEmits(['delete-history']);
const activeTab = ref('path');
const learningPath = ref(null);
const loadingPath = ref(false);

const handleDeleteHistory = (index) => {
  emit('delete-history', index);
};

const openSearch = (keyword) => {
  window.open(`https://www.baidu.com/s?wd=${encodeURIComponent(keyword)}`, '_blank');
};

// 获取路径（手动触发）
const fetchLearningPath = async () => {
  if (!props.currentEntity) return;
  loadingPath.value = true;
  learningPath.value = null; // 清空旧数据
  
  try {
    const res = await api.getLearningPath(props.currentEntity);
    if (res.data) {
        learningPath.value = res.data;
    } else {
        ElMessage.warning('AI 未能生成路径，请重试');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('路径规划失败，请检查网络');
  } finally {
    loadingPath.value = false;
  }
};

// 监听实体变化，只重置状态，不自动请求
watch(() => props.currentEntity, (newVal) => {
  if (newVal) {
    learningPath.value = null; 
    activeTab.value = 'path'; // 自动切回路径 Tab
  }
});
</script>

<style scoped>
/* --- 基础容器 --- */
.recommend-panel-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

/* --- 顶部 Tab 切换 --- */
.panel-header {
  display: flex;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 12px 0;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-bottom: 2px solid transparent;
  user-select: none;
}

.tab-item:hover {
  background: #f0f2f5;
  color: #409EFF;
}

.tab-item.active {
  color: #409EFF;
  background: #fff;
  border-bottom: 2px solid #409EFF;
  font-weight: 600;
}

/* --- 内容滚动区 --- */
.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fff;
  position: relative;
}

/* 自定义滚动条 */
.panel-body::-webkit-scrollbar {
  width: 6px;
}

.panel-body::-webkit-scrollbar-thumb {
  background: #e0e0e0;
  border-radius: 4px;
}

/* 1.准备规划状态 */
.start-plan-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding-top: 40px;
}

.plan-icon-wrapper {
  width: 80px;
  height: 80px;
  background: #ecf5ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.plan-icon {
  font-size: 40px;
  color: #409EFF;
}

.start-plan-box h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.start-plan-box p {
  color: #909399;
  margin-bottom: 30px;
  font-size: 14px;
}

/* 加载中状态*/
.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding-top: 60px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409EFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-box p {
  color: #409EFF;
  font-weight: bold;
  margin: 0;
}

.loading-box .sub-text {
  color: #909399;
  font-weight: normal;
  font-size: 12px;
  margin-top: 5px;
}

/* --- 3. 🗺️ 路径展示样式 --- */
.path-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-weight: bold;
  color: #303133;
  font-size: 16px;
}

/* 卡片基础 */
.path-card {
  border: none;
  border-radius: 8px;
  position: relative;
}

.path-card :deep(.el-card__body) {
  padding: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.card-title {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  flex: 1;
}

.card-desc {
  font-size: 12px;
  color: #666;
  margin: 0;
  line-height: 1.5;
}

/* 卡片分类颜色 */
/* 前置 - 灰色 */
.pre-card {
  background: #f4f4f5;
  border-left: 3px solid #909399;
}

/* 核心 - 蓝色 */
.core-card {
  background: #ecf5ff;
  border-left: 3px solid #409EFF;
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15) !important;
}

/* 进阶 - 绿色 */
.next-card {
  background: #f0f9eb;
  border-left: 3px solid #67C23A;
}

.main-title {
  font-size: 16px;
  color: #409EFF;
}

.main-desc {
  color: #555;
}

/* --- 列表样式 (关联推荐/历史记录) --- */
.list-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-item {
  display: flex;
  align-items: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
  gap: 12px;
  transition: all 0.2s;
}

.list-item:hover {
  background: #ecf5ff;
}

.list-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.bg-blue {
  background: #a0cfff;
}

.bg-gray {
  background: #dcdfe6;
}

.list-info {
  flex: 1;
  overflow: hidden;
}

.list-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.list-name {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  cursor: pointer;
}

.list-name:hover {
  text-decoration: underline;
  color: #409EFF;
}

.list-desc {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-time {
  font-size: 12px;
  color: #ccc;
}
</style>