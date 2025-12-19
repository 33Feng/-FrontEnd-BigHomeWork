<template>
  <div class="graph-wrapper" style="width: 100%; height: 100%; position: relative;">
    <!-- 顶部导航栏：标题 + 右侧功能按钮（含视图切换） -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
      <h3 style="margin: 0; color: #333;">知识图谱可视化</h3>
      <!-- 右侧功能按钮组：视图切换 + 导出 + 全屏 -->
      <div style="display: flex; gap: 10px; align-items: center;">
        <!-- 视图切换按钮 -->
        <el-button 
          :type="viewMode === 'graph' ? 'success' : 'primary'" 
          @click="toggleViewMode"
        >
          {{ viewMode === 'graph' ? '切换为词条视图' : '切换为图谱视图' }}
        </el-button>
        
        <!-- 下拉导出菜单 -->
        <el-dropdown>
          <el-button plain>
            <el-icon class="el-icon--left"><Download /></el-icon>
            导出数据
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :icon="Picture" @click="exportGraphImage">导出为图片 (.png)</el-dropdown-item>
              <el-dropdown-item :icon="Download" @click="exportGraphJSON">导出 JSON 数据</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 全屏按钮 -->
        <el-button plain @click="toggleFullScreen">
          <el-icon class="el-icon--left"><FullScreen /></el-icon>
          全屏模式
        </el-button>
      </div>
    </div>

    <!-- 搜索区域 -->
    <div class="search-bar" style="margin-bottom: 10px; display: flex; gap: 10px;">
      <el-input
        v-model="searchEntity"
        placeholder="输入节点名称搜索"
        clearable
        @keyup="handleInputKeyup" 
        style="flex: 1; max-width: 80%;"
    ></el-input>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="showAllGraph">显示全部</el-button>
    </div>

    <!-- 图谱/词条容器 -->
    <div :class="['graph-container', { 'fullscreen': isFullScreen }]" style="width: 100%; height: calc(100% - 120px); position: relative; overflow: hidden;">
      <!-- 加载提示和回溯按钮（右上方，调整位置避免遮挡滚动条） -->
      <div style="position: absolute; top: 10px; right: 30px; display: flex; gap: 10px; z-index: 99999;">
        <el-button 
          type="primary" 
          size="small" 
          @click="backToPreviousNode"
          :disabled="nodeHistory.length <= 1"
          style="padding: 6px 12px; backdrop-filter: blur(2px);"
        >
          <el-icon class="el-icon--left"><ArrowLeft /></el-icon>
          回溯
        </el-button>
        <div v-if="loading" class="loading-tip">
          <el-icon style="margin-right: 5px;"><Loading /></el-icon>
          {{ currentEntity ? `加载「${currentEntity}」...` : '计算布局中...' }}
        </div>
      </div>
      
      <!-- 图谱视图 -->
      <div 
        v-show="viewMode === 'graph'"
        ref="graphRef" 
        style="width: 100%; height: 100%; border: 1px solid #e6e6e6; border-radius: 8px;"
      ></div>
      
      <!-- 词条视图 -->
      <div 
        v-show="viewMode === 'terms'" 
        class="terms-container"
      >
        <div class="terms-header">
          <h3>实体关系列表</h3>
          <p v-if="currentEntity">当前实体: {{ currentEntity || '无文本内容' }}</p>
        </div>
        <!-- 词条列表滚动容器：限制高度确保内容完整显示 -->
        <div class="terms-list-wrapper">
          <div class="terms-list">
            <!-- 加载中显示骨架屏 -->
            <div v-if="loading" class="terms-loading">
              <div class="loading-skeleton" v-for="i in 5" :key="i"></div>
            </div>
            
            <!-- 有数据时显示词条 -->
            <div 
              v-else-if="termsData.edges.length > 0"
              v-for="(edge, index) in termsData.edges" 
              :key="`${edge.source}-${edge.relation}-${edge.target}-${index}`" 
              class="term-item"
            >
              <!-- 词条添加百度百科链接 -->
              <a 
                :href="getBaiduLink(edge.source)" 
                target="_blank" 
                class="term-node"
                :title="edge.source || '无文本内容'"
              >
                {{ edge.source || '无文本内容' }}
              </a>
              <div class="term-relation">{{ edge.relation || '无关联' }}</div>
              <a 
                :href="getBaiduLink(edge.target)" 
                target="_blank" 
                class="term-node"
                :title="edge.target || '无文本内容'"
              >
                {{ edge.target || '无文本内容' }}
              </a>
              <el-button 
                type="text" 
                size="small" 
                @click="handleTermClick(edge.source === currentEntity ? edge.target : edge.source)"
                :disabled="
                  !(edge.source === currentEntity ? edge.target : edge.source) || 
                  (edge.source === currentEntity ? edge.target : edge.source) === '无文本内容' ||
                  !hasSubordinateContent(edge.source === currentEntity ? edge.target : edge.source, termsData.edges)
                "
              >
                查看详情
              </el-button>
            </div>
            
            <!-- 无数据时显示友好提示 -->
            <div v-else class="no-data">
              无关联实体关系
            </div>
          </div>
        </div>
      </div>
      
      <el-button 
        type="text" 
        @click="initGraph" 
        style="position: absolute; bottom: 10px; right: 10px; z-index: 99999;"
      >
        重新加载
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted, watch,  shallowRef, markRaw } from 'vue';
import { Network, DataSet } from 'vis-network/standalone';
import { ElButton, ElMessage, ElInput, ElIcon } from 'element-plus';
import { FullScreen, Picture, Download, ArrowDown, Loading, ArrowLeft } from '@element-plus/icons-vue';
import { api } from '../api/index';

