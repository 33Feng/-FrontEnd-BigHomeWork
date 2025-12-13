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
import { ref, onMounted, nextTick, onUnmounted, defineProps, defineEmits } from 'vue';
import { Network, DataSet } from 'vis-network/standalone';
import { ElButton, ElMessage, ElInput, ElIcon } from 'element-plus';
import { Fullscreen, Picture, Download, ArrowDown, Loading, ArrowLeft } from '@element-plus/icons-vue';
import { api } from '../api/index';

// 关系颜色映射函数 采用模糊匹配
const getRelationColor = (relation) => {
  const rel = (relation || '').trim();
  if (!rel) return '#A9A9A9'; // 空值默认灰

  // 【橙色系】版本、历史、时间相关
  if (['版本', '历史', '旧', 'Time'].some(k => rel.includes(k))) {
    return '#E6A23C'; 
  }

  // 【红色系】工具、框架、工程化、生态相关
  if (['框架', '工具', '编辑器', '管理', '容器', '部署', '规范', 'CI/CD', '处理器', '生态', '调试', '服务', 'Environment'].some(k => rel.includes(k))) {
    return '#F56C6C';
  }

  // 【青色系】性能、网络、安全、浏览器环境相关
  if (['优化', '性能', '加载', '渲染', '安全', '权限', '协议', '请求', '异步', '错误', '异常', '网络', 'Web', '客户端', '服务端', '浏览器', 'HTTP', 'DNS'].some(k => rel.includes(k))) {
    return '#00BCD4';
  }

  // 【金色/黄色系】事件、交互、通信、路由
  if (['事件', '通信', '路由', '交互', '监听', '导航', '行为', 'DOM'].some(k => rel.includes(k))) {
    return '#FFD700';
  }

  // 【紫色系】高阶概念、底层机制、模块化、抽象
  if (['机制', '原理', '模式', '环境', '作用域', '上下文', '模块', '依赖', '继承', '超集', '代理', '反射', '型变', '约束'].some(k => rel.includes(k))) {
    return '#9C27B0';
  }

  // 【绿色系】语法细节、代码元素、属性、样式
  if (['属性', '标签', '选择器', '样式', '语法', '指令', '方法', '函数', '声明', '规则', '类型', '参数', '变量', '操作', '钩子', '元素', '插槽', '装饰器', '泛型', '接口', '枚举', '数组', '对象', '字符串', '组件', '值'].some(k => rel.includes(k))) {
    return '#67C23A';
  }

  // 【蓝色系】核心结构、定义、标准、顶层分类 
  if (['核心', '组成', '环节', '领域', '标准', '组织', '定义', '概念', '维度', '进阶', '方案', '优势'].some(k => rel.includes(k))) {
    return '#409EFF';
  }

  // 默认颜色 (深灰色)
  return '#909399';
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
const EMPTY_TEXT_PLACEHOLDER = '无文本内容'; // 空文本占位符
const EMPTY_RELATION_PLACEHOLDER = '无关联'; // 空关系占位符

// 格式化空文本
const formatEmptyText = (text, placeholder = EMPTY_TEXT_PLACEHOLDER, skipTrim = false) => {
  if (!text) return placeholder;
  const processed = skipTrim ? text : text.trim();
  return processed === '' ? placeholder : processed;
};

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
const hasSubordinateContent = (entity, edges) => {
  if (!entity || entity === EMPTY_TEXT_PLACEHOLDER) return false;
  return edges.some(edge => edge.source === entity);
};

// 回溯到上一个节点
const backToPreviousNode = () => {
  if (nodeHistory.value.length <= 1) return;
  
  // 移除当前节点
  nodeHistory.value.pop();
  // 获取上一个节点
  const prevEntity = nodeHistory.value[nodeHistory.value.length - 1];
  
  searchEntity.value = prevEntity;
  currentEntity.value = prevEntity;
  emit('update:currentEntity', prevEntity);
  // 通知父组件更新推荐数据
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

  // 强制触发重绘
  graphRef.value.style.display = 'none';
  graphRef.value.offsetHeight;
  graphRef.value.style.display = 'block';
  
  const rect = graphRef.value.getBoundingClientRect();
  if (rect.width <= 10 || rect.height <= 10) {
    graphRef.value.style.minWidth = '300px';
    graphRef.value.style.minHeight = '300px';
    // 再次检查
    const newRect = graphRef.value.getBoundingClientRect();
    return newRect.width > 10 && newRect.height > 10;
  }
  
  return true;
};

// 初始化图谱
const initGraph = async (targetEntity = '', forceFull = false) => {
  if (viewMode.value !== 'graph') return;
  
  try {
    // 显示加载状态
    loading.value = true;
    
    // 销毁旧图谱
    destroyNetwork();
    
    // 检查容器有效性
    if (!checkContainerValidity()) {
      loading.value = false;
      return;
    }
    
    // 加载数据
    let res;
    if (targetEntity && targetEntity !== EMPTY_TEXT_PLACEHOLDER) {
      // 加载指定实体的数据
      res = await api.getGraphDataByEntity(targetEntity);
      isShowingFull.value = false;
    } else if (isFullScreen.value || forceFull) {
      // 全屏模式或强制全屏：加载全量数据
      res = await api.getFullGraphData();
      isShowingFull.value = true;
    } else {
      // 默认加载10个核心节点
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
    
    // 格式化节点数据：鲜艳蓝色+黑色边框+白色文字，优化光滑度
    const formattedNodes = Array.from(validNodeLabels).map(nodeLabel => ({
      id: nodeLabel,
      label: nodeLabel,
      size: Math.min(20 + Math.log(Array.from(validNodeLabels).length) * 3, 30),
      // 节点颜色配置：黑色边框+白色文字，与词条颜色风格一致
      color: {
        background: nodeLabel === currentEntity.value ? '#0C6ECD' : '#1989FA', // 选中节点更深的蓝色，默认节点鲜艳蓝色
        border: '#000000', // 边框设置为黑色
        text: '#FFFFFF' // 文字设置为白色
      },
      // 优化节点光滑度：轻微的阴影和圆角（ellipse形状本身圆润，补充阴影参数）
      shadow: {
        enabled: true,
        color: 'rgba(0, 0, 0, 0.2)',
        size: 3,
        x: 1,
        y: 1
      }
    }));
    
    // 更新词条数据
    termsData.value = {
      nodes: formattedNodes,
      edges: formattedEdges
    };
    
    // 图谱数据
    const graphData = {
      nodes: new DataSet(formattedNodes),
      edges: new DataSet(formattedEdges.map(edge => ({
        from: edge.source,
        to: edge.target,
        label: edge.relation,
        color: {
          color: getRelationColor(edge.relation),
          highlight: '#FF0000'
        },
        font: {
          size: 12,
          strokeWidth: 0
        },
        width: Math.min(2 + (edge.weight || 0) / 5, 5)
      })))
    };
    
    // 图谱配置
    const options = {
      nodes: {
        shape: 'ellipse',
        font: {
          size: 14,
          color: '#FFFFFF', // 显式指定文字颜色为白色，确保兼容
          strokeWidth: 0
        },
        borderWidth: 1, // 边框宽度，配合黑色边框更清晰
        shadow: true // 启用阴影增强光滑感
      },
      edges: {
        smooth: {
          type: 'cubicBezier',
          forceDirection: 'vertical',
          roundness: 0.4
        },
        font: {
          align: 'middle'
        },
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 0.8
          }
        }
      },
      physics: {
        forceAtlas2Based: {
          gravitationalConstant: -26,
          centralGravity: 0.005,
          springLength: 230
        },
        maxVelocity: 146,
        solver: 'forceAtlas2Based',
        timestep: 0.35,
        stabilization: {
          enabled: true,
          iterations: 1000,
          updateInterval: 25
        }
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
        tooltipDelay: 200,
        hover: true
      },
      layout: {
        randomSeed: 2
      }
    };
    
    // 创建新图谱实例
    await nextTick();
    if (graphRef.value) {
      network.value = new Network(graphRef.value, graphData, options);
      
      // 图谱加载完成
      network.value.on('stabilizationIterationsDone', () => {
        loading.value = false;
        emit('graph-loaded', true);
      });
      
      // 节点点击事件：修复循环叠加问题
      network.value.on('click', (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const nodeLabel = nodeId;
          
          // 避免重复点击相同节点导致循环叠加
          if (nodeLabel === currentEntity.value) return;
          
          // 检查是否有下属内容
          const hasContent = hasSubordinateContent(nodeLabel, formattedEdges);
          if (!hasContent) {
            ElMessage.info({
              message: `「${nodeLabel}」无下属关联内容`,
              type: 'info',
              duration: 2000,
              zIndex: 999999
            });
            return;
          }
          
          // 添加到历史记录
          if (nodeHistory.value[nodeHistory.value.length - 1] !== nodeLabel) {
            nodeHistory.value.push(nodeLabel);
          }
          
          searchEntity.value = nodeLabel;
          currentEntity.value = nodeLabel;
          emit('update:currentEntity', nodeLabel);
          emit('getRecommendData', nodeLabel);
          
          // 重新初始化图谱，避免节点叠加
          initGraph(nodeLabel);
        }
      });

      // 监听物理引擎更新
      network.value.on('physicsUpdate', () => {
        if (network.value && formattedNodes.length > 1) {
          network.value.setOptions({
            physics: {
              collision: {
                enabled: true
              }
            }
          });
        }
      });

    } else {
      loading.value = false;
      ElMessage.error('图谱容器未准备好');
    }

  } catch (error) {
    console.error('图谱初始化错误：', error);
    ElMessage.error(`图谱加载失败：${error.message || '未知错误'}`);
    loading.value = false;
    destroyNetwork();
  }
};

