<template>
  <div class="graph-wrapper" style="width: 100%; height: 550px; position: relative;">
    <!-- 顶部导航栏：标题 + 右侧功能按钮（含视图切换） -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
      
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
          <el-icon class="el-icon--left"><Fullscreen /></el-icon>
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
        @keyup.enter="handleSearch"
        style="flex: 1; max-width: 80%;"
      ></el-input>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="showAllGraph">显示全部</el-button>
    </div>

    <!-- 图谱/词条容器 -->
    <div :class="['graph-container', { 'fullscreen': isFullScreen }]" style="width: 100%; height: 500px; position: relative; overflow: hidden;">
      <!-- 加载提示和回溯按钮（右上方） -->
      <div style="position: absolute; top: 10px; right: 10px; display: flex; gap: 10px; z-index: 99999;">
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
          {{ currentEntity ? `加载「${currentEntity}」数据...` : '加载中...' }}
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
            <div class="term-node">{{ edge.source || '无文本内容' }}</div>
            <div class="term-relation">{{ edge.relation || '无关联' }}</div>
            <div class="term-node">{{ edge.target || '无文本内容' }}</div>
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
import { ref, onMounted, nextTick, onUnmounted, watch, defineProps, defineEmits } from 'vue';
import { api } from '../api/index';
import { Network, DataSet } from 'vis-network/standalone';
import { ElButton, ElMessage, ElInput, ElIcon } from 'element-plus';
import { Fullscreen, Picture, Download, ArrowDown, Loading, ArrowLeft } from '@element-plus/icons-vue';

// 接收父组件传递的核心实体
const props = defineProps({
  mainEntity: {
    type: String,
    default: ''
  }
});

// 向父组件发送当前选中的实体
const emit = defineEmits(['update:currentEntity', 'graph-loaded']);

// 响应式数据
const graphRef = ref(null);
const network = ref(null); // 图谱实例
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

// 切换视图模式
const toggleViewMode = () => {
  const oldMode = viewMode.value;
  viewMode.value = viewMode.value === 'graph' ? 'terms' : 'graph';
  
  // 切换到词条视图：强制加载数据
  if (viewMode.value === 'terms') {
    loadTermsData(currentEntity.value || props.mainEntity);
  } 
  // 切换到图谱视图：强制初始化
  else if (viewMode.value === 'graph' && oldMode === 'terms') {
    if (graphRef.value) {
      graphRef.value.innerHTML = '';
    }
    initGraph(currentEntity.value || props.mainEntity);
  }
};

// 检查节点是否有下属关联内容（作为source存在关联边）
const hasSubordinateContent = (entity, edges = []) => {
  if (!entity || entity === EMPTY_TEXT_PLACEHOLDER) return false;
  // 检查是否存在该实体作为source的关联边
  return edges.some(edge => edge.source === entity && edge.target !== EMPTY_TEXT_PLACEHOLDER);
};

// 格式化空文本：空值/乱码/无效文本替换为占位符，relation单独宽松判断
const formatEmptyText = (text, defaultText = EMPTY_TEXT_PLACEHOLDER, isRelation = false) => {
  if (text === undefined || text === null) return defaultText;
  
  const trimmedText = String(text).trim();
  if (trimmedText === '') return defaultText;
  
  // Relation宽松判断：只要包含中文、字母、数字即为有效
  if (isRelation) {
    // 匹配中文、字母、数字的正则
    const validCharRegex = /[\u4e00-\u9fa5a-zA-Z0-9]/;
    return validCharRegex.test(trimmedText) ? trimmedText : defaultText;
  }
  
  // 普通文本严格判断：空字符串、纯数字、纯特殊字符、乱码（含不可打印字符）
  const isInvalid = /^[\d\s\W]+$/.test(trimmedText) || 
                    /[\x00-\x1F\x7F]/.test(trimmedText) || // 控制字符
                    /[\uFFFD]/.test(trimmedText); // 替换字符（乱码标识）
  return isInvalid ? defaultText : trimmedText;
};

