<template>
  <div class="graph-wrapper" style="width: 100%; height: 550px; position: relative;">
    <div class="search-bar" style="margin-bottom: 10px; display: flex; gap: 10px;">
      <!-- 左侧：搜索区域 -->
      <div style="display: flex; gap: 10px; flex: 1; max-width: 70%;">
        <el-input
          v-model="searchEntity"
          placeholder="输入节点名称搜索"
          clearable
          @keyup.enter="handleSearch"
        ></el-input>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="showAllGraph">显示全部</el-button>
      </div>

      <!-- 右侧：工具区域 -->
      <div style="display: flex; gap: 10px; align-items: center;">
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

    <!-- 修改：给图谱容器添加动态class，用于全屏样式控制 -->
    <div :class="['graph-container', { 'fullscreen': isFullScreen }]" style="width: 100%; height: 500px; position: relative;">
      <div v-if="loading" class="loading">
        {{ currentEntity ? `加载「${currentEntity}」相关图谱...` : '加载知识图谱中...' }}
      </div>
      <div 
        ref="graphRef" 
        style="width: 100%; height: 100%; border: 1px solid #e6e6e6; border-radius: 8px;"
      ></div>
      <el-button 
        type="text" 
        @click="initGraph" 
        style="position: absolute; bottom: 10px; right: 10px;"
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
import { ElButton, ElMessage, ElInput } from 'element-plus';
// 原有导入保留，新增：导入全屏图标
import { Fullscreen, Picture, Download, ArrowDown } from '@element-plus/icons-vue';
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
const network = ref(null); // 图谱实例（初始为null）
const loading = ref(true);
const searchEntity = ref('');
const currentEntity = ref('');
// 原有响应式数据保留，新增：全屏状态标识
const isFullScreen = ref(false); // 控制全屏状态

// 销毁图谱实例（增加非空校验）
const destroyNetwork = () => {
  if (network.value) {
    // 先移除所有事件监听，再销毁
    network.value.off('stabilizationIterationsDone');
    network.value.off('click');
    network.value.destroy();
    network.value = null; // 销毁后重置为null
  }
};

