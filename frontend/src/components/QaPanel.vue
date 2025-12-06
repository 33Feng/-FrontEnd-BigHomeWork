<template>
  <div class="qa-panel">
    <!-- 新增模式切换按钮 -->
    <div style="margin-bottom: 10px; display: flex; align-items: center; gap: 10px;">
      <span>回答模式：</span>
      <el-radio-group v-model="answerMode" @change="handleModeChange">
        <el-radio label="quick">快速回答 (5-7秒)</el-radio>
        <el-radio label="deep">深度回答 (最长60秒)</el-radio>
      </el-radio-group>
    </div>

    <el-form @submit.prevent="submitQuestion">
      <!-- 原有表单内容保持不变 -->
      <el-form-item label="请输入问题：">
        <el-input
          v-model="question"
          placeholder="例如：Vue3有哪些新特性？Vite的特性是什么？"
          clearable
          @keyup.enter="submitQuestion"
        ></el-input>
      </el-form-item>
      
      <!-- 快速提问按钮 -->
      <div v-if="currentEntity" style="margin-bottom: 10px;">
        <el-button type="text" @click="quickAsk">快速提问：{{ currentEntity }}相关知识</el-button>
      </div>
      
      <el-form-item>
        <el-button type="primary" @click="submitQuestion">提交问题</el-button>
        <el-button @click="resetForm">清空</el-button>
      </el-form-item>
    </el-form>

    <!-- 修改加载状态提示，区分不同模式 -->
    <div v-if="isLoading" class="loading">
      <template v-if="answerMode === 'deep'">深度思考中，请稍候（最长60秒）...</template>
      <template v-else>正在生成答案，请稍候（5-7秒）...</template>
    </div>

    <!-- 回答展示区域保持不变 -->
    <div class="answer-container" v-if="answer && !isLoading">
      <h3>回答：</h3>
      <el-card>
        <div class="answer-text" v-html="answer"></div>
      </el-card>
    </div>

    <RecommendPanel :recommendations="recommendations" />
  </div>
</template>

<script setup>
import { ref, defineEmits, defineProps, watch } from 'vue';
import { ElForm, ElFormItem, ElInput, ElButton, ElCard, ElMessage, ElRadioGroup, ElRadio } from 'element-plus';
import { api } from '../api/index';
import RecommendPanel from './RecommendPanel.vue';

// 接收父组件传递的图谱选中实体
const props = defineProps({
  currentEntity: {
    type: String,
    default: ''
  }
});

// 定义emit
const emit = defineEmits(['update:mainEntity']);

// 响应式数据
const question = ref('');
const answer = ref('');
const recommendations = ref([]);
const mainEntity = ref('');
const isLoading = ref(false);
// 新增：回答模式，默认快速回答
const answerMode = ref('quick');

// 处理模式切换
const handleModeChange = () => {
  // 可以在这里添加模式切换时的额外逻辑
  ElMessage.info(`已切换至${answerMode.value === 'quick' ? '快速' : '深度'}回答模式`);
};

// 提交问题（修改部分）
const submitQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题！');
    return;
  }

  isLoading.value = true;
  try {
    // 根据模式设置不同超时时间
    const timeout = answerMode.value === 'quick' ? 7000 : 60000;
    
    // 调用API时传递模式参数
    const res = await api.qa({
      question: question.value,
      mode: answerMode.value
    }, {
      timeout: timeout // 覆盖全局超时设置
    });
    
    answer.value = res.data.answer;
    recommendations.value = res.data.recommendations;
    mainEntity.value = res.data.related_entities[0] || '';
    emit('update:mainEntity', mainEntity.value);
  } catch (error) {
    if (error.code === 'ECONNABORTED') {
      ElMessage.error(`${answerMode.value === 'quick' ? '快速回答超时' : '深度思考超时'}，请稍后重试`);
    } else {
      ElMessage.error('获取回答失败：' + (error.message || '未知错误'));
    }
  } finally {
    isLoading.value = false;
  }
};

// 原有其他方法保持不变
const resetForm = () => {
  question.value = '';
  answer.value = '';
  recommendations.value = [];
  mainEntity.value = '';
  emit('update:mainEntity', '');
};

const quickAsk = () => {
  if (props.currentEntity) {
    question.value = `${props.currentEntity}相关知识有哪些？`;
    submitQuestion();
  }
};

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