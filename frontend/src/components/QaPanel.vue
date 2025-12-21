<template>
  <div class="qa-panel">
    <!-- 标题和知识问答按钮 -->
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
      <h2 style="margin: 0; margin-right: 10px;">前端知识随心测</h2>
      <div class="question-button" @click="showKnowledgeQuiz = true">
        <span>?</span>
      </div>
    </div>

    <!-- 自定义可拖拽浮层（替代原弹窗） -->
    <div
      v-if="showKnowledgeQuiz"
      class="drag-modal"
      :style="{ top: `${modalTop}px`, left: `${modalLeft}px` }"
    >
      <!-- 拖拽头部（仅头部可拖拽） -->
      <div class="drag-modal-header" @mousedown="handleMouseDown">
        <span class="modal-title">前端知识小测验</span>
        <el-button type="text" size="small" @click="handleQuizClose">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>

      <!-- 浮层内容区域：相对定位，用于承载加载弹窗和内容 -->
      <div class="drag-modal-body">
        <!-- 难度选择区域 -->
        <div class="quiz-difficulty" v-if="!quizLoading">
          <span>题目难度：</span>
          <el-radio-group v-model="quizDifficulty" @change="onDifficultyChange">
            <el-radio label="easy">简单模式（概念区分）</el-radio>
            <el-radio label="hard">困难模式（深度思考）</el-radio>
          </el-radio-group>
        </div>

        <!-- 加载弹窗：覆盖在内容框上层，仅在加载中显示 -->
        <div v-if="quizLoading" class="quiz-loading-overlay">
          <div class="loading-content">
            <el-icon size="24" style="margin-right: 8px;"><Loading /></el-icon>
            <span>正在生成题目，请稍候...</span>
          </div>
        </div>

        <!-- 内容区域：仅在加载完成后显示（题目/错误） -->
        <div v-if="hasQuizLoaded" class="quiz-content-wrapper">
          <!-- 题目内容：增加非空判断，确保数据存在时才渲染 -->
          <div v-if="quizData && quizData.question && quizData.options.length" class="quiz-content">
            <h3 class="quiz-question">{{ quizData.question }}</h3>
            <div class="quiz-options">
              <el-radio-group v-model="selectedAnswer">
                <el-radio
                  v-for="(option, index) in quizData.options"
                  :key="index"
                  :label="option"
                  class="quiz-option"
                >
                  {{ option }}
                </el-radio>
              </el-radio-group>
            </div>
          </div>

          <!-- 错误/空数据处理：更友好的提示 -->
          <div v-else class="quiz-error">
            <p>无法加载题目，已为你提供默认题目</p>
            <!-- 默认题目：确保即使加载失败也有内容显示 -->
            <div class="default-quiz">
              <h3 class="quiz-question">Vue3中ref和reactive的主要区别是什么？</h3>
              <div class="quiz-options">
                <el-radio-group v-model="selectedAnswer">
                  <el-radio label="ref用于基本类型，reactive用于引用类型" class="quiz-option">ref用于基本类型，reactive用于引用类型</el-radio>
                  <el-radio label="ref和reactive没有区别" class="quiz-option">ref和reactive没有区别</el-radio>
                  <el-radio label="ref只能在组合式API中使用，reactive只能在选项式API中使用" class="quiz-option">ref只能在组合式API中使用，reactive只能在选项式API中使用</el-radio>
                  <el-radio label="ref是响应式的，reactive不是" class="quiz-option">ref是响应式的，reactive不是</el-radio>
                </el-radio-group>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 浮层底部按钮 -->
      <div class="drag-modal-footer">
        <el-button @click="handleQuizClose">关闭</el-button>
        <el-button type="primary" @click="submitAnswer">提交答案</el-button>
      </div>
    </div>

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

    <!-- 回答展示区域：整合加载状态到显示框内 -->
    <div class="answer-container" v-if="(answer && !isLoading) || isLoading">
      <h3>回答：</h3>
      <el-card>
        <!-- 加载中状态 -->
        <div v-if="isLoading" class="loading-in-card">
          <el-icon size="20" style="margin-right: 8px;"><Loading /></el-icon>
          <template v-if="answerMode === 'deep'">深度思考中，请稍候（最长120秒）...</template>
          <template v-else>正在生成答案，请稍候（5-7秒）...</template>
        </div>
        <!-- 回答内容 -->
        <div v-else class="answer-text" v-html="answer"></div>
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
import { ref, defineEmits, defineProps, watch, onMounted, onUnmounted } from 'vue';
import { ElForm, ElFormItem, ElInput, ElButton, ElCard, ElMessage, ElRadioGroup, ElRadio, ElIcon } from 'element-plus';
import { Close, Loading } from '@element-plus/icons-vue'; // 引入Loading图标
// 引入封装的API
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
const answerMode = ref('quick');
// 搜索历史相关
const searchHistory = ref([]);
const showHistoryDropdown = ref(false);
const isMouseInDropdown = ref(false);
const blurTimeout = ref(null);

