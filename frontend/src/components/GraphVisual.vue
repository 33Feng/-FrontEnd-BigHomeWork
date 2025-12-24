<template>
  <div class="graph-wrapper">
    <div class="float-panel top-left">
      <transition name="fade">
        <el-button 
          v-if="nodeHistory.length > 1"
          circle
          class="glass-btn back-btn" 
          @click="backToPreviousNode" 
          title="返回上级"
        >
            <el-icon><ArrowLeft /></el-icon>
        </el-button>
      </transition>
      
      <div class="search-capsule glass-panel">
         <el-input
          v-model="searchEntity"
          placeholder="搜索节点..."
          clearable
          @keyup="handleInputKeyup" 
          class="transparent-input"
         >
           <template #prefix>
             <el-icon class="search-icon"><Search /></el-icon>
           </template>
         </el-input>
         <div class="divider-v"></div>
         <el-button link type="primary" @click="handleSearch" class="search-btn">Go</el-button>
      </div>
    </div>

    <div class="float-panel top-right glass-panel toolbar-group">
        <div class="view-switch">
            <span 
              class="switch-item" 
              :class="{ active: viewMode === 'graph' }" 
              @click="toggleViewMode"
            >
              图谱
            </span>
            <span 
              class="switch-item" 
              :class="{ active: viewMode === 'terms' }" 
              @click="toggleViewMode"
            >
              列表
            </span>
        </div>

        <div class="divider-v"></div>

        <el-tooltip content="显示全部" placement="bottom">
            <el-button circle link class="tool-btn" @click="showAllGraph">
              <el-icon><Connection /></el-icon>
            </el-button>
        </el-tooltip>
        
        <el-dropdown trigger="click">
            <el-button circle link class="tool-btn">
              <el-icon><Download /></el-icon>
            </el-button>
            <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :icon="Picture" @click="exportGraphImage">导出图片 (.png)</el-dropdown-item>
                  <el-dropdown-item :icon="Download" @click="exportGraphJSON">导出 JSON 数据</el-dropdown-item>
                </el-dropdown-menu>
            </template>
        </el-dropdown>

        <el-tooltip content="全屏模式" placement="bottom">
          <el-button circle link class="tool-btn" @click="toggleFullScreen">
              <el-icon><FullScreen /></el-icon>
          </el-button>
        </el-tooltip>
        
        <el-tooltip content="重新加载" placement="bottom">
          <el-button circle link class="tool-btn" @click="initGraph">
              <el-icon><RefreshRight /></el-icon>
          </el-button>
        </el-tooltip>
    </div>

    <div v-if="loading" class="center-loading">
       <div class="spinner"></div>
       <div class="loading-text">
         {{ currentEntity ? `加载「${currentEntity}」...` : '计算布局中...' }}
       </div>
    </div>

    <div 
        v-show="viewMode === 'graph'"
        ref="graphRef" 
        class="graph-canvas"
        :class="{ 'fullscreen-mode': isFullScreen }"
    ></div>

    <div v-show="viewMode === 'terms'" class="terms-wrapper">
         <div class="terms-scroll-area">
             <div v-if="loading" class="terms-loading-skeleton">
                <div class="skeleton-row" v-for="i in 5" :key="i"></div>
             </div>
             
             <div v-else-if="termsData.edges.length > 0" class="terms-grid">
                <div 
                  v-for="(edge, index) in termsData.edges" 
                  :key="`${edge.source}-${edge.relation}-${edge.target}-${index}`" 
                  class="term-card"
                >
                    <div class="term-content">
                        <a 
                          :href="getBaiduLink(edge.source)" 
                          target="_blank" 
                          class="node-pill source"
                          :title="edge.source"
                        >
                          {{ edge.source }}
                        </a>
                        
                        <div class="relation-arrow">
                           <span class="line"></span>
                           <span class="rel-text">{{ edge.relation }}</span>
                           <span class="arrow-head">►</span>
                        </div>
                        
                        <a 
                          :href="getBaiduLink(edge.target)" 
                          target="_blank" 
                          class="node-pill target"
                          :title="edge.target"
                        >
                          {{ edge.target }}
                        </a>
                    </div>
                    
                    <el-button 
                        type="primary" link size="small" 
                        class="detail-btn"
                        @click="handleTermClick(edge.source === currentEntity ? edge.target : edge.source)"
                        :disabled="!(edge.source === currentEntity ? edge.target : edge.source) || !hasSubordinateContent(edge.source === currentEntity ? edge.target : edge.source, termsData.edges)"
                    >
                        查看详情
                    </el-button>
                </div>
             </div>
             <el-empty v-else description="无关联实体关系" :image-size="80" />
         </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted, watch,  shallowRef, markRaw } from 'vue';