// 加载词条数据：默认显示所有词条
const loadTermsData = async (entity = '') => {
  if (viewMode.value !== 'terms') return;
  
  loading.value = true;
  try {
    let res;
    if (entity && entity !== EMPTY_TEXT_PLACEHOLDER) {
      // 有指定实体时，加载该实体相关数据
      res = await api.getGraphDataByEntity(entity);
    } else {
      // 无指定实体时，直接加载全量数据（默认显示所有词条）
      res = await api.getFullGraphData();
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
    ElMessage.error(`加载词条失败：${error.message || '未知错误'}`);
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
    return;
  }
  
  // 添加到历史记录
  if (nodeHistory.value[nodeHistory.value.length - 1] !== entity) {
    nodeHistory.value.push(entity);
  }
  
  currentEntity.value = entity;
  emit('update:currentEntity', entity);
  // 通知父组件更新推荐数据
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
  // 通知父组件清空推荐数据
  emit('getRecommendData', '');
  
  nodeHistory.value = [];
  
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
    ElMessage.warning('无可用数据导出');
    return;
  }
  
  try {
    const jsonStr = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    const fileName = currentEntity.value && currentEntity.value !== EMPTY_TEXT_PLACEHOLDER
      ? `knowledge-graph-${currentEntity.value}.json` 
      : 'frontend-knowledge-graph.json';
    link.download = fileName;
    
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 100);
    
    ElMessage.success('数据已导出为JSON');
  } catch (e) {
    ElMessage.error('导出JSON失败：' + e.message);
  }
};

