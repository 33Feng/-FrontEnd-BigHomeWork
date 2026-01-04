<template>
  <div class="qa-panel-wrapper">
    <div class="qa-scroll-body">
      <div class="panel-header-row">
        <h2 class="panel-title">
          前端知识问答与推荐
          <span style="margin-left: 225px;">
          </span>
          前端知识随心测
        </h2>
        <!-- <h2 class="panel-question-title">
          
        </h2> -->
        <div 
          class="question-button" 
          @click="showKnowledgeQuiz = true" 
          title="开始测验"
        >
          
          <span>?</span>
        </div>
      </div>

      <div class="recommend-wrapper">
        <RecommendPanel
          :recommendations="recommendations"
          :history-recommendations="searchHistory"
          :current-entity="currentEntity"
          @delete-history="deleteHistoryItem"
        />
      </div>

      <div 
        class="answer-section" 
        v-if="(answer && !isLoading) || isLoading"
      >
        <div class="section-title">
          AI 回答
        </div>
        <div class="answer-bubble">
          <div v-if="isLoading" class="loading-in-card">
            <el-icon class="is-loading" size="20">
              <Loading />
            </el-icon>
            <span class="loading-text">
              <template v-if="answerMode === 'deep'">
                深度思考中，请稍候...
              </template>
              <template v-else>
                正在生成答案...
              </template>
            </span>
          </div>
          <div 
            v-else 
            class="answer-text" 
            v-html="answer"
          ></div>
        </div>
      </div>
    </div>

    <div class="input-dock-container">
      <div class="mode-switch-row">
        <span class="mode-label">
          模式：
        </span>
        <span 
          class="mode-item" 
          :class="{ active: answerMode === 'quick' }" 
          @click="answerMode = 'quick'; handleModeChange()"
        >
           快速
        </span>
        <span class="divider">
          |
        </span>
        <span 
          class="mode-item" 
          :class="{ active: answerMode === 'deep' }" 
          @click="answerMode = 'deep'; handleModeChange()"
        >
           深度
        </span>
        
        <span 
          v-if="currentEntity" 
          class="quick-ask-link" 
          @click="quickAsk"
        >
           提问「{{ currentEntity }}」
        </span>
      </div>

      <el-form @submit.prevent="submitQuestion" class="capsule-form">
        <div 
          class="capsule-input-box" 
          :class="{ focused: isInputFocused }"
        >
            <el-input
                v-model="question"
                placeholder="问点什么... (例如：Vue3新特性)"
                class="transparent-input"
                clearable
                @focus="handleInputFocus"
                @blur="handleInputBlur"
                @keyup.enter="submitQuestion"
            ></el-input>
            
            <button 
              class="send-btn" 
              @click="submitQuestion" 
              :disabled="isLoading"
            >
                 <el-icon><Position /></el-icon>
            </button>

             <transition name="fade">
               <div
                  v-if="showHistoryDropdown && searchHistory.length"
                  class="history-dropdown"
                  @mouseenter="isMouseInDropdown = true"
                  @mouseleave="isMouseInDropdown = false"
                >
                  <div class="dropdown-header">
                    搜索历史
                  </div>
                  <div
                    class="history-item"
                    v-for="(item, index) in searchHistory"
                    :key="index"
                    @click="selectHistoryItem(item)"
                  >
                    <span class="text-truncate">
                      {{ item }}
                    </span>
                    <el-icon class="delete-icon" @click.stop="deleteHistoryItem(index)">
                      <Close />
                    </el-icon>
                  </div>
                  <div class="clear-history" @click="clearAllHistory">
                    清除全部历史
                  </div>
                </div>
             </transition>
        </div>
      </el-form>
    </div>

    <div
      v-if="showKnowledgeQuiz"
      class="drag-modal"
      :style="{ top: `${modalTop}px`, left: `${modalLeft}px` }"
    >
      <div class="drag-modal-header" @mousedown="handleMouseDown">
        <span class="modal-title">
          前端知识小测验
        </span>
        <el-button type="text" size="small" @click="handleQuizClose">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>

      <div class="drag-modal-body">
        <div class="quiz-difficulty" v-if="!quizLoading">
          <span>
            题目难度：
          </span>
          <el-radio-group v-model="quizDifficulty" @change="onDifficultyChange" size="small">
            <el-radio-button label="easy">
              简单模式（概念区分）
            </el-radio-button>
            <el-radio-button label="hard">
              困难模式（深度思考）
            </el-radio-button>
          </el-radio-group>
        </div>

        <div v-if="quizLoading" class="quiz-loading-overlay">
          <div class="loading-content">
            <el-icon class="is-loading" size="24">
              <Loading />
            </el-icon>
            <span>
              正在生成题目...
            </span>
          </div>
        </div>

        <!-- 核心修改：增加滚动区域限制 -->
        <div v-if="hasQuizLoaded" class="quiz-content-wrapper">
          <div v-if="quizData && quizData.question && quizData.options && quizData.options.length === 4" class="quiz-content">
            <h3 class="quiz-question">
              {{ quizData.question }}
            </h3>
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

          <div v-else class="quiz-error">
            <p>
              无法加载题目，已为你提供默认题目
            </p>
            <div class="default-quiz">
              <h3 class="quiz-question">
                Vue3中ref和reactive的主要区别是什么？
              </h3>
              <div class="quiz-options">
                <el-radio-group v-model="selectedAnswer">
                  <el-radio label="ref用于基本类型，reactive用于引用类型" class="quiz-option">
                    ref用于基本类型，reactive用于引用类型
                  </el-radio>
                  <el-radio label="ref和reactive没有区别" class="quiz-option">
                    ref和reactive没有区别
                  </el-radio>
                  <el-radio label="ref只能在组合式API中使用，reactive只能在选项式API中使用" class="quiz-option">
                    ref只能在组合式API中使用，reactive只能在选项式API中使用
                  </el-radio>
                  <el-radio label="ref是响应式的，reactive不是" class="quiz-option">
                    ref是响应式的，reactive不是
                  </el-radio>
                </el-radio-group>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="drag-modal-footer">
        <el-button size="small" @click="handleQuizClose">
          关闭
        </el-button>
        <el-button size="small" type="primary" @click="submitAnswer">
          提交答案
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineEmits, defineProps, watch, onMounted, onUnmounted } from 'vue';
import { ElForm, ElInput, ElButton, ElMessage, ElRadioGroup, ElRadio, ElRadioButton, ElIcon } from 'element-plus';
import { Close, Loading, Position } from '@element-plus/icons-vue';
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
const isInputFocused = ref(false);