// 知识测验相关
const showKnowledgeQuiz = ref(false);
const quizData = ref(null);
const quizLoading = ref(false);
const selectedAnswer = ref('');
// 题目难度选择（easy:简单/概念区分，hard:困难/深度思考）
const quizDifficulty = ref('easy');
// 存储已生成的题目，避免重复（本地存储持久化）
const generatedQuizQuestions = ref([]);
// 标记题目是否已加载完成（用于控制弹窗仅首次/重新触发时出现）
const hasQuizLoaded = ref(false);

// 拖拽相关响应式数据
const modalTop = ref(100); // 浮层初始顶部位置
const modalLeft = ref(200); // 浮层初始左侧位置
const isDragging = ref(false); // 是否正在拖拽
const startX = ref(0); // 拖拽起始X坐标
const startY = ref(0); // 拖拽起始Y坐标

// 初始化时从本地存储加载数据
onMounted(() => {
  // 加载搜索历史
  const savedHistory = localStorage.getItem('searchHistory');
  if (savedHistory) {
    searchHistory.value = JSON.parse(savedHistory);
  }
  // 加载已生成的题目列表（避免重复题目）
  const savedQuizQuestions = localStorage.getItem('generatedQuizQuestions');
  if (savedQuizQuestions) {
    generatedQuizQuestions.value = JSON.parse(savedQuizQuestions);
  }
});

// 清理鼠标事件监听
onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove);
  document.removeEventListener('mouseup', handleMouseUp);
});

// 保存搜索历史到本地存储
const saveSearchHistory = () => {
  localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value));
};

