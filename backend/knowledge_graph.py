import markdown
import networkx as nx
import pandas as pd
from typing import List, Dict, Tuple
import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class FrontendKnowledgeGraph:
    def __init__(self, data_path: str = "data/frontend_knowledge.csv"):
        # 初始化知识图谱
        self.G = nx.DiGraph()
        self.load_data(data_path)
         # 初始化DeepSeek API配置
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_api_url = os.getenv("DEEPSEEK_API_URL")
        if not self.deepseek_api_key:
            raise ValueError("请配置DEEPSEEK_API_KEY环境变量")

    def load_data(self, data_path: str):
        """加载知识图谱数据"""
        try:
            df = pd.read_csv(data_path, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            # 删除空行
            df.dropna(subset=['source', 'target'], inplace=True)
            # 权重处理
            if 'weight' in df.columns:
                df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(1).astype(int)
            else:
                df['weight'] = 1 
            count = 0
            for _, row in df.iterrows():
                source_node = str(row['source']).strip()
                target_node = str(row['target']).strip()
                
                if not source_node or not target_node:
                    continue

                self.G.add_edge(
                    source_node,
                    target_node,
                    relation=str(row.get('relation', '')), 
                    weight=int(row['weight'])
                )
                count += 1
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            pass
    
    def get_top_graph_data(self, limit: int = 10) -> Dict:
        """
        获取核心图谱数据（按节点度数排序，只显示重要节点）
        默认只返回10个核心节点，确保初始视图简洁
        """
        # 1. 计算所有节点的度（连接数），并按降序排序
        sorted_nodes = sorted(self.G.degree, key=lambda x: x[1], reverse=True)
        
        # 2. 取前 limit 个节点作为核心节点
        top_nodes_list = [node for node, degree in sorted_nodes[:limit]]
        top_nodes_set = set(top_nodes_list)
        
        # 3. 构建返回的节点列表
        nodes = []
        for node in top_nodes_list:
            nodes.append({
                "id": str(node),
                "label": str(node),
                "value": self.G.degree[node] 
            })
            
        # 4. 构建返回的边列表（只保留核心节点之间的连线）
        edges = []
        for u, v, data in self.G.edges(data=True):
            if u in top_nodes_set and v in top_nodes_set:
                edges.append({
                    "from": str(u),
                    "to": str(v),
                    "label": str(data.get('relation', '')),
                    "weight": int(data.get('weight', 0)),
                    "relation": str(data.get('relation', ''))
                })
                
        return {"nodes": nodes, "edges": edges}        

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

    def answer_question(self, question: str, mode: str = "quick") -> Dict:
        """使用DeepSeek大模型回答问题，结合知识图谱数据增强"""
        # 提取问题中的核心实体
        entities = [node for node in self.G.nodes if node in question]
        related_data = []
        if entities:
            main_entity = max(entities, key=lambda x: len(x))
            related_data = self.query_relation(main_entity)
    
        # 构建知识图谱上下文
        kg_context = ""
        if related_data:
            kg_context = "根据知识图谱，我获取到以下相关信息：\n"
            for item in related_data:
                kg_context += f"- {item['source']} {item['relation']} {item['target']}（相关度：{item['weight']}/10）\n"
    
        # 根据模式调整提示词和超时时间
        if mode == "quick":
            # 快速回答提示词
            prompt = f"""请基于以下上下文信息，用简洁的语言快速回答问题，控制在5-7秒内完成。
上下文信息：
{kg_context}

问题：{question}
"""
            timeout = 7  # 快速回答超时时间（秒）
        else:
            # 深度回答提示词
            prompt = f"""请基于以下上下文信息，进行深入思考后详细回答问题，
可以分点阐述，提供更全面的信息和分析，并给出完整严谨科学的回答,请一定要完整给出答案。
上下文信息：
{kg_context}

问题：{question}
"""
            timeout = 200  # 深度回答超时时间（秒）
    
        # 调用DeepSeek API
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deepseek_api_key}"
            }
        
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个前端技术专家，擅长解答各种前端技术问题。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7 if mode == "deep" else 0.3,  # 深度回答温度更高
                "max_tokens": 3000 if mode == "deep" else 300   # 深度回答字数更多
            }
        
            response = requests.post(
                self.deepseek_api_url,
                headers=headers,
                json=data,
                timeout=timeout  # 使用根据模式设置的超时时间
            )
        
            response.raise_for_status()
            answer_markdown = response.json()["choices"][0]["message"]["content"]
            answer = markdown.markdown(
                answer_markdown,
                extensions=[
                    'extra',
                    'codehilite'
                ]
            )
        
        except Exception as e:
            print(f"DeepSeek API调用失败: {str(e)}")
            # fallback逻辑
            answer = "抱歉，暂时无法获取回答。"
            if related_data:
                answer_parts = [f"<h4>关于「{main_entity}」的相关知识：</h4>"]
                for item in related_data:
                    answer_parts.append(f"<p>- {item['source']} <strong>{item['relation']}</strong> {item['target']}（相关度：{item['weight']}/10）</p>")
                answer = "\n".join(answer_parts)
            else:
                answer = "<p>抱歉，暂时无法获取回答。</p>"
    
        # 生成推荐
        recommendations = []
        if related_data:
            for item in sorted(related_data, key=lambda x: x['weight'], reverse=True)[:5]:
                recommendations.append({
                    "entity": item['target'] if item['source'] == main_entity else item['source'],
                    "reason": f"{item['source']} {item['relation']} {item['target']}",
                    "weight": int(item['weight'])
                })
    
        return {
            "answer": answer,
            "related_entities": entities,
            "recommendations": recommendations
        }

    def get_graph_data(self) -> Dict:
        """获取全部图谱可视化数据（用于全屏模式）"""
        nodes = []
        for node in self.G.nodes:
            nodes.append({
                "id": str(node),  # 确保id为字符串
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