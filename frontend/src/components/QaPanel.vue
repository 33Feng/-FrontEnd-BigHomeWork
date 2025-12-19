<template>
  <div class="qa-panel">
    <!-- 模式切换按钮 -->
    <div style="margin-bottom: 10px; display: flex; align-items: center; gap: 10px;">
      <span>回答模式：</span>
      <el-radio-group v-model="answerMode" @change="handleModeChange">
        <el-radio label="quick">快速回答 (5-7秒)</el-radio>
        <el-radio label="deep">深度回答 (最长120秒)</el-radio>
      </el-radio-group>
    </div>

    <el-form @submit.prevent="submitQuestion">
      <!-- 问题输入框，增加历史推荐下拉 -->
      <el-form-item label="请输入问题：">
        <div class="search-container">
          <el-input
            v-model="question"
            placeholder="例如：Vue3有哪些新特性？Vite的特性是什么？"
            clearable
            @keyup.enter="submitQuestion"
            @focus="showHistoryDropdown = true"
            @blur="handleInputBlur"
          ></el-input>
          
          <!-- 搜索历史下拉条 -->
          <div 
            v-if="showHistoryDropdown && searchHistory.length" 
            class="history-dropdown"
            @mouseenter="isMouseInDropdown = true"
            @mouseleave="isMouseInDropdown = false"
          >
            <div class="dropdown-header">搜索历史</div>
            <div 
              class="history-item" 
              v-for="(item, index) in searchHistory" 
              :key="index"
              @click="selectHistoryItem(item)"
            >
              {{ item }}
              <el-button 
                type="text" 
                size="small" 
                class="delete-item"
                @click.stop="deleteHistoryItem(index)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div class="clear-history" @click="clearAllHistory">
              清除全部历史
            </div>
          </div>
        </div>
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

    <!-- 加载状态提示 -->
    <div v-if="isLoading" class="loading">
      <template v-if="answerMode === 'deep'">深度思考中，请稍候（最长120秒）...</template>
      <template v-else>正在生成答案，请稍候（5-7秒）...</template>
    </div>

    <!-- 回答展示区域 -->
    <div class="answer-container" v-if="answer && !isLoading">
      <h3>回答：</h3>
      <el-card>
        <div class="answer-text" v-html="answer"></div>
      </el-card>
    </div>

    <!-- 推荐面板：确保容器在灰色区域内 -->
    <div class="recommend-wrapper">
      <RecommendPanel 
        :recommendations="recommendations" 
        :history-recommendations="searchHistory"
        :current-entity="currentEntity"
        @delete-history="deleteHistoryItem"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, defineEmits, defineProps, watch, onMounted } from 'vue';
import { ElForm, ElFormItem, ElInput, ElButton, ElCard, ElMessage, ElRadioGroup, ElRadio, ElIcon } from 'element-plus';
import { Close } from '@element-plus/icons-vue';
// 引入封装的API（保持原有导入方式）
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

// 响应式数据（保留所有原有数据）
const question = ref('');
const answer = ref('');
const recommendations = ref([]);
const mainEntity = ref('');
const isLoading = ref(false);
const answerMode = ref('quick');
// 搜索历史相关
const searchHistory = ref([]);
const showHistoryDropdown = ref(false);
const isMouseInDropdown = ref(false);
const blurTimeout = ref(null);

// 初始化时从本地存储加载搜索历史
onMounted(() => {
  const savedHistory = localStorage.getItem('searchHistory');
  if (savedHistory) {
    searchHistory.value = JSON.parse(savedHistory);
  }
});

// 保存搜索历史到本地存储
const saveSearchHistory = () => {
  localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value));
};

// 处理输入框失去焦点
const handleInputBlur = () => {
  // 延迟隐藏，等待点击事件触发
  blurTimeout.value = setTimeout(() => {
    if (!isMouseInDropdown.value) {
      showHistoryDropdown.value = false;
    }
  }, 200);
};

// 选择历史记录项
const selectHistoryItem = (item) => {
  question.value = item;
  showHistoryDropdown.value = false;
};

// 删除单个历史记录
const deleteHistoryItem = (index) => {
  searchHistory.value.splice(index, 1);
  saveSearchHistory();
};

// 清除所有历史记录
const clearAllHistory = () => {
  searchHistory.value = [];
  saveSearchHistory();
};

// 处理模式切换
const handleModeChange = () => {
  ElMessage.info(`已切换至${answerMode.value === 'quick' ? '快速' : '深度'}回答模式`);
};