// 加载词条数据
const loadTermsData = async (entity = '') => {
  try {
    loading.value = true;
    let res;
    
    // 优化请求逻辑：entity为空时加载核心数据
    if (entity.trim() && entity !== EMPTY_TEXT_PLACEHOLDER) {
      res = await api.getGraphDataByEntity(encodeURIComponent(entity.trim()));
    } else {
      res = await api.getGraphData();
    }
    
    // 数据强容错处理
    const data = res?.data || { nodes: [], edges: [] };
    const formattedEdges = [];
    
    // 格式化边数据：兼容不同后端返回格式，relation宽松判断
    if (Array.isArray(data.edges)) {
      formattedEdges.push(...data.edges.map(edge => ({
        source: formatEmptyText(edge.source || edge.from),
        target: formatEmptyText(edge.target || edge.to),
        // 关系字段单独处理，宽松判断有效内容
        relation: formatEmptyText(edge.relation || edge.label, EMPTY_RELATION_PLACEHOLDER, true)
      })));
    }
    
    // 过滤无效边，确保数据有效性（两端节点均有效）
    const validEdges = formattedEdges.filter(edge => 
      edge.source && edge.target && edge.relation && 
      edge.source !== edge.target && 
      edge.source !== EMPTY_TEXT_PLACEHOLDER && 
      edge.target !== EMPTY_TEXT_PLACEHOLDER
    );
    
    // 基于有效边提取有效节点（避免孤立的无效节点）
    const validNodeLabels = new Set();
    validEdges.forEach(edge => {
      validNodeLabels.add(edge.source);
      validNodeLabels.add(edge.target);
    });
    
    // 处理节点数据：仅保留有效边关联的节点
    const validNodes = Array.isArray(data.nodes) 
      ? data.nodes.map(node => ({
          ...node,
          label: formatEmptyText(node.label || node.id)
        })).filter(node => validNodeLabels.has(node.label))
      : Array.from(validNodeLabels).map(label => ({
          id: `node_${label}_${Date.now()}`,
          label,
          shape: 'ellipse',
          size: 25
        }));
    
    termsData.value = {
      nodes: validNodes,
      edges: validEdges
    };
    
  } catch (error) {
    ElMessage.error(`加载词条数据失败：${error.message || '网络错误'}`);
    console.error('词条数据加载错误：', error);
    termsData.value = { nodes: [], edges: [] };
  } finally {
    loading.value = false;
  }
};

// 处理词条点击
const handleTermClick = (entity) => {
  const formattedEntity = formatEmptyText(entity);
  if (formattedEntity === EMPTY_TEXT_PLACEHOLDER) return;
  
  // 检查是否有下属内容，无则提示不触发
  if (!hasSubordinateContent(formattedEntity, termsData.value.edges)) {
    ElMessage.info(`「${formattedEntity}」无下属关联内容，无需查看详情`);
    return;
  }
  
  // 添加到历史记录（去重，避免连续点击同一节点）
  if (nodeHistory.value[nodeHistory.value.length - 1] !== formattedEntity) {
    nodeHistory.value.push(formattedEntity);
  }
  
  searchEntity.value = formattedEntity;
  currentEntity.value = formattedEntity;
  emit('update:currentEntity', formattedEntity);
  
  // 点击后保持在词条视图，更新数据
  loadTermsData(formattedEntity);
};

// 回溯到上一个节点
const backToPreviousNode = () => {
  if (nodeHistory.value.length <= 1) {
    ElMessage.info('已经是第一个节点了');
    return;
  }
  
  // 移除当前节点，获取上一个节点
  nodeHistory.value.pop();
  const prevEntity = nodeHistory.value[nodeHistory.value.length - 1];
  
  // 更新状态并加载上一个节点数据
  searchEntity.value = prevEntity;
  currentEntity.value = prevEntity;
  emit('update:currentEntity', prevEntity);
  
  if (viewMode.value === 'graph') {
    initGraph(prevEntity);
  } else {
    loadTermsData(prevEntity);
  }
  
  ElMessage.success(`已回溯到「${prevEntity}」`);
};

