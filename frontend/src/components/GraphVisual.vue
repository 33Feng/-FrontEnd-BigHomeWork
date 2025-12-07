<template>
  <div class="graph-wrapper" style="width: 100%; height: 550px; position: relative;">
    <!-- 顶部导航栏：标题 + 右侧功能按钮（含视图切换） -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
      
      <!-- 右侧功能按钮组：视图切换 + 导出 + 全屏 -->
      <div style="display: flex; gap: 10px; align-items: center;">
        <!-- 视图切换按钮（移至此处，保持蓝绿切换逻辑） -->
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

    <!-- 搜索区域（独立一行，不被压缩） -->
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
      <!-- 仅保留右上角加载提示 -->
      <div v-if="loading" class="loading-tip">
        <el-icon style="margin-right: 5px;"><Loading /></el-icon>
        {{ currentEntity ? `加载「${currentEntity}」数据...` : '加载中...' }}
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
          <p v-if="currentEntity">当前实体: {{ currentEntity }}</p>
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
            <div class="term-node">{{ edge.source }}</div>
            <div class="term-relation">{{ edge.relation }}</div>
            <div class="term-node">{{ edge.target }}</div>
            <el-button 
              type="text" 
              size="small" 
              @click="handleTermClick(edge.source === currentEntity ? edge.target : edge.source)"
            >
              查看详情
            </el-button>
          </div>
          
          <!-- 无数据时显示友好提示 -->
          <div v-else class="no-data">
            没有相关实体关系数据
          </div>
        </div>
      </div>
      
      <el-button 
        type="text" 
        @click="initGraph" 
        style="position: absolute; bottom: 10px; right: 10px; z-index: 10;"
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
import { Fullscreen, Picture, Download, ArrowDown, Loading } from '@element-plus/icons-vue';

// 接收父组件传递的核心实体
const props = defineProps({
  mainEntity: {
    type: String,
    default: ''
  }
});

// 向父组件发送当前选中的实体
const emit = defineEmits(['update:currentEntity']);

// 响应式数据
const graphRef = ref(null);
const network = ref(null); // 图谱实例
const loading = ref(false); // 加载状态（默认false）
const searchEntity = ref('');
const currentEntity = ref('');
const isFullScreen = ref(false);
const viewMode = ref('graph'); // 视图模式：graph/terms
const termsData = ref({ nodes: [], edges: [] }); // 词条数据
const initRetryCount = ref(0); // 初始化重试计数器

// 切换视图模式（功能逻辑不变）
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

// 加载词条数据（功能逻辑不变）
const loadTermsData = async (entity = '') => {
  try {
    loading.value = true;
    let res;
    
    // 优化请求逻辑：entity为空时加载全量数据
    if (entity.trim()) {
      res = await api.getGraphDataByEntity(encodeURIComponent(entity.trim()));
    } else {
      res = await api.getFullGraphData ? await api.getFullGraphData() : await api.getGraphData();
    }
    
    // 数据强容错处理
    const data = res?.data || { nodes: [], edges: [] };
    const formattedEdges = [];
    
    // 格式化边数据：兼容不同后端返回格式（from/to 或 source/target）
    if (Array.isArray(data.edges)) {
      formattedEdges.push(...data.edges.map(edge => ({
        source: edge.source || edge.from || '未知实体',
        target: edge.target || edge.to || '未知实体',
        relation: edge.relation || edge.label || '相关'
      })));
    }
    
    // 过滤无效边
    termsData.value = {
      nodes: Array.isArray(data.nodes) ? data.nodes : [],
      edges: formattedEdges.filter(edge => 
        edge.source && edge.target && edge.relation && edge.source !== edge.target
      )
    };
    
    // 无数据提示
    if (termsData.value.edges.length === 0) {
      ElMessage.info(entity ? `未找到「${entity}」相关实体关系` : '暂无实体关系数据');
    }
  } catch (error) {
    ElMessage.error(`加载词条数据失败：${error.message || '网络错误'}`);
    console.error('词条数据加载错误：', error);
    termsData.value = { nodes: [], edges: [] };
  } finally {
    loading.value = false;
  }
};

// 处理词条点击（功能逻辑不变）
const handleTermClick = (entity) => {
  if (!entity || !entity.trim()) return;
  
  searchEntity.value = entity.trim();
  currentEntity.value = entity.trim();
  emit('update:currentEntity', entity.trim());
  
  // 点击后保持在词条视图，更新数据
  loadTermsData(entity.trim());
};

