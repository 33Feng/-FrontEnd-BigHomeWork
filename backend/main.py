from dotenv import load_dotenv
load_dotenv()  # 加载环境变量

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from knowledge_graph import FrontendKnowledgeGraph
import re

# 初始化FastAPI应用
app = FastAPI(title="前端技术知识图谱问答API")

# 配置跨域（解决前后端跨域问题）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化知识图谱
kg = FrontendKnowledgeGraph()

# 请求模型
class QuestionRequest(BaseModel):
    question: str

# API接口
@app.get("/api/graph-data")
async def get_graph_data():
    """获取知识图谱可视化数据"""
    try:
        return {"code": 200, "data": kg.get_graph_data(), "msg": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图谱数据失败：{str(e)}")

@app.post("/api/qa")
async def qa(request: QuestionRequest):
    """问答接口"""
    try:
        result = kg.answer_question(request.question)
        return {"code": 200, "data": result, "msg": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败：{str(e)}")

@app.get("/api/entities")
async def get_entities():
    """获取所有实体列表"""
    try:
        entities = list(kg.G.nodes)
        return {"code": 200, "data": entities, "msg": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体列表失败：{str(e)}")

# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# 在main.py中新增接口，支持按实体筛选图谱数据
@app.get("/api/graph-data/entity/{entity}")
async def get_graph_data_by_entity(entity: str):
    """根据实体获取相关的图谱数据"""
    try:
        # 过滤非法实体名称
        if not entity or entity.startswith('[object'):
            return {"code": 400, "data": {"nodes": [], "edges": []}, "msg": "无效的实体名称"}
        # 获取该实体的所有相关关系
        related_data = kg.query_relation(entity)
        # 提取相关节点（源节点+目标节点）
        related_nodes = {entity}
        for item in related_data:
            related_nodes.add(item['source'])
            related_nodes.add(item['target'])
        related_nodes = list(related_nodes)
        
        # 构建筛选后的节点和边
        nodes = [{"id": str(node), "label": str(node)} for node in related_nodes]
        edges = []
        for u, v, data in kg.G.edges(data=True):
            if u in related_nodes and v in related_nodes:
                edges.append({
                    "from": str(u),
                    "to": str(v),
                    "label": str(data.get('relation', '')),
                    "weight": int(data.get('weight', 0)),
                    "relation": str(data.get('relation', ''))
                })
        
        return {"code": 200, "data": {"nodes": nodes, "edges": edges}, "msg": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体图谱数据失败：{str(e)}")

# 新增：模糊搜索实体接口
@app.get("/api/graph-data/entity/fuzzy/{keyword}")
async def fuzzy_search_entity(keyword: str):
    """根据关键词模糊匹配实体"""
    try:
        if not keyword:
            return {"code": 400, "data": {"nodes": [], "edges": []}, "msg": "关键词不能为空"}
        
        # 模糊匹配所有包含关键词的实体（不区分大小写）
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        matched_entities = [
            node for node in kg.G.nodes 
            if pattern.search(str(node))  # 匹配节点名称
        ]
        
        # 提取匹配实体的所有关联关系
        related_nodes = set(matched_entities)
        related_edges = []
        for u, v, data in kg.G.edges(data=True):
            if str(u) in related_nodes or str(v) in related_nodes:
                related_nodes.add(str(u))
                related_nodes.add(str(v))
                related_edges.append({
                    "from": str(u),
                    "to": str(v),
                    "label": str(data.get('relation', '')),
                    "weight": int(data.get('weight', 0)),
                    "relation": str(data.get('relation', ''))
                })
        
        nodes = [{"id": node, "label": node} for node in related_nodes]
        return {"code": 200, "data": {"nodes": nodes, "edges": related_edges}, "msg": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模糊搜索失败：{str(e)}")