// 处理全屏状态变化
const handleFullScreenChange = () => {
  const isFull = !!document.fullscreenElement || 
                 !!document.webkitFullscreenElement || 
                 !!document.msFullscreenElement;
  isFullScreen.value = isFull;
  
  // 退出全屏时重新加载数据
  if (!isFull) {
    if (viewMode.value === 'graph') {
      initGraph(currentEntity.value || '', false);
    } else {
      loadTermsData(currentEntity.value || '');
    }
  }
};

// 切换全屏模式
const toggleFullScreen = async () => {
  const container = document.querySelector('.graph-container');
  if (!container) {
    ElMessage.error('未找到图谱容器');
    return;
  }
  
  try {
    if (!isFullScreen.value) {
      // 进入全屏前加载全量数据
      if (viewMode.value === 'graph') {
        await initGraph(currentEntity.value || '', true);
      } else {
        await loadTermsData(currentEntity.value || '');
      }
      // 进入全屏
      if (container.requestFullscreen) {
        await container.requestFullscreen();
      } else if (container.webkitRequestFullscreen) {
        await container.webkitRequestFullscreen();
      } else if (container.msRequestFullscreen) {
        await container.msRequestFullscreen();
      }
      ElMessage.success(`已进入全屏模式，按ESC键可退出`);
    } else {
      // 退出全屏
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        await document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        await document.msExitFullscreen();
      }
      ElMessage.info(`已退出全屏模式`);
    }
  } catch (error) {
    ElMessage.error(`全屏操作失败：${error.message}`);
  }
};