// 知识测验相关
const showKnowledgeQuiz = ref(false);
const quizData = ref(null);
const quizLoading = ref(false);
const selectedAnswer = ref('');
const quizDifficulty = ref('easy');
const generatedQuizQuestions = ref([]);
const hasQuizLoaded = ref(false);

// 拖拽相关响应式数据
const modalTop = ref(100);
const modalLeft = ref(200);
const isDragging = ref(false);
const startX = ref(0);
const startY = ref(0);

// 初始化
onMounted(() => {
  const savedHistory = localStorage.getItem('searchHistory');
  if (savedHistory) {
    searchHistory.value = JSON.parse(savedHistory);
  }
  const savedQuizQuestions = localStorage.getItem('generatedQuizQuestions');
  if (savedQuizQuestions) {
    generatedQuizQuestions.value = JSON.parse(savedQuizQuestions);
  }
});

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove);
  document.removeEventListener('mouseup', handleMouseUp);
});

const saveSearchHistory = () => {
  localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value));
};

const saveGeneratedQuizQuestions = () => {
  localStorage.setItem('generatedQuizQuestions', JSON.stringify(generatedQuizQuestions.value));
};

// 输入框聚焦逻辑
const handleInputFocus = () => {
    isInputFocused.value = true;
    showHistoryDropdown.value = true;
};

const handleInputBlur = () => {
  isInputFocused.value = false;
  blurTimeout.value = setTimeout(() => {
    if (!isMouseInDropdown.value) {
      showHistoryDropdown.value = false;
    }
  }, 200);
};

