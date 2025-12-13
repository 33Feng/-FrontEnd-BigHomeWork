<template>
  <div class="recommend-panel-container">
    <!-- 标签页切换：相关推荐/历史推荐 -->
    <el-tabs v-model="activeTab" class="recommend-tabs" type="card">
      <el-tab-pane label="相关推荐" name="related">
        <div class="recommend-content related-content">
          <el-empty v-if="!recommendations.length" description="暂无推荐内容"></el-empty>
          <el-card v-else class="recommend-card" v-for="(item, index) in recommendations" :key="'related-' + index">
            <!-- 优化相关推荐内容显示结构 -->
            <div class="recommend-item related-item">
              <div class="item-header">
                <a 
                  class="entity" 
                  :href="`https://www.baidu.com/s?wd=${encodeURIComponent(item.entity || item.label)}`" 
                  target="_blank"
                >
                  {{ item.entity || item.label }}
                </a>
                <el-rate 
                  v-model="item.weight" 
                  disabled 
                  max="10" 
                  class="weight"
                ></el-rate>
              </div>
              <div class="item-body">
                <span class="reason-label">推荐理由：</span>
                <span class="reason">{{ item.reason || item.desc || '该实体与当前内容高度相关' }}</span>
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
      <el-tab-pane label="历史推荐" name="history">
        <div class="recommend-content history-content">
          <el-empty v-if="!historyRecommendations.length" description="暂无历史记录"></el-empty>
          <el-card v-else class="recommend-card" v-for="(item, index) in historyRecommendations" :key="'history-' + index">
            <div class="recommend-item history-item">
              <a 
                class="entity" 
                :href="`https://www.baidu.com/s?wd=${encodeURIComponent(item)}`" 
                target="_blank"
              >
                {{ item }}
              </a>
              <el-button 
                type="text" 
                size="small" 
                class="delete-history" 
                @click="handleDeleteHistory(index)"
              >
                删除
              </el-button>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref } from 'vue';
import { ElEmpty, ElCard, ElRate, ElButton, ElTabs, ElTabPane } from 'element-plus';

// 接收父组件传递的推荐数据和历史记录
const props = defineProps({
  recommendations: {
    type: Array,
    default: () => []
  },
  historyRecommendations: {
    type: Array,
    default: () => []
  }
});

// 定义删除历史记录的事件
const emit = defineEmits(['delete-history']);

// 激活的标签页
const activeTab = ref('related');

const handleDeleteHistory = (index) => {
  emit('delete-history', index);
};
</script>

<style scoped>
.recommend-panel-container {
  width: 100%;
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

/* 标签页样式 */
.recommend-tabs {
  width: 100%;
  box-sizing: border-box;
}

/* 推荐内容容器：同一显示区域 */
.recommend-content {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 0;
}

/* 历史推荐内容：保留滚动条，固定最大高度 */
.history-content {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}

/* 相关推荐内容：自适应高度，显示全部内容 */
.related-content {
  height: fit-content;
}

/* 滚动条样式优化（仅历史推荐） */
.history-content::-webkit-scrollbar {
  width: 6px;
}

.history-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.history-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.history-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.recommend-card {
  margin-bottom: 10px;
  border-radius: 6px;
}

/* 相关推荐项：优化内容显示结构 */
.related-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
}

.related-item .item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.related-item .item-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 4px;
}

.reason-label {
  font-size: 14px;
  color: #999;
  font-weight: 500;
}

/* 历史推荐项 */
.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  padding: 10px;
}

.entity {
  font-size: 16px;
  font-weight: bold;
  color: #409EFF;
  text-decoration: none;
}

.entity:hover {
  text-decoration: underline;
}

.reason {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.weight {
  align-self: center;
}

.delete-history {
  color: #F56C6C;
  padding: 0;
  height: auto;
  line-height: normal;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .history-content {
    max-height: 300px;
  }

  .entity {
    font-size: 14px;
  }

  .reason {
    font-size: 12px;
  }
}
</style>