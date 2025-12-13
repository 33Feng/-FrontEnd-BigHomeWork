import axios from 'axios';

const service = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
service.interceptors.request.use(
  config => {
    console.log('请求参数：', config);
    return config;
  },
  error => {
    console.error('请求错误：', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data;
    console.log('响应数据：', res);
    if (res.code !== 200) {
      console.error('请求失败：', res.msg);
      return Promise.reject(new Error(res.msg || '请求失败'));
    }
    return res;
  },
  error => {
    console.error('响应错误：', error.response || error);
    return Promise.reject(error);
  }
);

export const api = {
  // 获取核心图谱数据（少量节点，默认10个）
  getGraphData() {
    return service.get('/graph-data?limit=10');
  },
  // 获取全量图谱数据（用于全屏模式）
  getFullGraphData() {
    return service.get('/graph-data/full');
  },
  // 根据实体获取相关图谱数据
  getGraphDataByEntity(entity) {
    return service.get(`/graph-data/entity/${encodeURIComponent(entity)}`);
  },
  // 模糊搜索实体
  fuzzySearchEntity(keyword) {
    return service.get(`/graph-data/entity/fuzzy/${encodeURIComponent(keyword)}`);
  },
  // 问答接口
  qa(data, config = {}) {
    return service.post('/qa', data, config);
  },
  // 获取所有实体
  getEntities() {
    return service.get('/entities');
  }
};