import { Network, DataSet } from 'vis-network/standalone';
import { ElButton, ElMessage, ElInput, ElIcon } from 'element-plus';
// 引入新需要的图标
import { FullScreen, Picture, Download, ArrowDown, Loading, ArrowLeft, Search, RefreshRight, Connection } from '@element-plus/icons-vue';
import { api } from '../api/index';

// --- 1. 智能颜色映射 (完全恢复原有逻辑) ---
const getRelationColor = (relation) => {
  const rel = (relation || '').trim();
  if (!rel) return '#A9A9A9';
  
  // 【橙色系】版本、历史、时间相关
  if (['版本', '历史', '旧', 'Time'].some(k => rel.includes(k))) return '#E6A23C'; 
  // 【红色系】工具、框架、工程化、生态相关
  if (['框架', '工具', '编辑器', '管理', '容器', '部署', '规范', 'CI/CD', '处理器', '生态', '调试', '服务', 'Environment'].some(k => rel.includes(k))) return '#F56C6C';
  // 【青色系】性能、网络、安全、浏览器环境相关
  if (['优化', '性能', '加载', '渲染', '安全', '权限', '协议', '请求', '异步', '错误', '异常', '网络', 'Web', '客户端', '服务端', '浏览器', 'HTTP', 'DNS'].some(k => rel.includes(k))) return '#00BCD4';
  // 【金色/黄色系】事件、交互、通信、路由
  if (['事件', '通信', '路由', '交互', '监听', '导航', '行为', 'DOM'].some(k => rel.includes(k))) return '#FFD700'; 
  // 【紫色系】高阶概念、底层机制、模块化、抽象
  if (['机制', '原理', '模式', '环境', '作用域', '上下文', '模块', '依赖', '继承', '超集', '代理', '反射', '型变', '约束'].some(k => rel.includes(k))) return '#9C27B0';
  // 【绿色系】语法细节、代码元素、属性、样式
  if (['属性', '标签', '选择器', '样式', '语法', '指令', '方法', '函数', '声明', '规则', '类型', '参数', '变量', '操作', '钩子', '元素', '插槽', '装饰器', '泛型', '接口', '枚举', '数组', '对象', '字符串', '组件', '值'].some(k => rel.includes(k))) return '#67C23A';
  // 【蓝色系】核心结构、定义、标准、顶层分类 
  if (['核心', '组成', '环节', '领域', '标准', '组织', '定义', '概念', '维度', '进阶', '方案', '优势'].some(k => rel.includes(k))) return '#409EFF';
  
  return '#FFC100';
};

// 生成百度百科链接
const getBaiduLink = (text) => {
  const placeholder = '无文本内容';
  if (!text || text === placeholder) {
    return 'javascript:void(0);'; // 空内容不跳转
  }
  return `https://baike.baidu.com/item/${encodeURIComponent(text.trim())}`;
};

// 接收父组件传递的核心实体
const props = defineProps({
  mainEntity: {
    type: String,
    default: ''
  },
  height: {
    type: String,
    default: '550px'
  }
});

// 向父组件发送当前选中的实体和推荐数据请求
const emit = defineEmits(['update:currentEntity', 'graph-loaded', 'getRecommendData']);

