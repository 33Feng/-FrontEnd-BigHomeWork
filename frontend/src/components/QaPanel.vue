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

    <!-- 回答展示 -->
    <div class="answer-container" v-if="answer">
      <h3>回答：</h3>
      <el-card>
        <pre class="answer-text">{{ answer }}</pre>
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

// 提交问题
const submitQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题！');
    return;
  }

  try {
    const res = await api.qa(question.value);
    answer.value = res.data.answer;
    recommendations.value = res.data.recommendations;
    // 获取核心实体（问答返回的related_entities中取第一个）
    mainEntity.value = res.data.related_entities[0] || '';
    // 向父组件发送核心实体
    emit('update:mainEntity', mainEntity.value);
  } catch (error) {
    ElMessage.error('获取回答失败：' + (error.message || '未知错误'));
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
.answer-text {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  margin: 0;
}
</style>