import axios from 'axios';

const service = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 60000, // 延长超时时间
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
    console.log('响应数据：', res); // 打印响应，方便调试
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
  getGraphData() {
    return service.get('/graph-data');
  },
  // 新增：按实体获取图谱数据
  getFullGraphData() {
    return service.get('/graph-data/full'); // 获取全量数据
  },
  getGraphDataByEntity(entity) {
    return service.get(`/graph-data/entity/${encodeURIComponent(entity)}`);
  },
  // 新增：模糊搜索接口
  fuzzySearchEntity(keyword) {
    return service.get(`/graph-data/entity/fuzzy/${encodeURIComponent(keyword)}`);
  },
  qa(question) {
    return service.post('/qa', { question });
  },
  getEntities() {
    return service.get('/entities');
  }
};