// 响应式数据
const graphRef = ref(null);
const network = shallowRef(null); // 图谱实例
const loading = ref(false); // 加载状态
const searchEntity = ref('');
const currentEntity = ref('');
const isFullScreen = ref(false);
const viewMode = ref('graph'); // 视图模式：graph/terms
const termsData = ref({ nodes: [], edges: [] }); // 词条数据
const initRetryCount = ref(0); // 初始化重试计数器
const isShowingFull = ref(false); // 是否显示全部节点
const nodeHistory = ref([]); // 节点点击历史记录（用于回溯）
const MAX_DEFAULT_NODES = 15; // 初始默认显示最大节点数
const EMPTY_TEXT_PLACEHOLDER = '无文本内容'; // 空文本占位符
const EMPTY_RELATION_PLACEHOLDER = '无关联'; // 空关系占位符

// 格式化空文本
const formatEmptyText = (text, defaultText = EMPTY_TEXT_PLACEHOLDER, isRelation = false) => {
  if (text === undefined || text === null) return defaultText;
  const trimmedText = String(text).trim();
  if (trimmedText === '') return defaultText;
  if (isRelation) {
    const validCharRegex = /[\u4e00-\u9fa5a-zA-Z0-9]/;
    return validCharRegex.test(trimmedText) ? trimmedText : defaultText;
  }
  const isInvalid = /^[\d\s\W]+$/.test(trimmedText) || /[\x00-\x1F\x7F]/.test(trimmedText) || /[\uFFFD]/.test(trimmedText);
  return isInvalid ? defaultText : trimmedText;
};

// 切换视图模式
const toggleViewMode = () => {
  const oldMode = viewMode.value;
  viewMode.value = viewMode.value === 'graph' ? 'terms' : 'graph';
   
  if (viewMode.value === 'terms') {
    loadTermsData(currentEntity.value || props.mainEntity);
  } else if (viewMode.value === 'graph' && oldMode === 'terms') {
    if (graphRef.value) {
      graphRef.value.innerHTML = '';
    }
    initGraph(currentEntity.value || props.mainEntity);
  }
};

// 检查节点是否有下属关联内容
const hasSubordinateContent = (entity, edges) => {
  if (!entity || entity === EMPTY_TEXT_PLACEHOLDER) return false;
  return edges.some(edge => edge.source === entity);
};

// 回溯到上一个节点（支持回溯到初始状态）
const backToPreviousNode = () => {
  if (nodeHistory.value.length <= 1) return;
  // 移除当前节点，获取上一个节点
  nodeHistory.value.pop();
  const prevEntity = nodeHistory.value[nodeHistory.value.length - 1];
   
  searchEntity.value = prevEntity;
  currentEntity.value = prevEntity;
  emit('update:currentEntity', prevEntity);
  emit('getRecommendData', prevEntity);
   
  if (viewMode.value === 'graph') {
    initGraph(prevEntity);
  } else {
    loadTermsData(prevEntity);
  }
};

// 销毁图谱实例
const destroyNetwork = () => {
  if (network.value) {
    try {
      network.value.destroy();
    } catch (e) {
      console.warn('销毁图谱实例警告：', e);
    } finally {
      network.value = null;
    }
  }
};

// 检查容器有效性
const checkContainerValidity = () => {
  if (!graphRef.value) {
    // ElMessage.error('图谱容器不存在');
    return false;
  }
  graphRef.value.style.display = 'none';
  graphRef.value.offsetHeight;
  graphRef.value.style.display = 'block';
  const rect = graphRef.value.getBoundingClientRect();
  if (rect.width <= 10 || rect.height <= 10) {
    graphRef.value.style.minWidth = '300px';
    graphRef.value.style.minHeight = '300px';
    const newRect = graphRef.value.getBoundingClientRect();
    return newRect.width > 10 && newRect.height > 10;
  }
  return true;
};

