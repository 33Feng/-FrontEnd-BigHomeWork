<template>
  <div class="qa-panel">
    <el-form @submit.prevent="submitQuestion">
      <el-form-item label="请输入问题：">
        <el-input
          v-model="question"
          placeholder="例如：Vue3有哪些新特性？Vite的特性是什么？"
          clearable
          @keyup.enter="submitQuestion"
        ></el-input>
      </el-form-item>
      <!-- 新增：快速提问按钮（基于图谱选中的实体） -->
      <div v-if="currentEntity" style="margin-bottom: 10px;">
        <el-button type="text" @click="quickAsk">快速提问：{{ currentEntity }}相关知识</el-button>
      </div>
      <el-form-item>
        <el-button type="primary" @click="submitQuestion">提交问题</el-button>
        <el-button @click="resetForm">清空</el-button>
      </el-form-item>
    </el-form>

    <!-- 加载状态提示 -->
    <div v-if="isLoading" class="loading">正在生成答案，请稍候...</div>

    <!-- 回答展示：将pre标签改为div，使用v-html渲染 -->
  <div class="answer-container" v-if="answer && !isLoading">
    <h3>回答：</h3>
    <el-card>
      <!-- 关键修改：用v-html展示HTML内容，移除pre标签 -->
      <div class="answer-text" v-html="answer"></div>
    </el-card>
  </div>


    <!-- 推荐面板 -->
    <RecommendPanel :recommendations="recommendations" />
  </div>
</template>

<script setup>
import { ref, defineEmits, defineProps, watch } from 'vue';
import { ElForm, ElFormItem, ElInput, ElButton, ElCard, ElMessage } from 'element-plus';
import { api } from '../api/index';
import RecommendPanel from './RecommendPanel.vue';

// 接收父组件传递的图谱选中实体
const props = defineProps({
  currentEntity: {
    type: String,
    default: ''
  }
});

// 定义emit，向父组件传递核心实体
const emit = defineEmits(['update:mainEntity']);

// 响应式数据
const question = ref('');
const answer = ref('');
const recommendations = ref([]);
const mainEntity = ref(''); // 核心实体
// 新增加载状态变量
const isLoading = ref(false);

// 提交问题
const submitQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题！');
    return;
  }

  isLoading.value = true; // 开始加载
  try {
    const res = await api.qa(question.value);
    answer.value = res.data.answer; // 直接接收HTML格式的答案
    recommendations.value = res.data.recommendations;
    mainEntity.value = res.data.related_entities[0] || '';
    emit('update:mainEntity', mainEntity.value);
  } catch (error) {
    // 区分超时错误和其他错误
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试（问题可能较复杂，需要更长时间处理）');
    } else {
      ElMessage.error('获取回答失败：' + (error.message || '未知错误'));
    }
  } finally {
    isLoading.value = false; // 无论成功失败，结束加载
  }
};

// 重置表单
const resetForm = () => {
  question.value = '';
  answer.value = '';
  recommendations.value = [];
  mainEntity.value = '';
  // 重置时通知父组件清空实体（显示全量图谱）
  emit('update:mainEntity', '');
};

// 新增：基于图谱选中的实体快速提问
const quickAsk = () => {
  if (props.currentEntity) {
    question.value = `${props.currentEntity}相关知识有哪些？`;
    submitQuestion();
  }
};

// 监听图谱实体变化，自动填充问题（可选）
watch(
  () => props.currentEntity,
  (newEntity) => {
    if (newEntity && !question.value.trim()) {
      question.value = `${newEntity}相关知识有哪些？`;
    }
  },
  { immediate: true }
);
</script>

<style scoped>
/* 原有样式不变 */
.qa-panel {
  margin-bottom: 20px;
}
.answer-container {
  margin-top: 20px;
}
/* .answer-text {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  margin: 0;
} */
.answer-text {
  font-size: 15px;
  line-height: 1.8; /* 增加行高，提升可读性 */
  color: #333;
  padding: 15px; /* 内部间距 */
   /* 1. 设置最大高度*/
  max-height: 300px; 
  /* 2. 开启垂直滚动 */
  overflow-y: auto;
  /* 3. 防止水平滚动条出现 */
  overflow-x: hidden; 
}
.answer-text::-webkit-scrollbar {
  width: 8px; /* 滚动条宽度 */
}
.answer-text::-webkit-scrollbar-thumb {
  background-color: #dcdfe6; /* 滚动条滑块颜色 */
  border-radius: 4px; 
}
.answer-text::-webkit-scrollbar-thumb:hover {
  background-color: #c0c4cc; /* 鼠标悬停时的颜色 */
}
.answer-text::-webkit-scrollbar-track {
  background-color: #f5f7fa; /* 滚动条轨道颜色 */
}
/* 优化标题样式 */
.answer-text h1,
.answer-text h2,
.answer-text h3,
.answer-text h4 {
  margin: 1.5em 0 0.8em;
  color: #2c3e50;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}
/* 优化列表样式 */
.answer-text ul,
.answer-text ol {
  margin: 1em 0;
  padding-left: 2em;
}

.answer-text li {
  margin: 0.5em 0;
}
/* 优化链接样式 */
.answer-text a {
  color: #42b983;
  text-decoration: none;
}

.answer-text a:hover {
  text-decoration: underline;
}
/* 优化代码块样式（如果有代码） */
.answer-text pre {
  background: #f5f5f5;
  padding: 1em;
  border-radius: 4px;
  overflow-x: auto;
  font-family: monospace;
  margin: 1em 0;
}

.answer-text code {
  background: #f0f0f0;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}
/* 新增加载状态样式 */
.loading {
  margin-top: 20px;
  padding: 20px;
  text-align: center;
  color: #666;
  background: #f5f5f5;
  border-radius: 4px;
}
</style>