// 检查当前节点是否为无效节点（无文本内容），如果是则自动回溯
const checkAndBacktrackInvalidNode = (nodeLabel) => {
  // 独立节点（无关联节点）即使是无文本内容也不回溯
  if (nodeLabel === EMPTY_TEXT_PLACEHOLDER && nodeHistory.value.length > 1) {
    ElMessage.warning('当前节点无文本内容，已自动回溯到上一节点');
    setTimeout(() => {
      backToPreviousNode();
    }, 500);
    return true;
  }
  return false;
};

// 销毁图谱实例
const destroyNetwork = () => {
  if (network.value) {
    try {
      network.value.off('stabilizationIterationsDone');
      network.value.off('click');
      network.value.off('physicsUpdate');
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

  // 强制触发重绘
  graphRef.value.style.display = 'none';
  graphRef.value.offsetHeight;
  graphRef.value.style.display = 'block';
  
  const rect = graphRef.value.getBoundingClientRect();
  if (rect.width <= 10 || rect.height <= 10) {
    graphRef.value.style.minWidth = '300px';
    graphRef.value.style.minHeight = '300px';
    return true;
  }
  
  return true;
};

// 初始化图谱
const initGraph = async (targetEntity = '', forceFull = false) => {
  if (viewMode.value !== 'graph') return;
  
  try {
    loading.value = true;
    destroyNetwork();

    await nextTick();
    await new Promise(resolve => setTimeout(resolve, 300));

    if (!checkContainerValidity()) {
      if (initRetryCount.value < 3) {
        initRetryCount.value++;
        ElMessage.info(`重试初始化图谱（${initRetryCount.value}/3）`);
        setTimeout(() => initGraph(targetEntity, forceFull), 800);
        return;
      } else {
        initRetryCount.value = 0;
        loading.value = false;
        ElMessage.error('图谱初始化失败，请刷新页面重试');
        return;
      }
    }
    initRetryCount.value = 0;

    let entity = typeof targetEntity === 'string' ? targetEntity.trim() : '';
    entity = targetEntity === '' ? '' : (entity || currentEntity.value || props.mainEntity);
    // 格式化实体名称，避免无效值
    entity = formatEmptyText(entity);
    currentEntity.value = entity;
    emit('update:currentEntity', entity);

    let res;
    try {
      // 根据是否全屏或强制全屏决定加载核心还是全部数据
      if (entity && entity !== EMPTY_TEXT_PLACEHOLDER) {
        // 有当前实体：加载当前实体数据（全屏时也加载当前实体，不加载全部）
        res = await api.getGraphDataByEntity(encodeURIComponent(entity));
        isShowingFull.value = forceFull; // 仅标记为全屏状态，不改变数据加载逻辑
      } else if (isFullScreen.value || forceFull) {
        // 无当前实体（默认状态）+ 全屏：加载全部数据
        res = await api.getFullGraphData ? await api.getFullGraphData() : await api.getGraphData();
        isShowingFull.value = true;
      } else {
        // 默认状态：加载核心数据
        res = await api.getGraphData();
        isShowingFull.value = false;
      }
      
      // 同步更新词条数据
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
      
      // 基于有效边提取有效节点（减少无效节点）
      const validNodeLabels = new Set();
      formattedEdges.forEach(edge => {
        validNodeLabels.add(edge.source);
        validNodeLabels.add(edge.target);
      });
      
      termsData.value = {
        nodes: Array.isArray(data.nodes) ? data.nodes.map(node => ({
          ...node,
          label: formatEmptyText(node.label || node.id)
        })).filter(node => validNodeLabels.has(node.label)) : [],
        edges: formattedEdges
      };
    } catch (apiError) {
      ElMessage.error(`数据请求失败：${apiError.message}`);
      loading.value = false;
      return; 
    }
    
    const { nodes = [], edges = [] } = res?.data || {};

    // 格式化并过滤边数据（仅保留有效边，relation宽松判断）
    const formattedEdges = Array.isArray(edges) ? edges.map(edge => ({
      source: formatEmptyText(edge.source || edge.from),
      target: formatEmptyText(edge.target || edge.to),
      // 关系字段单独处理，确保后端CSV中的relation正确显示
      relation: formatEmptyText(edge.relation || edge.label, EMPTY_RELATION_PLACEHOLDER, true)
    })).filter(edge => 
      edge.source && edge.target && edge.relation && 
      edge.source !== edge.target && 
      edge.source !== EMPTY_TEXT_PLACEHOLDER && 
      edge.target !== EMPTY_TEXT_PLACEHOLDER
    ) : [];

    // 基于有效边提取有效节点（避免大量"无文本内容"节点）
    const validNodeLabels = new Set();
    formattedEdges.forEach(edge => {
      validNodeLabels.add(edge.source);
      validNodeLabels.add(edge.target);
    });

    // 处理节点数据：仅保留有效边关联的节点，格式化空文本/乱码
    let validNodes = nodes
      .filter(node => node.id || node.label)
      .map(node => ({
        id: node.id || `node_${Date.now()}_${Math.random().toString(36).slice(2)}`,
        label: formatEmptyText(node.label || node.id), // 格式化空文本/乱码
        shape: 'ellipse',
        size: 25,
        color: { 
          background: (node.id || formatEmptyText(node.label || node.id)) === entity ? '#67C23A' : '#409EFF',
          border: (node.id || formatEmptyText(node.label || node.id)) === entity ? '#529B2E' : '#1989FA' 
        },
        // 节点物理属性：启用碰撞，设置质量
        physics: true,
        mass: 1.5 // 增加节点质量，使碰撞更明显
      }))
      // 过滤：仅保留有效边关联的节点，减少"无文本内容"节点
      .filter(node => validNodeLabels.has(node.label) && node.label !== EMPTY_TEXT_PLACEHOLDER);

    // 初始状态（非全屏、非搜索、非强制全屏）只显示前15个关键节点
    if (!entity || entity === EMPTY_TEXT_PLACEHOLDER) {
      if (!isFullScreen.value && !forceFull && !isShowingFull.value) {
        validNodes = validNodes.slice(0, MAX_DEFAULT_NODES);
        ElMessage.info(`当前显示前${MAX_DEFAULT_NODES}个关键节点，全屏模式下显示全部`);
      }
    }

    // 处理没有关联节点的情况（点击节点后无下属节点）
    if (validNodes.length === 0) {
      validNodes.push({
        id: `node_empty_${Date.now()}`,
        label: entity !== EMPTY_TEXT_PLACEHOLDER ? entity : EMPTY_TEXT_PLACEHOLDER,
        shape: 'ellipse',
        size: 30,
        color: { 
          background: '#67C23A',
          border: '#529B2E'
        },
        physics: false // 单个节点禁用物理引擎
      });
    }

    const nodeIds = validNodes.map(n => n.id);
    const nodeLabelMap = new Map(validNodes.map(n => [n.label, n.id])); // 标签到ID的映射

    // 过滤并格式化边数据（确保边连接的节点存在于当前节点列表）
    const validEdges = formattedEdges
      .filter(edge => 
        nodeLabelMap.has(edge.source) && 
        nodeLabelMap.has(edge.target)
      )
      .map(edge => {
        // 为每条边生成随机但合理的物理参数，与节点共享同一碰撞引擎
        const randomness = 0.6 + Math.random() * 0.4; // 0.6-1.0之间的随机因子
        
        return {
          from: nodeLabelMap.get(edge.source),
          to: nodeLabelMap.get(edge.target),
          label: edge.relation, // 直接使用后端返回的relation，不修改
          width: 2,
          color: '#999',
          arrows: { to: { enabled: true, scaleFactor: 0.7 } },
          // 边的物理属性：启用物理碰撞，与节点使用相同的物理引擎
          physics: true,
          // 弹簧参数（控制边的拉力和长度）
          springConstant: 0.15 * randomness,
          springLength: 150 * randomness,
          damping: 0.7 * randomness,
          // 边的碰撞相关参数
          stiffness: 0.8 * randomness, // 边的刚度，影响碰撞反应
          repulsion: 200 * randomness, // 边之间的排斥力
          // 确保边参与碰撞检测
          mass: 1.0, // 边的质量，与节点质量匹配
          avoidOverlap: true // 启用边与边、边与节点的重叠避免
        };
      });

    // 优化物理引擎配置：节点和边共享同一碰撞引擎，都能发生碰撞
    const options = {
      nodes: { 
        font: { size: 14, color: '#333', face: 'Arial' },
        shape: 'dot',
        scaling: {
          min: 15,
          max: 35,
          label: { enabled: true, min: 14, max: 20 }
        },
        borderWidth: 2,
        margin: 15, // 增加节点边距，增强碰撞效果
        zIndex: 100
      },
      edges: { 
        font: { size: 10, align: 'middle', color: '#888', face: 'Arial' },
        color: { color: '#e2e2e2', highlight: '#409EFF' },
        smooth: { 
          type: 'cubicBezier', 
          forceDirection: 'horizontal',
          roundness: 0.3
        },
        hoverWidth: 3,
        zIndex: 1,
        // 边的碰撞检测配置
        margin: 20, // 边与其他元素的距离，增强碰撞效果
        labelOffset: 15 // 边标签偏移，避免被碰撞覆盖
      },
      physics: {
        enabled: validNodes.length > 1, // 单个节点禁用物理引擎
        solver: 'forceAtlas2Based', // 统一使用forceAtlas2Based引擎
        forceAtlas2Based: {
          theta: 0.5,
          gravitationalConstant: -300, // 增强全局排斥力
          centralGravity: 0.08,
          springConstant: 0, // 禁用全局弹簧参数，使用边的独立参数
          springLength: 0, // 禁用全局弹簧长度，使用边的独立参数
          damping: 0.7,
          avoidOverlap: 0.9, // 增强全局避免重叠力度
          edgeWeightInfluence: 15.0, // 增强边权重影响，使边碰撞更明显
          // 碰撞检测配置
          barnesHut: {
            theta: 0.5,
            gravitationalConstant: -200,
            centralGravity: 0.1,
            springConstant: 0.04,
            springLength: 100,
            damping: 0.09
          }
        },
        stabilization: {
          enabled: true,
          iterations: 300, // 增加迭代次数，让碰撞稳定更充分
          updateInterval: 25,
          onlyDynamicEdges: false,
          fit: true
        },
        // 全局碰撞和排斥配置
        repulsion: {
          nodeDistance: 200, // 节点之间的最小距离
          centralGravity: 0.1,
          springLength: 200,
          springConstant: 0.03,
          damping: 0.1,
          // 边与边、边与节点的碰撞排斥
          edgeDistance: 50, // 边之间的最小距离
          edgeNodeDistance: 80 // 边与节点之间的最小距离
        },
        // 启用碰撞检测
        collision: {
          enabled: true,
          detection: 'all', // 检测所有元素（节点-节点、节点-边、边-边）
          handleOverlap: 0.8 // 重叠处理力度
        }
      },
      interaction: { 
        hover: true, 
        tooltipDelay: 200,
        dragNodes: true,
        zoomView: true,
        navigationButtons: false,
        keyboard: true,
        selectable: true
      },
      layout: {
        randomSeed: 42,
        improvedLayout: true // 启用改进布局，增强碰撞效果
      }
    };

    try {
      graphRef.value.style.visibility = 'visible';
      graphRef.value.style.opacity = '1';
      
      network.value = new Network(
        graphRef.value, 
        { 
          nodes: new DataSet(validNodes), 
          edges: new DataSet(validEdges) 
        }, 
        options
      );

      network.value.on('stabilizationIterationsDone', () => {
        loading.value = false;
        emit('graph-loaded');
        network.value?.setOptions({
          physics: {
            enabled: true,
            stabilization: { enabled: false },
            forceAtlas2Based: { 
              damping: 0.8,
              edgeWeightInfluence: 15.0
            },
            collision: {
              enabled: true
            }
          }
        });
        
        // 聚焦目标节点并检查是否为无效节点
        if (entity && entity !== EMPTY_TEXT_PLACEHOLDER && validNodes.length > 1) {
          const targetNode = validNodes.find(n => n.id === entity || n.label === entity);
          if (targetNode && network.value) {
            network.value.focus(targetNode.id, { scale: 1.3, animation: { duration: 1000 } });
            // 检查聚焦节点是否为无效节点，是则自动回溯
            checkAndBacktrackInvalidNode(targetNode.label);
          }
        }
      });

      network.value.on('click', (params) => {
        if (params.nodes.length > 0 && network.value) {
          const nodeId = params.nodes[0];
          const node = validNodes.find(n => n.id === nodeId);
          if (node) {
            // 过滤无文本内容的节点点击（全屏/非全屏均提示）
            if (node.label === EMPTY_TEXT_PLACEHOLDER) {
              ElMessage.info({
                message: '该节点无文本内容，无法触发操作',
                type: 'info',
                duration: 2000,
                zIndex: 999999 // 确保全屏时提示可见
              });
              // 有历史记录时自动回溯
              if (nodeHistory.value.length > 1) {
                setTimeout(() => {
                  checkAndBacktrackInvalidNode(node.label);
                }, 300);
              }
              return;
            }
            
            // 检查节点是否有下属内容，无则提示（全屏/非全屏均提示）
            const hasSubContent = validEdges.some(edge => edge.from === node.id);
            if (!hasSubContent) {
              ElMessage.info({
                message: `「${node.label}」无下属关联内容，无需进一步操作`,
                type: 'info',
                duration: 2000,
                zIndex: 999999 // 确保全屏时提示可见
              });
              return;
            }
            
            searchEntity.value = node.label;
            handleSearch();
          }
        }
      });

      // 监听物理引擎更新，确保碰撞持续生效
      network.value.on('physicsUpdate', () => {
        if (network.value && validNodes.length > 1) {
          network.value.setOptions({
            physics: {
              collision: {
                enabled: true
              }
            }
          });
        }
      });

    } catch (initError) {
      console.error('图谱实例创建失败：', initError);
      ElMessage.error(`图谱加载失败：${initError.message}`);
      loading.value = false;
      graphRef.value.innerHTML = `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#999;">图谱加载失败，请点击"重新加载"重试</div>`;
      return;
    }

  } catch (error) {
    console.error('图谱初始化总错误：', error);
    ElMessage.error(`系统错误：${error.message}`);
    loading.value = false;
    destroyNetwork();
  }
};

// 处理搜索
const handleSearch = () => {
  let entity = searchEntity.value.trim();
  // 格式化搜索实体，避免无效值
  entity = formatEmptyText(entity);
  
  if (entity === EMPTY_TEXT_PLACEHOLDER) {
    ElMessage.warning('请输入有效的节点名称！');
    return;
  }
  
  // 检查是否有下属内容（基于当前词条数据），无则提示
  if (!hasSubordinateContent(entity, termsData.value.edges)) {
    ElMessage.info(`「${entity}」无下属关联内容，无需搜索`);
    return;
  }
  
  // 添加到历史记录（去重，避免连续点击同一节点）
  if (nodeHistory.value[nodeHistory.value.length - 1] !== entity) {
    nodeHistory.value.push(entity);
  }
  
  currentEntity.value = entity;
  emit('update:currentEntity', entity);
  
  if (viewMode.value === 'graph') {
    initGraph(entity);
  } else {
    loadTermsData(entity);
  }
};

// 显示核心节点（默认状态）
const showAllGraph = () => {
  searchEntity.value = '';
  currentEntity.value = '';
  emit('update:currentEntity', '');
  nodeHistory.value = []; // 清空历史记录
  
  // 显示核心节点（前15个），不进入全屏
  if (viewMode.value === 'graph') {
    initGraph('', false);
  } else {
    loadTermsData('');
  }
};

// 导出图谱图片
const exportGraphImage = () => {
  if (viewMode !== 'graph' || !network.value || !graphRef.value) {
    ElMessage.warning('请在图谱视图下操作，且确保图谱已加载');
    return;
  }
  
  try {
    const canvas = graphRef.value.querySelector('canvas');
    if (!canvas) {
      ElMessage.error('无法获取图谱画布');
      return;
    }

    const imgUrl = canvas.toDataURL('image/png', 1.0);
    const link = document.createElement('a');
    link.href = imgUrl;
    const fileName = currentEntity.value && currentEntity.value !== EMPTY_TEXT_PLACEHOLDER
      ? `knowledge-graph-${currentEntity.value}.png` 
      : 'frontend-knowledge-graph.png';
    link.download = fileName;
    
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
    }, 100);
    
    ElMessage.success('图谱图片已导出');
  } catch (e) {
    ElMessage.error('导出图片失败：' + e.message);
  }
};