// --- 1. 智能颜色映射 (模糊匹配) ---
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
    ElMessage.error('图谱容器不存在');
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

// --- 核心：初始化图谱 ---
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

    // 8. 配置项 - 优化物理引擎
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
    graphRef.value.style.visibility = 'visible';
    graphRef.value.style.opacity = '1';
      

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
        
        // 记录历史 (用于回溯功能，确保初始状态被保留)
        if (nodeHistory.value[nodeHistory.value.length - 1] !== node.label) {
          nodeHistory.value.push(node.label);
        }
        
        // 通知父组件更新推荐
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
  // 检查是否有下属内容
  if (!hasSubordinateContent(entity, termsData.value.edges)) {
    ElMessage.info(`「${entity}」无下属关联内容`);
    // 依然可以查看推荐
    emit('getRecommendData', entity);
    return;
  }
  // 记录历史 (确保初始状态被保留)
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

// 显示核心节点（初始化历史记录为初始状态）
const showAllGraph = () => {
  searchEntity.value = '';
  currentEntity.value = '';
  emit('update:currentEntity', '');
  emit('getRecommendData', '');
  // 初始状态用空字符串标识，作为历史记录的第一个元素
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
  // 退出全屏时，如果是显示全部状态且没有选中实体，重置为核心视图以防卡顿
  if (!isFull && !currentEntity.value) {
    if (viewMode.value === 'graph') initGraph('', false);
  }
};

// 切换全屏模式
const toggleFullScreen = async () => {
  const container = document.querySelector('.graph-container');
  if (!container) return;

  try {
    if (!isFullScreen.value) {
      if (viewMode.value === 'graph') await initGraph(currentEntity.value || '', true);
      else await loadTermsData(currentEntity.value || '');
      
      if (container.requestFullscreen) await container.requestFullscreen();
      else if (container.webkitRequestFullscreen) await container.webkitRequestFullscreen();
      else if (container.msRequestFullscreen) await container.msRequestFullscreen();
      ElMessage.success(`已进入全屏模式`);
    } else {
      if (document.exitFullscreen) await document.exitFullscreen();
      else if (document.webkitExitFullscreen) await document.webkitExitFullscreen();
      else if (document.msExitFullscreen) await document.msExitFullscreen();
      ElMessage.info(`已退出全屏模式`);
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
  
  // 记录历史（确保初始状态被保留）
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

// 监听父组件实体变化（初始化历史记录）
watch(
  () => props.mainEntity,
  (newEntity) => {
    if (newEntity && newEntity.trim() && currentEntity.value !== newEntity.trim()) {
      const entity = formatEmptyText(newEntity.trim());
      // 初始时如果历史为空，添加初始实体到历史（作为初始状态）
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
    // 初始化历史记录：如果父组件有初始实体，添加到历史；否则添加空字符串（显示全部）
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
/* 容器样式 */
.graph-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.graph-container {
  position: relative;
  width: 100%;
  height: calc(100% - 120px);
  border-radius: 8px;
  box-sizing: border-box;
  background-color: #fff;
}

/* 加载提示 */
.loading-tip {
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 20px;
  font-size: 14px;
  color: #666;
  display: flex;
  align-items: center;
  backdrop-filter: blur(2px);
  z-index: 99999 !important;
}

/* 全屏样式 */
.graph-container.fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 99999 !important;
  background: white !important;
  border: none !important;
  margin: 0 !important;
  padding: 20px !important;
}

.graph-container.fullscreen :deep(.vis-network) {
  width: 100% !important;
  height: 100% !important;
  outline: none;
}

/* 词条视图样式 */
.terms-container {
  width: 100%;
  height: 100%;
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.terms-header {
  padding: 15px;
  border-bottom: 1px solid #e6e6e6;
  background-color: #f5f7fa;
}

.terms-header h3 {
  margin: 0 0 5px 0;
  font-size: 16px;
  color: #333;
}

.terms-header p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.terms-list-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
  box-sizing: border-box;
}

.terms-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.terms-loading {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 10px 0;
}

.loading-skeleton {
  height: 50px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 6px;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 词条项样式 */
.term-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  flex-wrap: wrap;
  transition: background-color 0.3s;
}

.term-item:hover {
  background: #eef2f7;
}

.term-node {
  padding: 6px 12px;
  background: #e8f4fd;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
  color: #1989FA;
  text-decoration: none;
  transition: all 0.2s;
}

.term-node:hover {
  background: #d1e7fd;
  text-decoration: underline;
  color: #0C6ECD;
}

.term-node[href="javascript:void(0);"] {
  color: #909399;
  cursor: not-allowed;
  background: #f5f5f5;
}

.term-node[href="javascript:void(0);"]:hover {
  text-decoration: none;
  background: #f5f5f5;
}

.term-relation {
  padding: 6px 12px;
  color: #666;
  flex: 1;
  min-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-data {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 14px;
}

/* Vis-network 样式覆盖 */
:deep(.vis-network) {
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
}

:deep(.vis-node) {
  transition: all 0.2s;
  z-index: 100 !important;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.2));
}

:deep(.vis-node:hover) {
  stroke: #000000 !important;
  stroke-width: 3px !important;
}

:deep(.vis-label) {
  font-size: 12px !important;
  padding: 2px 5px !important;
  border-radius: 3px !important;
  background-color: rgba(255, 255, 255, 0.8) !important;
}

:deep(.vis-edge) {
  transition: all 0.3s;
}

:deep(.vis-edge:hover) {
  stroke-width: 3px !important;
}

/* 全屏模式样式适配 */
.fullscreen .terms-container,
.fullscreen :deep(.vis-network) {
  height: 100% !important;
}

/* 确保Element Plus提示在全屏时可见 */
:deep(.el-message) {
  z-index: 999999 !important;
}
</style>