// --- 核心：初始化图谱 (完全恢复原有逻辑) ---
const initGraph = async (targetEntity = '', forceFull = false) => {
  if (viewMode.value !== 'graph') return;
   
  try {
    loading.value = true;
    destroyNetwork();
    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 300));

    // 1. 检查容器
    if (!checkContainerValidity()) {
      if (initRetryCount.value < 3) {
        initRetryCount.value++;
        setTimeout(() => initGraph(targetEntity, forceFull), 800);
        return;
      }
      loading.value = false;
      return;
    }
    initRetryCount.value = 0;

    // 2. 准备实体参数
    let entity = typeof targetEntity === 'string' ? targetEntity.trim() : '';
    entity = targetEntity === '' ? '' : (entity || currentEntity.value || props.mainEntity);
    entity = formatEmptyText(entity);
    currentEntity.value = entity;
    emit('update:currentEntity', entity);

    // 3. 获取数据
    let res;
    try {
      if (entity && entity !== EMPTY_TEXT_PLACEHOLDER) {
        // 加载指定实体的数据
        res = await api.getGraphDataByEntity(entity);
        isShowingFull.value = forceFull;
      } else if (isFullScreen.value || forceFull) {
        // 全屏模式或强制全屏：加载全量数据
        res = await api.getFullGraphData ? await api.getFullGraphData() : await api.getGraphData();
        isShowingFull.value = true;
      } else {
        // 默认加载核心节点
        res = await api.getGraphData();
        isShowingFull.value = false;
      }
    } catch (apiError) {
      ElMessage.error(`数据请求失败：${apiError.message}`);
      loading.value = false;
      return;
    }

    const { nodes = [], edges = [] } = res?.data || {};

    // 4. 数据预处理
    const rawEdges = Array.isArray(edges) ? edges.map(edge => ({
      source: formatEmptyText(edge.source || edge.from),
      target: formatEmptyText(edge.target || edge.to),
      relation: formatEmptyText(edge.relation || edge.label, EMPTY_RELATION_PLACEHOLDER, true),
      weight: edge.weight || 1
    })).filter(edge => 
      edge.source && edge.target && edge.relation && 
      edge.source !== edge.target && 
      edge.source !== EMPTY_TEXT_PLACEHOLDER && 
      edge.target !== EMPTY_TEXT_PLACEHOLDER
    ) : [];

    // 5. 颜色映射表 (目标节点跟随边染色)
    const nodeColorMap = new Map();
    rawEdges.forEach(edge => {
      if (!nodeColorMap.has(edge.target)) {
        nodeColorMap.set(edge.target, getRelationColor(edge.relation));
      }
    });

    // 6. 生成节点数据
    const allNodeLabels = new Set();
    rawEdges.forEach(edge => {
      allNodeLabels.add(edge.source);
      allNodeLabels.add(edge.target);
    });

    // 检查每个节点是否有下属节点
    const nodeHasSubordinates = new Map();
    Array.from(allNodeLabels).forEach(label => {
      nodeHasSubordinates.set(label, rawEdges.some(edge => edge.source === label));
    });

    // 【关键】：恢复原有的 validNodes 逻辑
    let validNodes = Array.from(allNodeLabels)
      .map(label => {
        // 确定节点颜色：有下属节点使用映射颜色，否则使用灰色
        const hasSubordinates = nodeHasSubordinates.get(label);
        const baseColor = hasSubordinates ? 
          (nodeColorMap.get(label) || '#409EFF') : '#CCCCCC';
         
        return {
          id: label,
          label: label,
          color: {
            background: baseColor,
            border: hasSubordinates ? shadeColor(baseColor, -30) : '#AAAAAA',
            highlight: hasSubordinates ? shadeColor(baseColor, -20) : '#BBBBBB'
          },
          shape: 'box', // 改为box形状使文字显示在内部
          size: Math.max(label.length * 8, 30), // 根据文字长度动态调整大小
          font: { 
            color: getContrastColor(baseColor), // 确保文字与背景颜色对比明显
            size: 14,
            face: 'Arial'
          },
          hasSubordinates: hasSubordinates // 记录是否有下属节点
        };
      })
      .filter(node => node.label !== EMPTY_TEXT_PLACEHOLDER);

    // 限制节点数量 (非全屏时)
    if (!entity || entity === EMPTY_TEXT_PLACEHOLDER) {
      if (!isFullScreen.value && !forceFull && !isShowingFull.value) {
        validNodes = validNodes.slice(0, MAX_DEFAULT_NODES);
        ElMessage.info(`当前显示前12个关键节点，全屏模式下显示全部`);
      }
    }

    if (validNodes.length === 0) validNodes.push({ 
      id: `node_empty`, 
      label: entity, 
      shape: 'box', 
      size: 30, 
      color: { background: '#67C23A', border: '#529B2E' },
      hasSubordinates: false
    });

    const nodeLabelMap = new Map(validNodes.map(n => [n.label, n.id]));

    // 7. 生成边数据
    const validEdges = rawEdges
      .filter(edge => nodeLabelMap.has(edge.source) && nodeLabelMap.has(edge.target))
      .map(edge => {
        const edgeColor = getRelationColor(edge.relation);
        return {
          from: nodeLabelMap.get(edge.source),
          to: nodeLabelMap.get(edge.target),
          label: edge.relation,
          width: Math.min(1.5 + (edge.weight || 0) / 5, 4), // 综合了权重逻辑
          color: { color: edgeColor, highlight: edgeColor, hover: edgeColor, inherit: false, opacity: 0.8 },
          arrows: { to: { enabled: true, scaleFactor: 0.5 } }
        };
      });

    // 8. 配置项 - 优化物理引擎 (恢复原有参数)
    const isLargeGraph = validNodes.length > 100;
    const options = {
      nodes: { 
        font: { size: 14, face: 'Arial' }, 
        shape: 'box', // 统一设置为box形状
        shadow: isLargeGraph ? false : true,
        shapeProperties: {
          interpolation: false 
        },
        scaling: {
          label: {
            enabled: true,
            drawThreshold: 8,
            maxVisible: 20 
          }
        }
      }, 
      edges: { 
        font: { size: 12, align: 'middle', color: '#888' },
        // 大图强制直线
        smooth: isLargeGraph ? false : { 
          type: 'dynamic', 
          roundness: 0.5 
        }
      },
      physics: {
        enabled: true,
        solver: 'barnesHut',
        barnesHut: {
          gravitationalConstant: isLargeGraph ? -30000 : -2500, // 调整引力
          centralGravity: 0.3,
          springLength: isLargeGraph ? 120 : 200, // 增加弹簧长度使布局更宽松
          springConstant: 0.05, // 增加弹簧强度
          damping: 0.15, // 增加阻尼使系统更快稳定
          avoidOverlap: 0.5 // 增加避免重叠的力度
        },
        adaptiveTimestep: true, // 启用自适应时间步长
        timestep: 0.4, 
        minVelocity: 0.75, 
        stabilization: {
          enabled: true,
          iterations: 1000, // 增加迭代次数使布局更稳定
          updateInterval: 50,
          onlyDynamicEdges: false,
          fit: true
        }
      },
       
      interaction: { 
        hover: true, 
        tooltipDelay: 200, 
        hoverConnectedEdges: !isLargeGraph, 
        hideEdgesOnDrag: isLargeGraph, 
        selectable: true,
        zoomView: true,
        zoomSpeed: 0.5 
      },
       
      layout: { 
        improvedLayout: !isLargeGraph 
      }
    };

    // 9. 渲染
    if(graphRef.value) {
        graphRef.value.style.visibility = 'visible';
        graphRef.value.style.opacity = '1';
    }

    network.value = new Network(
      graphRef.value, 
      { nodes: new DataSet(validNodes), edges: new DataSet(validEdges) }, 
      options
    );

    // 10. 事件监听
    network.value.on('stabilizationIterationsDone', () => {
      loading.value = false;
      emit('graph-loaded');
      if (entity && entity !== EMPTY_TEXT_PLACEHOLDER && validNodes.length > 1) {
        const targetNode = validNodes.find(n => n.id === entity || n.label === entity);
        if (targetNode) network.value.focus(targetNode.id, { scale: 1.0, animation: { duration: 1000 } });
      }
    });

    network.value.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = validNodes.find(n => n.id === nodeId);
         
        // 无下属节点则不响应点击
        if (!node || !node.hasSubordinates) {
          if (node && !node.hasSubordinates) {
            ElMessage.info('该节点无下属关联内容');
          }
          return;
        }
         
        if (node.label === EMPTY_TEXT_PLACEHOLDER) {
          ElMessage.info('该节点无文本内容');
          return;
        }
         
        // 更新当前选中的实体状态
        searchEntity.value = node.label;
        currentEntity.value = node.label;
         
        // 记录历史
        if (nodeHistory.value[nodeHistory.value.length - 1] !== node.label) {
          nodeHistory.value.push(node.label);
        }
         
        // 通知父组件
        emit('update:currentEntity', node.label);
        emit('getRecommendData', node.label); 
         
        // 直接调用 initGraph
        initGraph(node.label);
      }
    });

  } catch (error) {
    console.error('图谱初始化错误：', error);
    ElMessage.error(`系统错误：${error.message}`);
    loading.value = false;
    destroyNetwork();
  }
};

