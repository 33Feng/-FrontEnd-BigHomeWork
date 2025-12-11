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

// 处理词条点击
const handleTermClick = (entity) => {
  if (!entity || entity === EMPTY_TEXT_PLACEHOLDER) return;
  
  searchEntity.value = entity;
  handleSearch();
};

// 格式化空文本
const formatEmptyText = (text, placeholder = EMPTY_TEXT_PLACEHOLDER, isRelation = false) => {
  if (!text || typeof text !== 'string') {
    return placeholder;
  }
  
  const trimmed = text.trim();
  if (trimmed === '') {
    return placeholder;
  }
  
  return trimmed;
};

// 加载词条数据（模拟数据：若无api，可替换为本地模拟）
const loadTermsData = async (entity = '') => {
  loading.value = true;
  try {
    let res;
    entity = formatEmptyText(entity);
    
    // 模拟API请求：实际项目中替换为真实接口
    if (entity.trim() && entity !== EMPTY_TEXT_PLACEHOLDER) {
      // res = await api.getGraphDataByEntity(encodeURIComponent(entity.trim()));
      // 模拟数据
      res = {
        data: {
          nodes: [
            { id: 1, label: entity },
            { id: 2, label: `${entity}的父类` },
            { id: 3, label: `${entity}的子类` },
            { id: 4, label: `${entity}的相关技术` }
          ],
          edges: [
            { source: entity, target: `${entity}的父类`, relation: '继承自' },
            { source: entity, target: `${entity}的子类`, relation: '包含' },
            { source: entity, target: `${entity}的相关技术`, relation: '关联' },
            { source: `${entity}的相关技术`, target: 'Vue', relation: '基于' }
          ]
        }
      };
    } else {
      // res = await api.getGraphData();
      // 模拟数据
      res = {
        data: {
          nodes: [
            { id: 1, label: '前端开发' },
            { id: 2, label: 'Vue' },
            { id: 3, label: 'React' },
            { id: 4, label: 'JavaScript' }
          ],
          edges: [
            { source: '前端开发', target: 'Vue', relation: '核心框架' },
            { source: '前端开发', target: 'React', relation: '核心框架' },
            { source: 'Vue', target: 'JavaScript', relation: '基于' },
            { source: 'React', target: 'JavaScript', relation: '基于' }
          ]
        }
      };
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
      : [];
    
    termsData.value = { nodes: validNodes, edges: validEdges };
    // 通知父组件获取推荐数据
    emit('getRecommendData', currentEntity.value || props.mainEntity);
  } catch (error) {
    console.error('加载词条数据失败：', error);
    ElMessage.error(`加载失败：${error.message}`);
    termsData.value = { nodes: [], edges: [] };
  } finally {
    loading.value = false;
  }
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
      // 模拟API请求：实际项目中替换为真实接口
      if (entity && entity !== EMPTY_TEXT_PLACEHOLDER) {
        // res = await api.getGraphDataByEntity(encodeURIComponent(entity));
        res = {
          data: {
            nodes: [
              { id: 1, label: entity },
              { id: 2, label: `${entity}的父类` },
              { id: 3, label: `${entity}的子类` },
              { id: 4, label: `${entity}的相关技术` }
            ],
            edges: [
              { source: entity, target: `${entity}的父类`, relation: '继承自' },
              { source: entity, target: `${entity}的子类`, relation: '包含' },
              { source: entity, target: `${entity}的相关技术`, relation: '关联' },
              { source: `${entity}的相关技术`, target: 'Vue', relation: '基于' }
            ]
          }
        };
        isShowingFull.value = forceFull; // 仅标记为全屏状态，不改变数据加载逻辑
      } else if (isFullScreen.value || forceFull) {
        // res = await api.getFullGraphData ? await api.getFullGraphData() : await api.getGraphData();
        res = {
          data: {
            nodes: [
              { id: 1, label: '前端开发' },
              { id: 2, label: 'Vue' },
              { id: 3, label: 'React' },
              { id: 4, label: 'JavaScript' },
              { id: 5, label: 'CSS3' },
              { id: 6, label: 'HTML5' }
            ],
            edges: [
              { source: '前端开发', target: 'Vue', relation: '核心框架' },
              { source: '前端开发', target: 'React', relation: '核心框架' },
              { source: 'Vue', target: 'JavaScript', relation: '基于' },
              { source: 'React', target: 'JavaScript', relation: '基于' },
              { source: '前端开发', target: 'CSS3', relation: '样式层' },
              { source: '前端开发', target: 'HTML5', relation: '结构层' }
            ]
          }
        };
        isShowingFull.value = true;
      } else {
        // res = await api.getGraphData();
        res = {
          data: {
            nodes: [
              { id: 1, label: '前端开发' },
              { id: 2, label: 'Vue' },
              { id: 3, label: 'React' },
              { id: 4, label: 'JavaScript' }
            ],
            edges: [
              { source: '前端开发', target: 'Vue', relation: '核心框架' },
              { source: '前端开发', target: 'React', relation: '核心框架' },
              { source: 'Vue', target: 'JavaScript', relation: '基于' },
              { source: 'React', target: 'JavaScript', relation: '基于' }
            ]
          }
        };
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
      // 通知父组件获取推荐数据
      emit('getRecommendData', entity);
    } catch (apiError) {
      ElMessage.error(`数据请求失败：${apiError.message}`);
      loading.value = false;
      return; 
    }
    
    const { nodes = [], edges = [] } = res?.data || {};
    // 预处理边：格式化文本
    const rawEdges = Array.isArray(edges) ? edges.map(edge => ({
      source: formatEmptyText(edge.source || edge.from),
      target: formatEmptyText(edge.target || edge.to),
      relation: formatEmptyText(edge.relation || edge.label, EMPTY_RELATION_PLACEHOLDER, true)
    })).filter(edge => 
      edge.source && edge.target && edge.relation && 
      edge.source !== edge.target && 
      edge.source !== EMPTY_TEXT_PLACEHOLDER && 
      edge.target !== EMPTY_TEXT_PLACEHOLDER
    ) : [];

    // 提取所有有效节点标签
    const allNodeLabels = new Set();
    rawEdges.forEach(edge => {
      allNodeLabels.add(edge.source);
      allNodeLabels.add(edge.target);
    });
    
    // 处理节点数据：格式化并过滤
    const baseNodes = Array.isArray(nodes) 
      ? nodes.map(node => ({
          ...node,
          label: formatEmptyText(node.label || node.id || `node_${Date.now()}_${Math.random().toString(36).slice(2)}`)
        }))
      : [];
    
    // 如果没有节点数据，从边数据创建节点
    const edgeDerivedNodes = Array.from(allNodeLabels).map(label => ({
      label,
      id: `auto_${label.replace(/\s+/g, '_')}`
    }));
    
    // 合并节点，去重
    const combinedNodes = [...baseNodes, ...edgeDerivedNodes];
    const uniqueNodes = [];
    const seenLabels = new Set();
    
    combinedNodes.forEach(node => {
      if (!seenLabels.has(node.label)) {
        seenLabels.add(node.label);
        uniqueNodes.push(node);
      }
    });
    
    // 标记中心节点（当前实体）
    const centerLabel = entity !== EMPTY_TEXT_PLACEHOLDER ? entity : props.mainEntity || '';
    const isCenterNode = (label) => centerLabel && label === centerLabel;
    
    // 格式化节点数据：改为**更圆滑的椭圆形**，调整尺寸增强圆润感
    const validNodes = uniqueNodes
      .filter(node => node.label && node.label !== EMPTY_TEXT_PLACEHOLDER)
      .map(node => {
        const label = node.label;
        const isCenter = isCenterNode(label);
        let bgColor, borderColor;
        
        // 节点颜色策略（保持原样式的颜色逻辑）
        if (isCenter) {
          // 中心节点用绿色突出（原样式颜色）
          bgColor = '#67C23A';
          borderColor = '#529B2E';
        } else if (label === props.mainEntity && props.mainEntity) {
          // 核心实体（来自父组件）用蓝色（原样式颜色）
          bgColor = '#409EFF';
          borderColor = '#1989FA';
        } else {
          // 普通节点用默认蓝（原样式颜色）
          bgColor = '#409EFF'; 
          borderColor = '#1989FA';
        }

        return {
          id: node.id || `node_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          label: label,
          shape: 'ellipse', // 保留圆滑椭圆形的功能调整
          size: isCenter ? 40 : 25, // 原尺寸配置
          width: isCenter ? 50 : 30, // 保留椭圆形宽高配置
          height: isCenter ? 30 : 20, // 保留椭圆形宽高配置
          font: { 
            size: isCenter ? 16 : 14, 
            color: isCenter ? '#000' : '#333', 
            strokeWidth: 2,
            strokeColor: '#fff'
          },
          color: { 
            background: bgColor,
            border: borderColor,
            highlight: {
                background: bgColor,
                border: '#000'
            }
          },
          physics: true,
          mass: isCenter ? 2 : 1,
          borderWidth: 3, // 原边框宽度
          borderWidthSelected: 5 // 原选中边框宽度
        };
      });

    // 确保至少有一个节点显示（原逻辑）
    if (validNodes.length === 0) {
      validNodes.push({
        id: `node_empty_${Date.now()}`,
        label: entity !== EMPTY_TEXT_PLACEHOLDER ? entity : '无数据',
        shape: 'ellipse',
        size: 35,
        width: 45,
        height: 25,
        color: { 
          background: '#67C23A',
          border: '#529B2E'
        },
        physics: false,
        borderWidth: 3
      });
    }

    const nodeLabelMap = new Map(validNodes.map(n => [n.label, n.id]));

    // 过滤并格式化边数据（原逻辑）
    const validEdges = rawEdges
      .filter(edge => 
        nodeLabelMap.has(edge.source) && 
        nodeLabelMap.has(edge.target)
      )
      .map(edge => {
        const randomness = 0.6 + Math.random() * 0.4;
        const edgeColor = getRelationColor(edge.relation);
        return {
          from: nodeLabelMap.get(edge.source),
          to: nodeLabelMap.get(edge.target),
          label: edge.relation,
          width: 0.8,
          color: {
            color: edgeColor,
            highlight: edgeColor,
            hover: edgeColor
          },
          font: {
            size: 12,
            strokeWidth: 1,
            strokeColor: '#fff'
          },
          physics: true,
          springLength: 150 * randomness,
          springConstant: 0.15 / randomness
        };
      });

    // 配置vis-network选项（保持原样式的配置）
    const options = {
      nodes: {
        borderWidth: 3,
        borderWidthSelected: 5,
        shadow: {
          enabled: true,
          size: 10,
          color: 'rgba(0,0,0,0.1)'
        },
        chosen: true
      },
      edges: {
        color: { color: '#e2e2e2', highlight: '#409EFF' },
        smooth: { 
          type: 'cubicBezier', 
          forceDirection: 'horizontal',
          roundness: 0.3
        },
        hoverWidth: 3,
        zIndex: 1,
        margin: 20,
        labelOffset: 15
      },
      physics: {
        enabled: validNodes.length > 1,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          theta: 0.5,
          gravitationalConstant: -500,
          centralGravity: 0.08,
          springConstant: 0,
          springLength: 0,
          damping: 0.7,
          avoidOverlap: 0.9,
          edgeWeightInfluence: 15.0,
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
          iterations: 300,
          updateInterval: 25,
          onlyDynamicEdges: false,
          fit: true
        },
        repulsion: {
          nodeDistance: 200,
          centralGravity: 0.1,
          springLength: 200,
          springConstant: 0.03,
          damping: 0.1,
          edgeDistance: 50,
          edgeNodeDistance: 80
        },
        collision: {
          enabled: true,
          detection: 'all',
          handleOverlap: 0.8
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
        improvedLayout: true
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
      });

      // 节点点击事件（原逻辑）
      network.value.on('click', (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = network.value.body.data.nodes.get(nodeId);
          
          if (node && node.label) {
            const nodeLabel = node.label;
            
            // 检查是否是无效节点
            if (nodeLabel === EMPTY_TEXT_PLACEHOLDER) {
              ElMessage.warning('该节点无有效信息');
              return;
            }
            
            // 检查节点是否有下属内容
            const hasSubContent = validEdges.some(edge => edge.from === nodeId);
            if (!hasSubContent) {
              ElMessage.info({
                message: `「${nodeLabel}」无下属关联内容`,
                type: 'info',
                duration: 2000,
                zIndex: 999999
              });
              return;
            }
            
            searchEntity.value = nodeLabel;
            handleSearch();
          }
        }
      });

      // 监听物理引擎更新（原逻辑）
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

// 处理搜索（原逻辑）
const handleSearch = () => {
  let entity = searchEntity.value.trim();
  entity = formatEmptyText(entity);
  
  if (entity === EMPTY_TEXT_PLACEHOLDER) {
    ElMessage.warning('请输入有效的节点名称！');
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

// 显示核心节点（默认状态，原逻辑）
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

// 导出图谱图片（原逻辑）
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

// 导出数据（原逻辑）
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

// 切换全屏模式（原逻辑）
const toggleFullScreen = async () => {
  const container = document.querySelector('.graph-container');
  if (!container) {
    ElMessage.error('未找到图谱容器');
    return;
  }
  
  try {
    if (!isFullScreen.value) {
      // 进入全屏
      if (viewMode.value === 'graph') {
        if (!currentEntity.value || currentEntity.value === EMPTY_TEXT_PLACEHOLDER) {
          // 无当前节点：加载全部节点
          await initGraph('', true);
        } else {
          // 有当前节点：加载当前节点数据
          await initGraph(currentEntity.value, true);
        }
      }
      requestFullScreen(container);
      ElMessage.success(`已进入全屏模式（${currentEntity.value ? '显示当前节点' : '显示全部节点'}），按ESC键可退出`);
    } else {
      // 退出全屏
      exitFullScreen();
      ElMessage.info(`已退出全屏模式`);
    }
  } catch (error) {
    ElMessage.error(`全屏操作失败：${error.message}`);
  }
};

// 请求全屏（兼容多浏览器，原逻辑）
const requestFullScreen = (element) => {
  if (element.requestFullscreen) {
    element.requestFullscreen();
  } else if (element.webkitRequestFullscreen) {
    element.webkitRequestFullscreen();
  } else if (element.msRequestFullscreen) {
    element.msRequestFullscreen();
  }
};

// 退出全屏（兼容多浏览器，原逻辑）
const exitFullScreen = () => {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.webkitExitFullscreen) {
    document.webkitExitFullscreen();
  } else if (document.msExitFullscreen) {
    document.msExitFullscreen();
  }
};

// 监听全屏状态变化（原逻辑）
const handleFullScreenChange = () => {
  const fullscreenElement = document.fullscreenElement || 
                            document.webkitFullscreenElement || 
                            document.msFullscreenElement;
  const wasFullScreen = isFullScreen.value;
  isFullScreen.value = !!fullscreenElement;
  
  // 退出全屏时重新加载
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

// 初始化（原逻辑）
onMounted(() => {
  // 监听全屏变化
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

// 卸载时清理（原逻辑）
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

.terms-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  padding: 15px;
  box-sizing: border-box;
}

.terms-header {
  margin-bottom: 10px;
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

/* 恢复原滚动条样式 */
.terms-list-wrapper {
  width: 100%;
  height: calc(100% - 60px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 5px;
  box-sizing: border-box;
}

.terms-list-wrapper::-webkit-scrollbar {
  width: 6px;
}

.terms-list-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.terms-list-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.terms-list-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.terms-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

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
  color: #1989FA;
  text-decoration: none;
  transition: all 0.2s;
}

.term-node:hover {
  background: #d1e7fd;
  text-decoration: underline;
  color: #0c6ecd;
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

/* 保留椭圆形节点的圆润样式，其余恢复原节点样式 */
:deep(.vis-node) {
  transition: all 0.2s;
  z-index: 100 !important;
  border-radius: 60% !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

:deep(.vis-node:hover) {
  scale: 1.05;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
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

:deep(.vis-node.vis-selected) {
  scale: 1.1;
  box-shadow: 0 0 15px rgba(64, 158, 255, 0.5) !important;
}

:deep(.vis-edge.vis-selected) {
  stroke-width: 4px !important;
  stroke: #409EFF !important;
}

/* 恢复原按钮样式 */
.el-button--small {
  display: flex;
  align-items: center;
  gap: 4px;
}

.el-button--text.is-disabled {
  color: #c0c4cc !important;
  cursor: not-allowed !important;
}

:deep(.el-message) {
  z-index: 999999 !important;
}
</style>