// 保存已生成题目到本地存储
const saveGeneratedQuizQuestions = () => {
  localStorage.setItem('generatedQuizQuestions', JSON.stringify(generatedQuizQuestions.value));
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

// 提交问题
const submitQuestion = async () => {
  const trimmedQuestion = question.value.trim();
  if (!trimmedQuestion) {
    ElMessage.warning('请输入问题！');
    return;
  }

  // 搜索历史处理逻辑
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
    // 根据模式设置超时时间
    const requestTimeout = answerMode.value === 'quick' ? 7000 : 120000;
    // 调用API
    const res = await api.qa(
      {
        question: trimmedQuestion,
        mode: answerMode.value,
        stream: false
      },
      {
        timeout: requestTimeout,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    const responseData = res.data || res;
    answer.value = responseData.answer || responseData.content || '';
    recommendations.value = responseData.recommendations || responseData.suggestions || [];
    mainEntity.value = (responseData.related_entities && responseData.related_entities[0]) || (recommendations.value[0]?.label || '');
    emit('update:mainEntity', mainEntity.value);

  } catch (error) {
    let errorMsg = '';
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      errorMsg = `${answerMode.value === 'quick' ? '快速回答超时' : '深度思考超时'}，请稍后重试`;
    } else if (error.response?.status === 401) {
      errorMsg = 'API 密钥无效，请检查配置';
    } else if (error.response?.status === 402) {
      errorMsg = 'API 额度不足，请充值后重试';
    } else if (error.response?.status === 403) {
      errorMsg = '无权限访问 API，请检查权限配置';
    } else if (error.response?.data?.error?.message) {
      errorMsg = `API 错误：${error.response.data.error.message}`;
    } else {
      errorMsg = '获取回答失败：' + (error.message || '未知错误');
    }
    ElMessage.error(errorMsg);

    // 错误时显示默认内容
    answer.value = `<p>抱歉，暂时无法为你提供回答，请稍后重试。</p>`;
    recommendations.value = [
      { label: 'Vue3', desc: '渐进式JavaScript框架，支持Composition API', weight: 5 },
      { label: 'Vite', desc: '新一代前端构建工具，极速冷启动', weight: 4 },
      { label: 'TypeScript', desc: '强类型JavaScript超集', weight: 4 },
    ];
  } finally {
    isLoading.value = false;
    showHistoryDropdown.value = false;
    clearTimeout(blurTimeout.value);
  }
};

// 重置表单
const resetForm = () => {
  question.value = '';
  answer.value = '';
  recommendations.value = [];
  mainEntity.value = '';
  emit('update:mainEntity', '');
};

// 快速提问
const quickAsk = () => {
  if (props.currentEntity) {
    question.value = `${props.currentEntity}相关知识有哪些？`;
    submitQuestion();
  }
};

// 监听当前实体变化
watch(
  () => props.currentEntity,
  (newEntity) => {
    if (newEntity && !question.value.trim()) {
      question.value = `${newEntity}相关知识有哪些？`;
    }
  },
  { immediate: true }
);

// 难度切换时重新加载题目（重置状态，显示弹窗）
const onDifficultyChange = () => {
  // 重置加载状态，重新显示弹窗
  hasQuizLoaded.value = false;
  fetchRandomQuiz();
};

// 知识测验相关方法：优化解析逻辑，确保题目正常显示
const fetchRandomQuiz = async () => {
  // 开始加载：显示弹窗，隐藏内容
  quizLoading.value = true;
  hasQuizLoaded.value = false;

  try {
    // 根据难度生成不同的Prompt要求
    let difficultyPrompt = '';
    if (quizDifficulty.value === 'easy') {
      // 简单模式：概念区分类题目
      difficultyPrompt = `1. 题目类型：仅生成前端**概念区分/定义类**题目（例如：Vue2与Vue3的核心区别、ref与reactive的区别、let与var的区别等）；
2. 难度要求：题目简单，侧重基础概念的识别和区分，选项差异明显但仍有一定迷惑性；`;
    } else {
      // 困难模式：深度思考类题目
      difficultyPrompt = `1. 题目类型：仅生成前端**深度思考/原理类**题目（例如：Vue3的响应式原理、Vite的构建优化原理、浏览器事件循环的底层逻辑等）；
2. 难度要求：题目困难，侧重底层原理、复杂场景应用和逻辑分析，选项具有强迷惑性；`;
    }

    // 优化prompt：明确要求JSON格式，减少解析问题
    const prompt = `请严格按照以下JSON格式生成一个前端开发的选择题，不要添加任何多余内容（包括注释、markdown、说明文字）：
{
  "question": "前端相关的问题内容",
  "options": ["选项1", "选项2", "选项3", "选项4"],
  "correctAnswer": "正确选项的完整内容"
}
要求：
${difficultyPrompt}
3. 知识领域：JavaScript、HTML/CSS、Vue3、React Hooks、Vite、TypeScript、浏览器原理、性能优化、前端安全中随机选一个；
4. 题目不能与已生成题目重复（已生成：${generatedQuizQuestions.value.join('，') || '无'}）；
5. 只有1个正确答案，选项固定4个；
6. 必须返回标准JSON，不能有任何多余字符。`;

    // 调用大模型：使用深度模式+30秒超时
    const res = await api.qa(
      {
        question: prompt,
        mode: "deep",
        stream: false
      },
      {
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    // 优化JSON解析逻辑：增加多层容错处理
    let responseText = res.data.answer || res.data.content || '';
    // 去除首尾多余字符（如空格、换行、markdown代码块）
    responseText = responseText.replace(/^```json|```$/g, '').trim();
    responseText = responseText.replace(/^\s+|\s+$/g, '');

    // 尝试解析JSON
    let quizResult = null;
    try {
      quizResult = JSON.parse(responseText);
    } catch (e) {
      // 解析失败时，尝试提取JSON片段
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        quizResult = JSON.parse(jsonMatch[0]);
      } else {
        throw new Error("未找到有效的JSON数据");
      }
    }

    // 验证数据完整性
    if (!quizResult.question || !quizResult.options || quizResult.options.length !== 4 || !quizResult.correctAnswer) {
      throw new Error("题目数据不完整");
    }

    quizData.value = quizResult;
    // 存储题目，避免重复
    generatedQuizQuestions.value.push(quizData.value.question);
    if (generatedQuizQuestions.value.length > 20) {
      generatedQuizQuestions.value.shift();
    }
    saveGeneratedQuizQuestions();
    selectedAnswer.value = '';

  } catch (error) {
    console.error('获取题目失败:', error);
    const errorMsg = error.code === 'ECONNABORTED' ? '题目生成超时，请稍后重试' : '获取题目失败，将显示默认题目';
    ElMessage.warning(errorMsg);
    quizData.value = null; // 置空触发默认题目显示

  } finally {
    // 加载完成：隐藏弹窗，显示内容（弹窗不再重复出现）
    quizLoading.value = false;
    hasQuizLoaded.value = true;
  }
};

// 提交答案：答错时填充问题到输入框（保留原有逻辑）
const submitAnswer = () => {
  if (!selectedAnswer.value) {
    ElMessage.warning('请选择一个答案');
    return;
  }

  // 处理默认题目和接口返回题目的答案验证
  const correctAnswer = quizData.value?.correctAnswer || "ref用于基本类型，reactive用于引用类型";
  if (selectedAnswer.value === correctAnswer) {
    ElMessage.success('哇，你真棒！');
  } else {
    ElMessage.info('再好好想想哦');
    // 填充问题到输入框（优先使用接口返回的问题，否则用默认问题）
    question.value = quizData.value?.question || "Vue3中ref和reactive的主要区别是什么？";
  }
};

// 处理浮层关闭：重置状态，下次打开时重新加载
const handleQuizClose = () => {
  showKnowledgeQuiz.value = false;
  // 重置加载状态，下次打开浮层时重新显示弹窗
  hasQuizLoaded.value = false;
};

// 拖拽相关方法（保留原有逻辑）
const handleMouseDown = (e) => {
  isDragging.value = true;
  startX.value = e.clientX;
  startY.value = e.clientY;
  const currentTop = modalTop.value;
  const currentLeft = modalLeft.value;

  const handleMouseMove = (e) => {
    if (isDragging.value) {
      const dx = e.clientX - startX.value;
      const dy = e.clientY - startY.value;
      modalTop.value = currentTop + dy;
      modalLeft.value = currentLeft + dx;
    }
  };

  const handleMouseUp = () => {
    isDragging.value = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
};

// 当浮层显示时触发题目加载（首次/重新打开时）
watch(
  () => showKnowledgeQuiz.value,
  (newVal) => {
    if (newVal) {
      fetchRandomQuiz();
    }
  }
);
</script>

<style scoped>
.qa-panel {
  margin-bottom: 20px;
  width: 100%;
  box-sizing: border-box;
  padding: 0;
}

/* 问号按钮样式 */
.question-button {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: #67C23A;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.question-button:hover {
  transform: scale(1.1);
  background-color: #52c41a;
}

/* 自定义可拖拽浮层样式 */
.drag-modal {
  position: fixed;
  width: 90%;
  max-width: 600px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 99999;
  user-select: none;
}

/* 拖拽头部样式 */
.drag-modal-header {
  padding: 12px 20px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: move;
}

.modal-title {
  font-weight: bold;
  color: #303133;
  font-size: 16px;
}

/* 浮层内容区域样式 */
.drag-modal-body {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
  /* 相对定位，用于承载绝对定位的加载弹窗 */
  position: relative;
  min-height: 200px; /* 保证内容区域有基础高度 */
}

/* 测验难度选择样式 */
.quiz-difficulty {
  margin-bottom: 15px;
  padding: 10px 0;
  border-bottom: 1px solid #e4e7ed;
}

/* 加载弹窗：覆盖在内容框上层，绝对定位 */
.quiz-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10; /* 确保在内容上层 */
}

.loading-content {
  display: flex;
  align-items: center;
  color: #606266;
  font-size: 16px;
}

/* 内容区域：加载完成后显示 */
.quiz-content-wrapper {
  position: relative;
  z-index: 1; /* 低于加载弹窗 */
}

/* 测验内容样式 */
.quiz-content {
  margin-top: 10px;
  padding: 10px 0;
}

.quiz-question {
  margin-bottom: 20px;
  color: #303133;
  font-size: 16px;
  line-height: 1.6;
  word-break: break-all;
}

.quiz-options {
  margin-bottom: 10px;
}

.quiz-option {
  margin-bottom: 10px;
  display: block;
  word-break: break-all;
}

/* 错误提示和默认题目样式 */
.quiz-error {
  padding: 20px;
  text-align: center;
  color: #F56C6C;
}

.default-quiz {
  margin-top: 15px;
  text-align: left;
  color: #303133;
}

/* 浮层底部按钮样式 */
.drag-modal-footer {
  padding: 12px 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 搜索容器和历史下拉样式 */
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

/* 回答容器样式 */
.answer-container {
  margin-top: 15px;
  width: 100%;
}

/* 回答框内的加载样式 */
.loading-in-card {
  padding: 20px;
  text-align: center;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 100px;
}

.answer-text {
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px;
  line-height: 1.6;
  word-break: break-all;
}

/* 滚动条样式优化 */
.answer-text::-webkit-scrollbar,
.drag-modal-body::-webkit-scrollbar {
  width: 6px;
}

.answer-text::-webkit-scrollbar-track,
.drag-modal-body::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.answer-text::-webkit-scrollbar-thumb,
.drag-modal-body::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.answer-text::-webkit-scrollbar-thumb:hover,
.drag-modal-body::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 推荐面板容器 */
.recommend-wrapper {
  width: 100%;
  box-sizing: border-box;
  margin-top: 20px;
  overflow: hidden;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .quiz-question {
    font-size: 14px;
  }

  .quiz-option {
    font-size: 14px;
  }

  .drag-modal {
    width: 95%;
    max-width: none;
  }
}
</style>