// 辅助函数：调整颜色明暗度
const shadeColor = (color, percent) => {
  let R = parseInt(color.substring(1, 3), 16);
  let G = parseInt(color.substring(3, 5), 16);
  let B = parseInt(color.substring(5, 7), 16);

  R = parseInt(R * (100 + percent) / 100);
  G = parseInt(G * (100 + percent) / 100);
  B = parseInt(B * (100 + percent) / 100);

  R = (R < 255) ? R : 255;
  G = (G < 255) ? G : 255;
  B = (B < 255) ? B : 255;

  R = Math.round(R);
  G = Math.round(G);
  B = Math.round(B);

  const RR = ((R.toString(16).length === 1) ? "0" + R.toString(16) : R.toString(16));
  const GG = ((G.toString(16).length === 1) ? "0" + G.toString(16) : G.toString(16));
  const BB = ((B.toString(16).length === 1) ? "0" + B.toString(16) : B.toString(16));

  return "#" + RR + GG + BB;
};

// 辅助函数：根据背景色获取对比度高的文字颜色
const getContrastColor = (color) => {
  // 解析RGB值
  const R = parseInt(color.substring(1, 3), 16);
  const G = parseInt(color.substring(3, 5), 16);
  const B = parseInt(color.substring(5, 7), 16);
   
  // 计算亮度
  const luminance = (0.299 * R + 0.587 * G + 0.114 * B) / 255;
   
  // 亮度大于0.5使用黑色，否则使用白色
  return luminance > 0.5 ? '#000000' : '#FFFFFF';
};