// 初始化图谱（核心修复：全程非空校验）
const initGraph = async (targetEntity = '') => {
  try {
    loading.value = true;
    destroyNetwork(); // 先销毁旧实例，避免内存泄漏

    // 等待DOM完全渲染
    await nextTick();

    // 1. 校验DOM容器
    if (!graphRef.value) {
      ElMessage.error('图谱容器不存在，无法初始化！');
      loading.value = false;
      return; // 终止执行，避免后续报错
    }

    // 2. 校验容器尺寸
    const rect = graphRef.value.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
      ElMessage.error('图谱容器无有效尺寸，请检查布局！');
      loading.value = false;
      return; // 终止执行
    }

    // 3.确定当前实体（强制处理空值）
    let entity = typeof targetEntity === 'string' ? targetEntity.trim() : '';
    // 关键：如果明确传递空字符串，强制使用空实体（覆盖父组件传递的实体）
    entity = targetEntity === '' ? '' : (entity || currentEntity.value || props.mainEntity);
    currentEntity.value = entity;
    emit('update:currentEntity', entity);

    // 4. 获取图谱数据
    let res;
    try {
      if (entity) {
        res = await api.getGraphDataByEntity(entity);
      } else {
        // 无实体：强制调用全量接口（核心修复）
      res = await api.getGraphData();
      console.log('加载全量图谱数据：', res.data); // 调试日志
      }
    } catch (dataError) {
      ElMessage.error(`获取图谱数据失败：${dataError.message}`);
      loading.value = false;
      return; // 数据获取失败，终止执行
    }

    const { nodes, edges } = res.data;

    // 5. 校验数据有效性
    if (!nodes || !nodes.length) {
      ElMessage.warning(entity ? `未找到「${entity}」相关图谱数据` : '暂无图谱数据');
      loading.value = false;
      return; // 无数据，终止执行
    }

    // 6. 格式化数据
    const visNodes = new DataSet(
      nodes.map(node => ({
        id: node.id || node.label,
        label: node.label || node.id,
        shape: 'ellipse',
        size: 25,
        color: { 
          background: node.id === entity ? '#67C23A' : '#409EFF',
          border: node.id === entity ? '#529B2E' : '#1989FA' 
        }
      }))
    );

    const visEdges = new DataSet(
      edges.map(edge => ({
        from: edge.from,
        to: edge.to,
        label: edge.label || edge.relation,
        width: 2,
        color: '#999',
        arrows: { to: { enabled: true, scaleFactor: 0.7 } }
      }))
    );

    // 7. 图谱配置
    const options = {
      nodes: { font: { size: 14, color: '#333' } },
      edges: { font: { size: 12, align: 'middle' } },
      physics: {
        enabled: true,
        stabilization: { enabled: true, iterations: 500, fit: true },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 200,
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.1
        }
      },
      interaction: { 
        hover: true, 
        tooltipDelay: 200,
        dragNodes: true,
        zoomView: true
      }
    };

    // 8. 创建图谱实例（核心：确保实例创建成功）
    try {
      network.value = new Network(graphRef.value, { nodes: visNodes, edges: visEdges }, options);
    } catch (initError) {
      ElMessage.error(`图谱实例创建失败：${initError.message}`);
      loading.value = false;
      return; // 实例创建失败，终止执行
    }

    // 9. 绑定事件（关键：先校验network.value非空）
    if (network.value) {
      // 绑定稳定完成事件
      network.value.on('stabilizationIterationsDone', () => {
        loading.value = false;
        network.value?.setOptions({ physics: { enabled: true } }); // 可选链操作
        // 聚焦核心实体（增加非空校验）
        if (entity && network.value) {
          network.value.focus(entity, { scale: 1.2, animation: true });
        }
      });

      // 绑定节点点击事件
      network.value.on('click', (params) => {
        if (params.nodes.length > 0 && network.value) { // 非空校验
          const nodeId = params.nodes[0];
          searchEntity.value = nodeId;
          handleSearch(); // 直接调用，不传递参数
        }
      });
    }

  } catch (error) {
    ElMessage.error(`图谱初始化失败：${error.message}`);
    loading.value = false;
    destroyNetwork(); // 异常时销毁实例
  }
};

// 处理搜索（移除参数，避免接收KeyboardEvent）
const handleSearch = () => {
  let entity = searchEntity.value.trim();
  // 过滤非法字符
  entity = entity.replace(/\[object .+\]/g, '').trim();
  if (!entity) {
    ElMessage.warning('请输入有效的节点名称！');
    return;
  }
  currentEntity.value = entity;
  initGraph(entity);
};

// 显示全量图谱（完整重置状态）
const showAllGraph = () => {
  // 1. 清空搜索框
  searchEntity.value = '';
  // 2. 重置当前实体（关键：彻底清除实体状态）
  currentEntity.value = '';
  // 3. 通知父组件清除实体（确保联动状态一致）
  emit('update:currentEntity', '');
  // 4. 强制加载全量数据（传递空字符串明确标识全量）
  initGraph('');
};
// ================= 新增功能：导出图谱图片 =================
const exportGraphImage = () => {
  if (!network.value || !graphRef.value) {
    ElMessage.warning('图谱尚未加载，无法导出');
    return;
  }
  
  try {
    // 获取 canvas 元素
    const canvas = graphRef.value.querySelector('canvas');
    if (!canvas) {
      ElMessage.error('无法获取画布内容');
      return;
    }

    // 转换为 Data URL (PNG格式)
    const imgUrl = canvas.toDataURL('image/png');
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = imgUrl;
    // 文件名：如果有实体名则用实体名，否则用默认名
    const fileName = currentEntity.value 
      ? `knowledge-graph-${currentEntity.value}.png` 
      : 'frontend-knowledge-graph.png';
    link.download = fileName;
    
    // 触发下载
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    ElMessage.success('图谱图片已导出');
  } catch (e) {
    ElMessage.error('导出图片失败：' + e.message);
  }
};

