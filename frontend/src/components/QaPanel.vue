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
    const timeout = answerMode.value === 'quick' ? 7000 : 200000;
    
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
/* 回答容器：保持原位置和宽度，不影响其他区域 */
.answer-container {
  margin-top: 15px;
  width: 100%; /* 继承父容器宽度，不额外占用空间 */
}
/* 关键修改：答案文本显示容器 */
.answer-text {
  /* 1. 保持原显示区域高度（根据你的需求调整 max-height，比如原高度是 400px） */
  max-height: 400px; /* 核心：限制容器最大高度（和原显示区域一致） */
  /* 2. 纵向溢出时显示滚动条，横向不溢出（避免挤压布局） */
  overflow-y: auto; /* 关键：内容超过 max-height 时显示纵向滚动条 */
  overflow-x: hidden; /* 防止横向滚动条出现，保持布局整洁 */
  /* 3. 其他样式优化（可选，根据原有样式调整） */
  padding: 10px;
  line-height: 1.6; /* 提高可读性 */
  word-break: break-all; /* 长单词/链接自动换行，避免横向溢出 */
}
/* 滚动条样式优化（可选，让滚动条更美观） */
.answer-text::-webkit-scrollbar {
  width: 6px; /* 滚动条宽度 */
}
.answer-text::-webkit-scrollbar-track {
  background: #f1f1f1; /* 滚动条轨道背景 */
  border-radius: 3px;
}
.answer-text::-webkit-scrollbar-thumb {
  background: #c1c1c1; /* 滚动条滑块颜色 */
  border-radius: 3px;
}
.answer-text::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8; /* 滚动条 hover 状态 */
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