// 导出数据
const exportGraphJSON = () => {
  let exportData;
  
  if (viewMode === 'graph' && network.value) {
    exportData = {
      nodes: network.value.body.data.nodes.get(),
      edges: network.value.body.data.edges.get()
    };
  } else if (viewMode === 'terms' && termsData.value) {
    exportData = termsData.value;
  } else {
    ElMessage.warning('数据未加载，无法导出');
    return;
  }

  try {
    const data = {
      timestamp: new Date().toISOString(),
      entity: currentEntity.value || 'ALL',
      nodes: exportData.nodes || [],
      edges: exportData.edges || []
    };

    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json; charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    const fileName = currentEntity.value && currentEntity.value !== EMPTY_TEXT_PLACEHOLDER
      ? `kg-data-${currentEntity.value}.json` 
      : 'kg-data-full.json';
    link.download = fileName;
    
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 100);

    ElMessage.success('数据已导出');
  } catch (e) {
    ElMessage.error('导出 JSON 失败：' + e.message);
  }
};

// 监听父组件实体变化
watch(
  () => props.mainEntity,
  (newEntity) => {
    if (newEntity && newEntity.trim() && (!currentEntity.value || currentEntity.value !== newEntity.trim())) {
      const entity = formatEmptyText(newEntity.trim());
      // 检查是否有下属内容，无则不加载
      if (!hasSubordinateContent(entity, termsData.value.edges)) {
        ElMessage.info(`「${entity}」无下属关联内容，无需加载`);
        return;
      }
      
      // 添加到历史记录
      if (entity !== EMPTY_TEXT_PLACEHOLDER && nodeHistory.value[nodeHistory.value.length - 1] !== entity) {
        nodeHistory.value.push(entity);
      }
      currentEntity.value = entity;
      if (viewMode.value === 'graph') {
        initGraph(entity);
      } else {
        loadTermsData(entity);
      }
    }
  },
  { immediate: true, flush: 'post' }
);