// 加载词条数据 
const loadTermsData = async (entity = '') => {
  if (viewMode.value !== 'terms') return;
   
  loading.value = true;
  try {
    let res;
    if (entity && entity !== EMPTY_TEXT_PLACEHOLDER) {
      res = await api.getGraphDataByEntity(entity);
    } else {
      res = await api.getFullGraphData ? await api.getFullGraphData() : await api.getGraphData();
    }
     
    const data = res?.data || { nodes: [], edges: [] };
    const formattedEdges = Array.isArray(data.edges) ? data.edges.map(edge => ({
      source: formatEmptyText(edge.source || edge.from),
      target: formatEmptyText(edge.target || edge.to),
      relation: formatEmptyText(edge.relation || edge.label, EMPTY_RELATION_PLACEHOLDER, true)
    })).filter(edge => 
      edge.source && edge.target && edge.relation && 
      edge.source !== edge.target && 
      edge.source !== EMPTY_TEXT_PLACEHOLDER && 
      edge.target !== EMPTY_TEXT_PLACEHOLDER
    ) : [];
     
    const validNodeLabels = new Set();
    formattedEdges.forEach(edge => {
      validNodeLabels.add(edge.source);
      validNodeLabels.add(edge.target);
    });
     
    termsData.value = {
      nodes: Array.from(validNodeLabels).map(node => ({ id: node, label: node })),
      edges: formattedEdges
    };
  } catch (error) {
    console.error('加载词条数据失败：', error);
    ElMessage.error(`加载词条失败：${error.message}`);
  } finally {
    loading.value = false;
  }
};

// 处理词条点击
const handleTermClick = (entity) => {
  if (!entity || entity === EMPTY_TEXT_PLACEHOLDER) {
    ElMessage.warning('无效的实体名称');
    return;
  }
  if (!hasSubordinateContent(entity, termsData.value.edges)) {
    ElMessage.info(`「${entity}」无下属关联内容`);
    emit('getRecommendData', entity);
    return;
  }
  if (nodeHistory.value[nodeHistory.value.length - 1] !== entity) {
    nodeHistory.value.push(entity);
  }
   
  currentEntity.value = entity;
  emit('update:currentEntity', entity);
  emit('getRecommendData', entity);
   
  if (viewMode.value === 'graph') {
    initGraph(entity);
  } else {
    loadTermsData(entity);
  }
};