// 处理搜索
const handleSearch = () => {
  let entity = searchEntity.value.trim();
  entity = formatEmptyText(entity);
  
  if (entity === EMPTY_TEXT_PLACEHOLDER) {
    showAllGraph();
    return;
  }
  
  // 检查是否有下属内容（预查询）
  const hasContent = async () => {
    try {
      const res = await api.getGraphDataByEntity(entity);
      const edges = res?.data?.edges || [];
      return edges.some(edge => edge.source === entity || edge.target === entity);
    } catch (error) {
      console.error('检查实体内容失败：', error);
      return false;
    }
  };
  
  hasContent().then(contentExists => {
    if (!contentExists) {
      ElMessage.warning(`未找到「${entity}」的相关数据`);
      return;
    }
    
    // 添加到历史记录
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
  });
};

// 组件挂载时初始化
onMounted(() => {
  // 监听全屏状态变化
  document.addEventListener('fullscreenchange', handleFullScreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
  document.addEventListener('msfullscreenchange', handleFullScreenChange);
  
  // 初始加载图谱
  if (props.mainEntity) {
    currentEntity.value = props.mainEntity;
    nodeHistory.value.push(props.mainEntity);
    initGraph(props.mainEntity);
  } else {
    initGraph();
  }
  
  // 监听窗口大小变化，重绘图谱
  window.addEventListener('resize', () => {
    if (network.value && viewMode.value === 'graph') {
      network.value.redraw();
    }
  });
});

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
/* 恢复原样式的核心样式配置 */
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

.graph-container.fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  z-index: 9999 !important;
  background-color: white;
  padding: 20px;
  border-radius: 0 !important;
}

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

/* 恢复原词条项样式 */
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
  color: #1989FA; /* 与节点颜色一致的鲜艳蓝色 */
  text-decoration: none;
  transition: all 0.2s;
}

.term-node:hover {
  background: #d1e7fd;
  text-decoration: underline;
  color: #0C6ECD; /* 与选中节点一致的深蓝色 */
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

/* 恢复原vis-network样式 */
:deep(.vis-network) {
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
}

/* 保留椭圆形节点的圆润样式，增强hover效果 */
:deep(.vis-node) {
  transition: all 0.2s;
  z-index: 100 !important;
  /* 配合节点配置，增强光滑感 */
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.2));
}

:deep(.vis-node:hover) {
  stroke: #000000 !important; /* hover时边框仍为黑色，增强一致性 */
  stroke-width: 3px !important; /* 增强hover时的边框效果 */
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

/* 全屏模式样式 */
.fullscreen .terms-container,
.fullscreen :deep(.vis-network) {
  height: calc(100% - 60px) !important;
}
</style>