//导出图谱 JSON
const exportGraphJSON = () => {
  if (!network.value) {
    ElMessage.warning('图谱尚未加载，无法导出');
    return;
  }

  try {
    // 从 network 实例中获取当前的节点和边数据
    // network.body.data.nodes 返回的是 DataSet，需要调用 .get() 转为数组
    const nodesData = network.value.body.data.nodes.get();
    const edgesData = network.value.body.data.edges.get();

    const data = {
      timestamp: new Date().toISOString(),
      entity: currentEntity.value || 'ALL',
      nodes: nodesData,
      edges: edgesData
    };

    // 转换为 JSON 字符串
    const jsonStr = JSON.stringify(data, null, 2);
    
    // 创建 Blob 对象
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = url;
    const fileName = currentEntity.value 
      ? `kg-data-${currentEntity.value}.json` 
      : 'kg-data-full.json';
    link.download = fileName;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url); // 释放内存

    ElMessage.success('图谱数据已导出');
  } catch (e) {
    ElMessage.error('导出 JSON 失败：' + e.message);
  }
};

// 监听问答面板实体变化（增加防抖）
watch(
  () => props.mainEntity,
  (newEntity) => {
    if (!currentEntity.value) {
      initGraph(newEntity);
    }
  },
  { immediate: true, flush: 'post' } // 延迟执行，确保DOM更新
);

// 挂载后初始化（增加延迟，确保DOM渲染完成）
onMounted(async () => {
  await nextTick();
  setTimeout(() => {
    initGraph();
  }, 300); // 延迟300ms，兼容慢渲染场景

  // 窗口resize监听（增加非空校验）
  window.addEventListener('resize', () => {
    if (network.value) {
      network.value.redraw();
    }
  });
  // 新增：绑定全屏事件监听
  document.addEventListener('fullscreenchange', handleFullScreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
  document.addEventListener('msfullscreenchange', handleFullScreenChange);
});
// 新增：全屏切换核心方法
const toggleFullScreen = () => {
  // 获取图谱容器DOM
  const container = document.querySelector('.graph-container');
  if (!container) return;

  try {
    if (!isFullScreen.value) {
      // 进入全屏（兼容多浏览器）
      if (container.requestFullscreen) {
        container.requestFullscreen();
      } else if (container.webkitRequestFullscreen) { // Chrome/Safari
        container.webkitRequestFullscreen();
      } else if (container.msRequestFullscreen) { // IE/Edge
        container.msRequestFullscreen();
      }
      ElMessage.success('已进入图谱全屏模式，按ESC键可退出');
    } else {
      // 退出全屏（兼容多浏览器）
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
      ElMessage.info('已退出图谱全屏模式');
    }
  } catch (error) {
    ElMessage.error(`全屏操作失败：${error.message}`);
  }
};

// 新增：监听全屏状态变化（同步isFullScreen，并重绘图谱）
const handleFullScreenChange = () => {
  // 检测当前是否处于全屏状态（兼容多浏览器）
  const fullscreenElement = document.fullscreenElement || 
                            document.webkitFullscreenElement || 
                            document.msFullscreenElement;
  isFullScreen.value = !!fullscreenElement;
  
  // 全屏状态变化时重绘图谱，避免尺寸异常
  if (network.value) {
    network.value.redraw();
  }
};
// 卸载时销毁（增加非空校验）
onUnmounted(() => {
  destroyNetwork();
  window.removeEventListener('resize', () => {});
  // 移除全屏监听
  document.removeEventListener('fullscreenchange', handleFullScreenChange);
});
</script>

<style scoped>
/* 原有loading样式保留 */
.loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  font-size: 16px;
  color: #666;
}

/* 新增：全屏状态下的容器样式 */
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
  box-sizing: border-box;
}

/* 深度选择器确保 vis-network 占满 */
.graph-container.fullscreen :deep(.vis-network) {
  width: 100% !important;
  height: 100% !important;
  outline: none;
}
</style>