// 显示核心节点
const showAllGraph = () => {
  searchEntity.value = '';
  currentEntity.value = '';
  emit('update:currentEntity', '');
  emit('getRecommendData', '');
  nodeHistory.value = [''];
   
  if (viewMode.value === 'graph') {
    initGraph('', false);
  } else {
    loadTermsData('');
  }
};

// 导出图谱图片
const exportGraphImage = () => {
  if (viewMode.value !== 'graph' || !network.value || !graphRef.value) {
    ElMessage.warning('请在图谱视图下操作');
    return;
  }
  try {
    const canvas = graphRef.value.querySelector('canvas');
    if (!canvas) return;
    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = `kg-${currentEntity.value || 'full'}.png`;
    link.click();
  } catch (e) {
    ElMessage.error('导出图片失败：' + e.message);
  }
};

// 导出数据
const exportGraphJSON = () => {
  if (!network.value && !termsData.value) return ElMessage.warning('数据未加载');
  const data = viewMode.value === 'graph' 
    ? { nodes: network.value.body.data.nodes.get(), edges: network.value.body.data.edges.get() } 
    : termsData.value;
  const jsonStr = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `kg-data-${currentEntity.value || 'full'}.json`;
  link.click();
  URL.revokeObjectURL(url);
};

// 处理全屏状态变化
const handleFullScreenChange = () => {
  const isFull = !!document.fullscreenElement || !!document.webkitFullscreenElement || !!document.msFullscreenElement;
  isFullScreen.value = isFull;
  if (!isFull && !currentEntity.value) {
    if (viewMode.value === 'graph') initGraph('', false);
  }
};

// 切换全屏模式
const toggleFullScreen = async () => {
  const container = document.querySelector('.graph-wrapper'); // 全屏容器
  if (!container) return;

  try {
    if (!isFullScreen.value) {
      if (viewMode.value === 'graph') await initGraph(currentEntity.value || '', true);
      else await loadTermsData(currentEntity.value || '');
      
      if (container.requestFullscreen) await container.requestFullscreen();
      else if (container.webkitRequestFullscreen) await container.webkitRequestFullscreen();
      else if (container.msRequestFullscreen) await container.msRequestFullscreen();
      ElMessage.success(`进入全屏`);
    } else {
      if (document.exitFullscreen) await document.exitFullscreen();
      else if (document.webkitExitFullscreen) await document.webkitExitFullscreen();
      else if (document.msExitFullscreen) await document.msExitFullscreen();
      ElMessage.info(`退出全屏`);
    }
  } catch (error) {
    ElMessage.error(`全屏操作失败：${error.message}`);
  }
};

// 处理搜索输入回车事件
const handleInputKeyup = (e) => {
  if (e.key === 'Enter') {
    handleSearch();
  }
};

// 处理搜索
const handleSearch = () => {
  const entity = formatEmptyText(searchEntity.value.trim());
  if (!entity || entity === EMPTY_TEXT_PLACEHOLDER) {
    showAllGraph();
    return;
  }
  if (nodeHistory.value[nodeHistory.value.length - 1] !== entity) {
    nodeHistory.value.push(entity);
  }
   
  currentEntity.value = entity;
  emit('update:currentEntity', entity);
  emit('getRecommendData', entity);
   
  if (viewMode.value === 'graph') {
    initGraph(entity);
  } else {
    loadTermsData(entity);
  }
};

// 监听父组件实体变化
watch(
  () => props.mainEntity,
  (newEntity) => {
    if (newEntity && newEntity.trim() && currentEntity.value !== newEntity.trim()) {
      const entity = formatEmptyText(newEntity.trim());
      if (nodeHistory.value.length === 0) {
        nodeHistory.value.push(entity);
      } else if (nodeHistory.value[nodeHistory.value.length - 1] !== entity) {
        nodeHistory.value.push(entity);
      }
      currentEntity.value = entity;
      viewMode.value === 'graph' ? initGraph(entity) : loadTermsData(entity);
    }
  },
  { immediate: true, flush: 'post' }
);