const selectHistoryItem = (item) => {
  question.value = item;
  showHistoryDropdown.value = false;
};

const deleteHistoryItem = (index) => {
  searchHistory.value.splice(index, 1);
  saveSearchHistory();
};

const clearAllHistory = () => {
  searchHistory.value = [];
  saveSearchHistory();
};

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
    const requestTimeout = answerMode.value === 'quick' ? 7000 : 120000;
    const res = await api.qa(
      {
        question: trimmedQuestion,
        mode: answerMode.value,
        stream: false
      },
      {
        timeout: requestTimeout,
        headers: { 'Content-Type': 'application/json' }
      }
    );

    const responseData = res.data || res;
    answer.value = responseData.answer || responseData.content || '';
    recommendations.value = responseData.recommendations || responseData.suggestions || [];
    mainEntity.value = (responseData.related_entities && responseData.related_entities[0]) || (recommendations.value[0]?.label || '');
    emit('update:mainEntity', mainEntity.value);

  } catch (error) {
    let errorMsg = '获取回答失败';
    if (error.code === 'ECONNABORTED') {
      errorMsg = '请求超时，请稍后重试';
    } else if (error.response?.data?.error?.message) {
      errorMsg = `API 错误：${error.response.data.error.message}`;
    } else if (error.response?.status === 401) {
      errorMsg = 'API 密钥无效，请检查配置';
    } else if (error.response?.status === 402) {
      errorMsg = 'API 额度不足，请充值后重试';
    } else if (error.response?.status === 403) {
      errorMsg = '无权限访问 API，请检查权限配置';
    }
    ElMessage.error(errorMsg);
    
    // 默认兜底
    answer.value = `<p>抱歉，暂时无法为你提供回答。</p>`;
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

const onDifficultyChange = () => {
  hasQuizLoaded.value = false;
  fetchRandomQuiz();
};

// 完整的测验题目生成逻辑
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
    // 加载完成：隐藏弹窗，显示内容
    quizLoading.value = false;
    hasQuizLoaded.value = true;
  }
};

// 优化的提交答案逻辑（答错时填充问题到输入框）
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

const handleQuizClose = () => {
  showKnowledgeQuiz.value = false;
  hasQuizLoaded.value = false;
};

// 拖拽逻辑
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

watch(() => showKnowledgeQuiz.value, (newVal) => {
    if (newVal) fetchRandomQuiz();
});
</script>

<style scoped>
/* 容器：垂直布局 */
.qa-panel-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  background: white;
}

/* 顶部内容滚动区 */
.qa-scroll-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 20px 20px;
  scroll-behavior: smooth;
}

/* 头部行 */
.panel-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0 10px 0;
  position: sticky;
  top: 0;
  background: white;
  z-index: 2;
}

.panel-title {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
  font-weight: 600;
}

.panel-question-title{
  text-align: end;
  margin: 0;
  padding: 0;
  font-size: 18px;
  color: #1e293b;
  font-weight: 600;
}

/* 问答按钮 */
.question-button {
  margin-left: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: #10B981;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(16, 185, 129, 0.3);
  transition: transform 0.2s;
}

.question-button:hover {
  transform: scale(1.1);
}

/* 推荐容器 */
.recommend-wrapper {
  margin-bottom: 20px;
}

/* 回答区域 */
.answer-section {
  margin-top: 10px;
  animation: fadeIn 0.3s ease;
}

.section-title {
  font-size: 13px;
  color: #94A3B8;
  margin-bottom: 6px;
  font-weight: 500;
}

/* 气泡样式 */
.answer-bubble {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 0 12px 12px 12px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
  color: #334155;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.loading-in-card {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748B;
  padding: 10px 0;
}

/* 底部输入停靠区 */
.input-dock-container {
  padding: 16px 20px 20px 20px;
  background: white;
  border-top: 1px solid #F1F5F9;
  z-index: 5;
}

.mode-switch-row {
  display: flex;
  align-items: center;
  font-size: 12px;
  margin-bottom: 12px;
  color: #64748B;
}

