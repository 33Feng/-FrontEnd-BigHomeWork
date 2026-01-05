知识图谱推荐系统 (FrontEnd-BigHomeWork)
<div align="center">
<p>基于 Vue3 + Element Plus 构建的知识图谱可视化与智能推荐前端项目</p>
<img src="https://img.shields.io/badge/Vue-3.2+-4FC08D.svg?style=flat&logo=vue.js" alt="Vue Version">
<img src="https://img.shields.io/badge/Element%20Plus-2.11+-409EFF.svg?style=flat&logo=element-plus" alt="Element Plus Version">
<img src="https://img.shields.io/badge/Node.js-12+-339933.svg?style=flat&logo=node.js" alt="Node Version">
</div>
一、项目介绍
本项目是一套前后端结合的知识图谱智能推荐系统，前端基于 Vue3 + Element Plus 搭建可视化交互界面，后端通过 Python 实现知识图谱的实体关联分析与推荐逻辑，核心能力为基于图谱结构的实体权重排序推荐（提取权重前 8 的关联实体），同时提供美观的响应式 UI 与完善的代码规范体系。
二、技术栈
前端核心技术
框架：Vue 3.2+（组合式 API）
UI 组件库：Element Plus 2.11+
网络请求：Axios
知识图谱可视化：vis-network 9.1+
构建工具：Vue CLI 5.x
代码规范：ESLint + Vue ESLint Plugin
后端核心技术
语言：Python 3.8+
核心逻辑：知识图谱实体关联分析、权重排序推荐
三、环境要求
环境	版本要求	备注
Node.js	≥ 12.x（推荐 14+/16+）	建议使用 nvm 管理版本
npm/yarn	npm ≥ 6.x / yarn ≥ 1.22.x	包管理工具二选一
Python	≥ 3.8（后端）	运行知识图谱推荐逻辑
四、快速开始
1. 克隆项目
bash
运行
git clone <项目仓库地址>
cd FrontEnd-BigHomeWork
2. 前端环境搭建（核心指令保留）
进入前端目录，执行以下指令：
bash
运行
cd frontend

# 安装项目依赖（原有核心指令）
npm install

# 启动开发环境（编译并热重载，原有核心指令）
npm run serve

# 生产环境打包（编译并压缩，原有核心指令）
npm run build

# 代码检查与自动修复（原有核心指令）
npm run lint

3. 后端环境搭建
bash
运行
cd backend

# 创建虚拟环境（推荐）(可选)
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 安装后端依赖（需根据requirements.txt补充，如无则按需安装）
pip install -r requirements.txt

# 如果不搭键虚拟环境，可以根据以下步骤下载可能需要的后端文件
pip install requests python-dotenv
pip install markdown
pip install fastapi
pip install uvicorn
python -m pip install networkx
python -m pip install pandas

# 下载完毕后，按如下指令运行后端
python main.py 或者 python3 main.py

## 注意：启动前端和后端需要在不同终端(Terminal)运行
4. 配置自定义项（原有说明保留）
前端项目配置可参考 Vue CLI 官方文档：
Configuration Reference
五、项目结构说明
plaintext
FrontEnd-BigHomeWork/
├── frontend/                # 前端核心目录
│   ├── public/              # 静态资源（index.html、favicon等）
│   ├── src/
│   │   ├── api/             # 接口封装（问答/推荐接口）
│   │   ├── components/      # 业务组件（如RecommendPanel推荐面板）
│   │   ├── main.js          # 入口文件（Element Plus注册）
│   │   └── App.vue          # 根组件
│   ├── package.json         # 依赖与脚本配置
│   └── README.md            # 原始前端说明
├── backend/                 # 后端核心目录
│   ├── knowledge_graph.py   # 知识图谱推荐核心逻辑
│   └── .gitignore           # 后端忽略文件配置
└── .gitignore               # 全局忽略文件配置
六、核心功能
智能实体推荐：基于知识图谱结构，提取与目标实体关联的 Top8 节点，按权重降序展示（含关联关系说明）；
可视化交互：基于 vis-network 实现知识图谱可视化（扩展能力）；
响应式 UI：适配不同设备的美观界面，含 hover 动效、色彩区分等交互优化；
代码质量保障：ESLint 规范代码风格，自动修复常见问题；
生产环境优化：Vue CLI 打包压缩，生成高性能静态产物。
七、开发规范
代码风格：遵循 ESLint 配置（vue3-essential + eslint-recommended），禁止随意关闭规则；
组件开发：组件命名采用 PascalCase，样式模块化（避免全局污染）；
提交规范：建议遵循 Conventional Commits（如 feat: 新增推荐面板、fix: 修复推荐权重排序问题）；
依赖管理：禁止随意升级核心依赖（如 Vue/Element Plus），升级前需测试兼容性。
八、常见问题
npm install 失败：
检查 Node 版本是否符合要求；
切换 npm 源（如 npmmirror）：npm config set registry https://registry.npmmirror.com；
清除 npm 缓存：npm cache clean --force。
npm run serve 启动报错：
检查端口是否被占用（默认 8080），可修改 vue.config.js 指定端口；
确认 Element Plus 已正确注册（main.js 中检查 app.use (ElementPlus)）。
后端推荐接口无返回：
检查实体是否存在于知识图谱节点中；
确认虚拟环境已激活，依赖已安装。
九、忽略文件说明
项目.gitignore 已配置以下忽略规则，避免冗余 / 敏感文件提交：
前端：node_modules/、dist/、环境配置文件（.env.*.local）、编辑器配置（.vscode/.idea）；
后端：venv/、Python 缓存（pycache/*.pyc）、环境变量文件（.env）；
全局：系统临时文件（.DS_Store/Thumbs.db）、日志文件（*.log）。
十、维护说明
前端依赖更新：npm update（需测试兼容性）；
后端依赖更新：pip install --upgrade <包名>；
定期清理 node_modules：rm -rf node_modules && npm install（解决依赖冲突）。
<div align="right">
项目维护：前端技术知识问答与推荐团队 | 更新时间：2025年
</div>