// 挂载后初始化
onMounted(async () => {
  await nextTick();
  setTimeout(() => {
    if (viewMode.value === 'graph') {
      initGraph(props.mainEntity);
    } else {
      loadTermsData(props.mainEntity);
    }
  }, 500);

  // 窗口resize监听
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (network.value && viewMode.value === 'graph') {
        network.value.redraw();
      }
    }, 300);
  });

  // 全屏事件监听
  document.addEventListener('fullscreenchange', handleFullScreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
  document.addEventListener('msfullscreenchange', handleFullScreenChange);
});

// 全屏切换（核心优化：默认状态显示全部，有当前节点显示当前节点）
const toggleFullScreen = () => {
  const container = document.querySelector('.graph-container');
  if (!container) return;

  try {
    if (!isFullScreen.value) {
      // 进入全屏：根据当前是否有选中节点决定加载内容
      if (viewMode.value === 'graph') {
        if (!currentEntity.value || currentEntity.value === EMPTY_TEXT_PLACEHOLDER) {
          // 无当前节点（默认状态）：加载全部节点
          initGraph('', true).then(() => {
            requestFullScreen(container);
          });
        } else {
          // 有当前节点：加载当前节点数据，仅进入全屏状态
          initGraph(currentEntity.value, true).then(() => {
            requestFullScreen(container);
          });
        }
      } else {
        // 词条视图直接进入全屏
        requestFullScreen(container);
      }
      ElMessage.success(`已进入全屏模式（${currentEntity.value ? '显示当前节点' : '显示全部节点'}），按ESC键可退出`);
    } else {
      // 退出全屏
      exitFullScreen();
      ElMessage.info(`已退出全屏模式（当前显示前${MAX_DEFAULT_NODES}个关键节点）`);
    }
  } catch (error) {
    ElMessage.error(`全屏操作失败：${error.message}`);
  }
};