// 提交问题（核心修正 DeepSeek 调用逻辑，保留原有业务逻辑）
const submitQuestion = async () => {
  const trimmedQuestion = question.value.trim();
  if (!trimmedQuestion) {
    ElMessage.warning('请输入问题！');
    return;
  }

  // 原有搜索历史处理逻辑（保留）
  const index = searchHistory.value.indexOf(trimmedQuestion);
  if (index > -1) {
    searchHistory.value.splice(index, 1);
  }
  searchHistory.value.unshift(trimmedQuestion);
  if (searchHistory.value.length > 10) {
    searchHistory.value.pop();
  }
  saveSearchHistory();

  isLoading.value = true;
  try {
    // 修正：根据模式设置超时时间，与前端显示一致
    const requestTimeout = answerMode.value === 'quick' ? 7000 : 120000;
    // 调用 DeepSeek API（修正参数传递和超时配置）
    const res = await api.qa(
      {
        question: trimmedQuestion,
        mode: answerMode.value, // 传递回答模式给后端
        stream: false // 关闭流式返回，确保完整响应
      },
      {
        timeout: requestTimeout, // 单独设置超时，覆盖全局配置
        headers: {
          'Content-Type': 'application/json' // 确保请求头正确
        }
      }
    );

    // 修正：兼容 DeepSeek 响应格式，提取核心数据（根据实际响应调整，此处保留原有解析逻辑并增强容错）
    const responseData = res.data || res;
    answer.value = responseData.answer || responseData.content || '';
    recommendations.value = responseData.recommendations || responseData.suggestions || [];
    mainEntity.value = (responseData.related_entities && responseData.related_entities[0]) || (recommendations.value[0]?.label || '');
    emit('update:mainEntity', mainEntity.value);

  } catch (error) {
    // 修正：细化 DeepSeek 常见错误处理
    let errorMsg = '';
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      errorMsg = `${answerMode.value === 'quick' ? '快速回答超时' : '深度思考超时'}，请稍后重试`;
    } else if (error.response?.status === 401) {
      errorMsg = 'DeepSeek API 密钥无效，请检查配置';
    } else if (error.response?.status === 402) {
      errorMsg = 'DeepSeek 额度不足，请充值后重试';
    } else if (error.response?.status === 403) {
      errorMsg = '无权限访问 DeepSeek API，请检查权限配置';
    } else if (error.response?.data?.error?.message) {
      errorMsg = `DeepSeek 错误：${error.response.data.error.message}`;
    } else {
      errorMsg = '获取回答失败：' + (error.message || '未知错误');
    }
    ElMessage.error(errorMsg);

    // 保留原有逻辑：错误时显示默认内容，保证页面不空白
    answer.value = `<p>抱歉，暂时无法为你提供回答，请稍后重试。</p>`;
    recommendations.value = [
      { label: 'Vue3', desc: '渐进式JavaScript框架，支持Composition API', weight: 5 },
      { label: 'Vite', desc: '新一代前端构建工具，极速冷启动', weight: 4 },
      { label: 'TypeScript', desc: '强类型JavaScript超集', weight: 4 },
    ];
  } finally {
    isLoading.value = false;
    showHistoryDropdown.value = false;
    // 清除超时定时器，防止内存泄漏
    clearTimeout(blurTimeout.value);
  }
};

// 重置表单（保留原有逻辑）
const resetForm = () => {
  question.value = '';
  answer.value = '';
  recommendations.value = [];
  mainEntity.value = '';
  emit('update:mainEntity', '');
};

// 快速提问（保留原有逻辑）
const quickAsk = () => {
  if (props.currentEntity) {
    question.value = `${props.currentEntity}相关知识有哪些？`;
    submitQuestion();
  }
};

// 监听当前实体变化（保留原有逻辑）
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
.qa-panel {
  margin-bottom: 20px;
  width: 100%;
  box-sizing: border-box;
  padding: 0;
}

/* 搜索容器和历史下拉样式（保留原有） */
.search-container {
  position: relative;
  width: 100%;
}

.history-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-header {
  padding: 10px 15px;
  font-weight: bold;
  color: #606266;
  border-bottom: 1px solid #e4e7ed;
}

.history-item {
  padding: 10px 15px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-item:hover {
  background-color: #f5f7fa;
}

.delete-item {
  color: #909399;
  padding: 0;
  height: auto;
}

.delete-item:hover {
  color: #F56C6C;
}

.clear-history {
  padding: 10px 15px;
  text-align: center;
  color: #409EFF;
  cursor: pointer;
  border-top: 1px solid #e4e7ed;
}

.clear-history:hover {
  background-color: #f5f7fa;
}

/* 回答容器样式（保留原有） */
.answer-container {
  margin-top: 15px;
  width: 100%;
  box-sizing: border-box;
}

.answer-text {
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px;
  line-height: 1.6;
  word-break: break-all;
}

/* 滚动条样式优化（保留原有） */
.answer-text::-webkit-scrollbar {
  width: 6px;
}

.answer-text::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.answer-text::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.answer-text::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 推荐面板容器（保留原有） */
.recommend-wrapper {
  width: 100%;
  box-sizing: border-box;
  margin-top: 20px;
  overflow: hidden;
}

/* 其他样式（保留原有） */
.answer-text h1,
.answer-text h2,
.answer-text h3,
.answer-text h4 {
  margin: 1.5em 0 0.8em;
  color: #2c3e50;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}

.answer-text ul,
.answer-text ol {
  margin: 1em 0;
  padding-left: 2em;
}

.answer-text li {
  margin: 0.5em 0;
}

.answer-text a {
  color: #42b983;
  text-decoration: none;
}

.answer-text a:hover {
  text-decoration: underline;
}

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

.loading {
  margin-top: 20px;
  padding: 20px;
  text-align: center;
  color: #666;
  background: #f5f5f5;
  border-radius: 4px;
}

/* 响应式调整（保留原有） */
@media (max-width: 768px) {
  .answer-text {
    max-height: 300px;
  }
  .recommend-wrapper {
    margin-top: 15px;
  }
}
</style>