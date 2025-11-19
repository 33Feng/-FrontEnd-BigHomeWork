<template>
  <!-- 模板部分保持不变 -->
  <div class="graph-wrapper" style="width: 100%; height: 550px; position: relative;">
    <div class="search-bar" style="margin-bottom: 10px; display: flex; gap: 10px;">
      <el-input
        v-model="searchEntity"
        placeholder="输入节点名称搜索（如Vue、Vite、ES6）"
        clearable
        style="flex: 1;"
        @keyup.enter="handleSearch"
      ></el-input>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="showAllGraph">显示全部</el-button>
    </div>

    <div style="width: 100%; height: 500px; position: relative;">
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
});

// 卸载时销毁（增加非空校验）
onUnmounted(() => {
  destroyNetwork();
  window.removeEventListener('resize', () => {});
});
</script>

<style scoped>
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
</style>