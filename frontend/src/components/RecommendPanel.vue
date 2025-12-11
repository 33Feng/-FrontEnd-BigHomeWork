<template>
  <div class="recommend-panel">
    <h3>相关推荐</h3>
    <el-empty v-if="!recommendations.length" description="暂无推荐内容"></el-empty>
    <el-card v-else class="recommend-card" v-for="(item, index) in recommendations" :key="index">
      <div class="recommend-item">
        <!-- 为实体添加百度搜索链接 -->
        <a 
          class="entity" 
          :href="`https://www.baidu.com/s?wd=${encodeURIComponent(item.entity)}`" 
          target="_blank"
        >
          {{ item.entity }}
        </a>
        <span class="reason">{{ item.reason }}</span>
        <el-rate 
          v-model="item.weight" 
          disabled 
          max="10" 
          class="weight"
        ></el-rate>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import { ElEmpty, ElCard, ElRate } from 'element-plus';

// 接收父组件传递的推荐数据
const props = defineProps({
  recommendations: {
    type: Array,
    default: () => []
  }
});
</script>

<style scoped>
.recommend-panel {
  margin-top: 20px;
  /* 添加滚动条功能：限制最大高度并允许纵向滚动 */
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px; /* 避免滚动条与内容重叠 */
}

/* 滚动条样式优化 */
.recommend-panel::-webkit-scrollbar {
  width: 6px;
}

.recommend-panel::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.recommend-panel::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.recommend-panel::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.recommend-card {
  margin-bottom: 10px;
}

.recommend-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
}

.weight {
  align-self: flex-start;
}
</style>