// 请求全屏（兼容多浏览器）
const requestFullScreen = (element) => {
  if (element.requestFullscreen) {
    element.requestFullscreen();
  } else if (element.webkitRequestFullscreen) {
    element.webkitRequestFullscreen();
  } else if (element.msRequestFullscreen) {
    element.msRequestFullscreen();
  }
};

// 退出全屏（兼容多浏览器）
const exitFullScreen = () => {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.webkitExitFullscreen) {
    document.webkitExitFullscreen();
  } else if (document.msExitFullscreen) {
    document.msExitFullscreen();
  }
};

// 监听全屏状态变化
const handleFullScreenChange = () => {
  const fullscreenElement = document.fullscreenElement || 
                            document.webkitFullscreenElement || 
                            document.msFullscreenElement;
  const wasFullScreen = isFullScreen.value;
  isFullScreen.value = !!fullscreenElement;
  
  // 退出全屏时重新加载核心节点（前15个）
  if (wasFullScreen && !isFullScreen.value) {
    if (viewMode.value === 'graph') {
      if (!currentEntity.value || currentEntity.value === EMPTY_TEXT_PLACEHOLDER) {
        initGraph('', false);
      } else {
        initGraph(currentEntity.value, false);
      }
    }
  }
  
  if (network.value && viewMode.value === 'graph') {
    setTimeout(() => {
      network.value.redraw();
    }, 300);
  }
};