// 销毁图谱实例（功能逻辑不变）
const destroyNetwork = () => {
  if (network.value) {
    try {
      network.value.off('stabilizationIterationsDone');
      network.value.off('click');
      network.value.destroy();
    } catch (e) {
      console.warn('销毁图谱实例警告：', e);
    } finally {
      network.value = null;
    }
  }
};

// 检查容器有效性（功能逻辑不变）
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

// 初始化图谱（功能逻辑不变）
const initGraph = async (targetEntity = '', isFull = false) => {
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
        setTimeout(() => initGraph(targetEntity, isFull), 800);
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
    currentEntity.value = entity;
    emit('update:currentEntity', entity);

    let res;
    try {
      if (entity) {
        res = await api.getGraphDataByEntity(encodeURIComponent(entity));
      } else if (isFull || !entity) { 
        res = await api.getFullGraphData ? await api.getFullGraphData() : await api.getGraphData();
      } else {
        res = await api.getGraphData();
      }
      
      // 同步更新词条数据
      const data = res?.data || { nodes: [], edges: [] };
      const formattedEdges = Array.isArray(data.edges) ? data.edges.map(edge => ({
        source: edge.source || edge.from || '未知实体',
        target: edge.target || edge.to || '未知实体',
        relation: edge.relation || edge.label || '相关'
      })).filter(edge => edge.source && edge.target && edge.relation) : [];
      
      termsData.value = {
        nodes: Array.isArray(data.nodes) ? data.nodes : [],
        edges: formattedEdges
      };
    } catch (apiError) {
      ElMessage.error(`数据请求失败：${apiError.message}`);
      loading.value = false;
      return; 
    }
    
    const { nodes = [], edges = [] } = res?.data || {};

    const validNodes = nodes
      .filter(node => node.id || node.label)
      .map(node => ({
        id: node.id || `node_${Date.now()}_${Math.random().toString(36).slice(2)}`,
        label: node.label || node.id || '未知节点',
        shape: 'ellipse',
        size: 25,
        color: { 
          background: (node.id || node.label) === entity ? '#67C23A' : '#409EFF',
          border: (node.id || node.label) === entity ? '#529B2E' : '#1989FA' 
        }
      }));

    const nodeIds = validNodes.map(n => n.id);
    const validEdges = edges
      .filter(edge => {
        const from = edge.from || edge.source;
        const to = edge.to || edge.target;
        return from && to && nodeIds.includes(from) && nodeIds.includes(to);
      })
      .map(edge => ({
        from: edge.from || edge.source,
        to: edge.to || edge.target,
        label: edge.label || edge.relation || '',
        width: 2,
        color: '#999',
        arrows: { to: { enabled: true, scaleFactor: 0.7 } }
      }));

    if (validNodes.length === 0) {
      ElMessage.warning(entity ? `未找到「${entity}」相关数据` : '暂无图谱数据');
      loading.value = false;
      return;
    }

    const options = {
      nodes: { 
        font: { size: 14, color: '#333', face: 'Arial' },
        shape: 'dot',
        scaling: {
          min: 15,
          max: 35,
          label: { enabled: true, min: 14, max: 20 }
        },
        borderWidth: 2
      },
      edges: { 
        font: { size: 10, align: 'middle', color: '#888', face: 'Arial' },
        color: { color: '#e2e2e2', highlight: '#409EFF' },
        smooth: { type: 'cubicBezier', forceDirection: 'horizontal' },
        hoverWidth: 3
      },
      physics: {
        enabled: true,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          theta: 0.5,
          gravitationalConstant: -100,
          centralGravity: 0.1,
          springConstant: 0.1,
          springLength: 120,
          damping: 0.6,
          avoidOverlap: 0.6
        },
        stabilization: {
          enabled: true,
          iterations: 200,
          updateInterval: 25,
          onlyDynamicEdges: false,
          fit: true
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
        randomSeed: 42
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
        network.value?.setOptions({
          physics: {
            enabled: true,
            stabilization: { enabled: false },
            forceAtlas2Based: { damping: 0.8 }
          }
        });
        if (entity) {
          const targetNode = validNodes.find(n => n.id === entity || n.label === entity);
          if (targetNode && network.value) {
            network.value.focus(targetNode.id, { scale: 1.3, animation: { duration: 1000 } });
          }
        }
      });

      network.value.on('click', (params) => {
        if (params.nodes.length > 0 && network.value) {
          const nodeId = params.nodes[0];
          const node = validNodes.find(n => n.id === nodeId);
          if (node) {
            searchEntity.value = node.label;
            handleSearch();
          }
        }
      });

    } catch (initError) {
      console.error('图谱实例创建失败：', initError);
      ElMessage.error(`图谱加载失败：${initError.message}`);
      loading.value = false;
      graphRef.value.innerHTML = '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#999;">图谱加载失败，请点击"重新加载"重试</div>';
      return;
    }

  } catch (error) {
    console.error('图谱初始化总错误：', error);
    ElMessage.error(`系统错误：${error.message}`);
    loading.value = false;
    destroyNetwork();
  }
};

