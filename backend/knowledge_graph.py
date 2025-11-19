import networkx as nx
import pandas as pd
from typing import List, Dict, Tuple

class FrontendKnowledgeGraph:
    def __init__(self, data_path: str = "data/frontend_knowledge.csv"):
        # 初始化知识图谱
        self.G = nx.DiGraph()
        self.load_data(data_path)

    def load_data(self, data_path: str):
        """加载知识图谱数据"""
        df = pd.read_csv(data_path)
        for _, row in df.iterrows():
            self.G.add_edge(
                row['source'],
                row['target'],
                relation=row['relation'],
                weight=row['weight']
            )

    def query_relation(self, entity: str) -> List[Dict]:
        """查询实体相关关系"""
        if entity not in self.G.nodes:
            return []
        
        results = []
        # 出边（实体作为源节点）
        for neighbor in self.G.successors(entity):
            edge_data = self.G[entity][neighbor]
            results.append({
                "source": entity,
                "relation": edge_data['relation'],
                "target": neighbor,
                "weight": edge_data['weight']
            })
        # 入边（实体作为目标节点）
        for neighbor in self.G.predecessors(entity):
            edge_data = self.G[neighbor][entity]
            results.append({
                "source": neighbor,
                "relation": edge_data['relation'],
                "target": entity,
                "weight": edge_data['weight']
            })
        return results

    def answer_question(self, question: str) -> Dict:
        """问答匹配（简单关键词匹配）"""
        # 提取问题中的核心实体
        entities = [node for node in self.G.nodes if node in question]
        if not entities:
            return {
                "answer": "未找到相关知识，请尝试其他关键词（如Vue、Vue3、Vite等）",
                "related_entities": [],
                "recommendations": []
            }
        
        # 取匹配度最高的实体
        main_entity = max(entities, key=lambda x: len(x))
        related_data = self.query_relation(main_entity)
        
        # 生成回答
        answer_parts = [f"关于「{main_entity}」的相关知识："]
        for item in related_data:
            answer_parts.append(f"- {item['source']} {item['relation']} {item['target']}（相关度：{item['weight']}/10）")
        
        # 生成推荐（相关度前5的实体）
        recommendations = []
        for item in sorted(related_data, key=lambda x: x['weight'], reverse=True)[:5]:
            recommendations.append({
                "entity": item['target'] if item['source'] == main_entity else item['source'],
                "reason": f"{item['source']} {item['relation']} {item['target']}",
                "weight": item['weight']
            })
        
        return {
            "answer": "\n".join(answer_parts),
            "related_entities": entities,
            "recommendations": recommendations
        }

    def get_graph_data(self) -> Dict:
        """获取图谱可视化数据"""
        nodes = []
        for node in self.G.nodes:
            nodes.append({
                "id": str(node),  # 确保id为字符串（vis-network要求）
                "label": str(node)
            })
        
        edges = []
        for u, v, data in self.G.edges(data=True):
            edges.append({
                "from": str(u),   # 确保from/to为字符串
                "to": str(v),
                "label": str(data.get('relation', '')),
                "weight": int(data.get('weight', 0)),
                "relation": str(data.get('relation', ''))  # 兼容前端的relation字段
            })
        
        return {"nodes": nodes, "edges": edges}