// 生命周期
onMounted(async () => {
  await nextTick();
  setTimeout(() => { 
    viewMode.value === 'graph' ? initGraph(props.mainEntity) : loadTermsData(props.mainEntity); 
    if (props.mainEntity && props.mainEntity.trim()) {
      const entity = formatEmptyText(props.mainEntity.trim());
      if (nodeHistory.value.length === 0) {
        nodeHistory.value.push(entity);
      }
    } else if (nodeHistory.value.length === 0) {
      nodeHistory.value.push('');
    }
  }, 500);
  window.addEventListener('resize', () => { network.value?.redraw(); });
  document.addEventListener('fullscreenchange', handleFullScreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
  document.addEventListener('msfullscreenchange', handleFullScreenChange);
});

onUnmounted(() => {
  destroyNetwork();
  window.removeEventListener('resize', () => {});
  document.removeEventListener('fullscreenchange', handleFullScreenChange);
  document.removeEventListener('webkitfullscreenchange', handleFullScreenChange);
  document.removeEventListener('msfullscreenchange', handleFullScreenChange);
});
</script>

<style scoped>
/* 核心容器*/
.graph-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #FAFAFA; /* 极淡的底色 */
  background-image: radial-gradient(#CBD5E1 1px, transparent 1px); /* 点阵背景 */
  background-size: 24px 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 悬浮面板 */
.float-panel {
  position: absolute;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-left {
  top: 20px;
  left: 20px;
}

.top-right {
  top: 20px;
  right: 20px;
}

/* 玻璃拟态效果 */
.glass-panel {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  padding: 4px;
}

.glass-btn {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  border: 1px solid #E2E8F0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* 搜索胶囊 */
.search-capsule {
  display: flex;
  align-items: center;
  padding: 4px 6px;
  transition: all 0.3s ease;
}

.search-capsule:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.transparent-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent;
  padding: 0 8px;
  width: 180px;
}

.search-icon {
  color: #94A3B8;
}

.divider-v {
  width: 1px;
  height: 16px;
  background: #E2E8F0;
  margin: 0 4px;
}

.search-btn {
  font-weight: 600;
}

/* 视图切换开关 */
.view-switch {
  display: flex;
  background: #F1F5F9;
  border-radius: 8px;
  padding: 3px;
}

.switch-item {
  padding: 4px 12px;
  font-size: 13px;
  color: #64748B;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-item.active {
  background: #FFFFFF;
  color: var(--primary-color);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* 工具按钮 */
.toolbar-group {
  padding: 6px 10px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tool-btn {
  color: #64748B;
  font-size: 16px;
}

.tool-btn:hover {
  color: var(--primary-color);
  background: #F1F5F9;
}

/*  画布与内容  */
.center-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 10;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #E0E7FF;
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 13px;
  color: #64748B;
  background: rgba(255,255,255,0.9);
  padding: 4px 12px;
  border-radius: 20px;
}

.graph-canvas {
  width: 100%;
  height: 100%;
  outline: none;
}

/*  列表视图优化  */
.terms-wrapper {
  width: 100%;
  height: 100%;
  padding-top: 80px; /* 避开悬浮栏 */
  box-sizing: border-box;
  overflow: hidden;
}

.terms-scroll-area {
  height: 100%;
  overflow-y: auto;
  padding: 0 30px 30px 30px;
}

.terms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

/* 词条卡片 */
.term-card {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}

.term-card:hover {
  transform: translateY(-2px);
  border-color: var(--primary-color);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
}

.term-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
}

.node-pill {
  padding: 4px 10px;
  border-radius: 6px;
  background: #F8FAFC;
  color: #334155;
  font-weight: 500;
  text-decoration: none;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-pill:hover {
  background: #EEF2FF;
  color: var(--primary-color);
}

.relation-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  margin: 0 8px;
  color: #94A3B8;
  font-size: 12px;
}

.relation-arrow .line {
  width: 100%;
  height: 1px;
  background: #E2E8F0;
  margin-bottom: 2px;
}

.relation-arrow .arrow-head {
  font-size: 10px;
  margin-top: -8px;
}

.detail-btn {
  align-self: flex-end;
}
</style>