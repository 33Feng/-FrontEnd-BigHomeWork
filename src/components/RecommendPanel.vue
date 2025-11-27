<template>
  <div class="recommend-panel">
    <h3>相关推荐</h3>
    <el-empty v-if="!recommendations.length" description="暂无推荐内容"></el-empty>
    <el-card v-else class="recommend-card" v-for="(item, index) in recommendations" :key="index">
      <div class="recommend-item">
        <span class="entity">{{ item.entity }}</span>
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
}

.reason {
  font-size: 14px;
  color: #666;
}

.weight {
  align-self: flex-start;
}
</style>