.mode-item {
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.mode-item.active {
  background: #EEF2FF;
  color: var(--primary-color);
  font-weight: 600;
}

.divider {
  margin: 0 8px;
  color: #CBD5E1;
}

.quick-ask-link {
  margin-left: auto;
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
  background: #F1F5F9;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.quick-ask-link:hover {
  background: #EEF2FF;
}

/* 胶囊输入框容器 */
.capsule-input-box {
  display: flex;
  align-items: center;
  border: 2px solid #E2E8F0;
  border-radius: 24px;
  padding: 4px 6px 4px 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  background: #FFFFFF;
}

.capsule-input-box.focused {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
}

/* Element Input 穿透 */
.transparent-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  padding: 0;
  background: transparent;
}

.transparent-input :deep(.el-input__inner) {
  font-size: 15px;
  color: #1E293B;
}

/* 发送按钮 */
.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.send-btn:hover {
  transform: scale(1.05);
  background: var(--primary-hover);
}

.send-btn:disabled {
  background: #CBD5E1;
  cursor: not-allowed;
}

/* 历史记录下拉 */
.history-dropdown {
  position: absolute;
  bottom: 115%;
  left: 0;
  right: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  border: 1px solid #E2E8F0;
  z-index: 100;
  max-height: 250px;
  overflow-y: auto;
}

.dropdown-header {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #94A3B8;
  background: #F8FAFC;
  border-bottom: 1px solid #F1F5F9;
}

.history-item {
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-size: 13px;
  color: #334155;
  transition: background 0.2s;
}

.history-item:hover {
  background: #F1F5F9;
  color: var(--primary-color);
}

.delete-icon {
  color: #CBD5E1;
  font-size: 14px;
}

.delete-icon:hover {
  color: #EF4444;
}

.clear-history {
  padding: 10px;
  text-align: center;
  color: #94A3B8;
  font-size: 12px;
  cursor: pointer;
  border-top: 1px solid #F1F5F9;
}

.clear-history:hover {
  color: var(--primary-color);
}

/* 测验弹窗 - 核心修改：响应式宽度 */
.drag-modal {
  position: fixed;
  /* 响应式宽度：最大90vw，最小300px，自适应中间宽度 */
  max-width: 90vw;
  width: 55%;
  min-width: 300px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  border: 1px solid #E2E8F0;
  z-index: 2000;
  overflow: hidden;
}

.drag-modal-header {
  padding: 12px 16px;
  background: #F8FAFC;
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: move;
}

.modal-title {
  font-weight: 600;
  font-size: 14px;
  color: #1E293B;
}

.drag-modal-body {
  padding: 20px;
  position: relative;
  min-height: 150px;
}

.quiz-difficulty {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

/* 核心修改：题目内容滚动区域限制 */
.quiz-content-wrapper {
  max-height: 220px; /* 固定最大高度 */
  overflow-y: auto;  /* 超出显示垂直滚动条 */
  padding-right: 8px; /* 给滚动条预留空间 */
  margin-top: 10px;
}

/* 滚动条美化（仅题目区域） */
.quiz-content-wrapper::-webkit-scrollbar {
  width: 6px;
}

.quiz-content-wrapper::-webkit-scrollbar-thumb {
  background: #E2E8F0;
  border-radius: 3px;
}

.quiz-content-wrapper::-webkit-scrollbar-thumb:hover {
  background: #94A3B8;
}

.quiz-question {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 16px;
  line-height: 1.5;
  word-wrap: break-word; /* 长题目自动换行 */
}

.quiz-option {
  display: flex;
  margin-bottom: 8px;
  white-space: normal; /* 长选项自动换行 */
  height: auto;
  padding: 6px 0;
  word-wrap: break-word; /* 确保选项文字不溢出 */
}

.drag-modal-footer {
  padding: 12px 16px;
  border-top: 1px solid #E2E8F0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  background: #F8FAFC;
}

.quiz-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滚动条美化 */
.qa-scroll-body::-webkit-scrollbar {
  width: 5px;
}

.qa-scroll-body::-webkit-scrollbar-thumb {
  background: #CBD5E1;
  border-radius: 4px;
}

.qa-scroll-body::-webkit-scrollbar-thumb:hover {
  background: #94A3B8;
}
</style>