// 处理搜索（功能逻辑不变）
const handleSearch = () => {
  let entity = searchEntity.value.trim();
  entity = entity.replace(/\[object .+\]/g, '').trim();
  if (!entity) {
    ElMessage.warning('请输入有效的节点名称！');
    return;
  }
  currentEntity.value = entity;
  emit('update:currentEntity', entity);
  
  if (viewMode.value === 'graph') {
    initGraph(entity);
  } else {
    loadTermsData(entity);
  }
};

// 显示全量数据（功能逻辑不变）
const showAllGraph = () => {
  searchEntity.value = '';
  currentEntity.value = '';
  emit('update:currentEntity', '');
  
  if (viewMode.value === 'graph') {
    initGraph('', true);
  } else {
    loadTermsData('');
  }
};

// 导出图谱图片（功能逻辑不变）
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
    const fileName = currentEntity.value 
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

// 导出数据（功能逻辑不变）
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
    const fileName = currentEntity.value 
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

// 监听父组件实体变化（功能逻辑不变）
watch(
  () => props.mainEntity,
  (newEntity) => {
    if (newEntity && newEntity.trim() && (!currentEntity.value || currentEntity.value !== newEntity.trim())) {
      currentEntity.value = newEntity.trim();
      if (viewMode.value === 'graph') {
        initGraph(newEntity.trim());
      } else {
        loadTermsData(newEntity.trim());
      }
    }
  },
  { immediate: true, flush: 'post' }
);

// 挂载后初始化（功能逻辑不变）
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

// 全屏切换（功能逻辑不变）
const toggleFullScreen = () => {
  const container = document.querySelector('.graph-container');
  if (!container) return;

  try {
    if (!isFullScreen.value) {
      if (container.requestFullscreen) {
        container.requestFullscreen();
      } else if (container.webkitRequestFullscreen) {
        container.webkitRequestFullscreen();
      } else if (container.msRequestFullscreen) {
        container.msRequestFullscreen();
      }
      ElMessage.success('已进入全屏模式，按ESC键可退出');
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
      ElMessage.info('已退出全屏模式');
    }
  } catch (error) {
    ElMessage.error(`全屏操作失败：${error.message}`);
  }
};

// 监听全屏状态变化（功能逻辑不变）
const handleFullScreenChange = () => {
  const fullscreenElement = document.fullscreenElement || 
                            document.webkitFullscreenElement || 
                            document.msFullscreenElement;
  isFullScreen.value = !!fullscreenElement;
  
  if (network.value && viewMode.value === 'graph') {
    setTimeout(() => {
      network.value.redraw();
    }, 300);
  }
};

// 卸载时清理（功能逻辑不变）
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

/* 加载提示（仅右上角） */
.loading-tip {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 20px;
  font-size: 14px;
  color: #666;
  display: flex;
  align-items: center;
  z-index: 20;
  backdrop-filter: blur(2px);
}

/* 全屏样式 */
.graph-container.fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
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

/* 修复vis-network样式冲突 */
:deep(.vis-network) {
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
}

:deep(.vis-node) {
  transition: all 0.2s;
}

:deep(.vis-node:hover) {
  scale: 1.05;
}

:deep(.vis-edge-text) {
  background-color: rgba(255, 255, 255, 0.8) !important;
  padding: 2px 4px !important;
  border-radius: 3px !important;
}
</style>