// 卸载时清理
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
  height: 550px;
  box-sizing: border-box;
}

.graph-container {
  position: relative;
  width: 100%;
  height: 500px;
  border-radius: 8px;
  box-sizing: border-box;
  background-color: #fff;
}

/* 加载提示（全屏时确保可见） */
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
  overflow: auto;
  padding: 15px;
  box-sizing: border-box;
}

.terms-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e6e6e6;
}

.terms-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.terms-header p {
  margin: 5px 0 0 0;
  font-size: 14px;
  color: #666;
}

.terms-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 词条加载骨架屏 */
.terms-loading {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.loading-skeleton {
  height: 48px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 6px;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

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

/* 修复vis-network样式冲突，增强碰撞可视化效果 */
:deep(.vis-network) {
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
}

:deep(.vis-node) {
  transition: all 0.2s;
  z-index: 100 !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1); /* 增加阴影，使碰撞更易观察 */
}

:deep(.vis-node:hover) {
  scale: 1.05;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

:deep(.vis-edge) {
  z-index: 1 !important;
  stroke-width: 2px !important;
  transition: all 0.3s;
}

:deep(.vis-edge:hover) {
  stroke-width: 3px !important;
  stroke: #409EFF !important;
}

:deep(.vis-edge-text) {
  background-color: rgba(255, 255, 255, 0.9) !important;
  padding: 3px 6px !important;
  border-radius: 4px !important;
  z-index: 50 !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
  font-weight: 500 !important;
}

/* 碰撞时的高亮效果 */
:deep(.vis-node.vis-selected) {
  scale: 1.1;
  box-shadow: 0 0 15px rgba(64, 158, 255, 0.5);
}

:deep(.vis-edge.vis-selected) {
  stroke-width: 4px !important;
  stroke: #409EFF !important;
}

/* 回溯按钮样式优化 */
.el-button--small {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 禁用按钮样式优化 */
.el-button--text.is-disabled {
  color: #c0c4cc !important;
  cursor: not-allowed !important;
}

/* 确保Element Plus提示在全屏时可见 */
:deep(.el-message) {
  z-index: 999999 !important;
}
</style>