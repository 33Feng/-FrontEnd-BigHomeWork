<<<<<<< HEAD
import markdown  # 新增：导入markdown库
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
        """使用DeepSeek大模型回答问题，结合知识图谱数据增强"""
        # 提取问题中的核心实体
        entities = [node for node in self.G.nodes if node in question]
        related_data = []
        if entities:
            # 获取相关实体的关系数据
            main_entity = max(entities, key=lambda x: len(x))
            related_data = self.query_relation(main_entity)
        
        # 构建知识图谱上下文
        kg_context = ""
        if related_data:
            kg_context = "根据知识图谱，我获取到以下相关信息：\n"
            for item in related_data:
                kg_context += f"- {item['source']} {item['relation']} {item['target']}（相关度：{item['weight']}/10）\n"
        
        # 调用DeepSeek API
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deepseek_api_key}"
            }
            
            # 构建提示词
            prompt = f"""请基于以下上下文信息回答问题。如果上下文没有相关信息，也可以根据你的知识回答。
上下文信息：
{kg_context}

问题：{question}
"""
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个前端技术专家，擅长解答各种前端技术问题。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            response = requests.post(
                self.deepseek_api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            # 关键修改：将Markdown格式的答案转换为HTML
            answer_markdown = response.json()["choices"][0]["message"]["content"]
            # 转换Markdown为HTML，并添加基础样式类
            answer = markdown.markdown(
                answer_markdown,
                extensions=[
                    'extra',  # 支持表格、代码块等扩展
                    'codehilite'  # 代码高亮（可选）
                ]
            )
            
        except Exception as e:
            print(f"DeepSeek API调用失败: {str(e)}")
            #  fallback到原有逻辑
            answer = "抱歉，暂时无法获取回答。"
            # 对fallback答案也进行HTML格式化
            if related_data:
                answer_parts = [f"<h4>关于「{main_entity}」的相关知识：</h4>"]
                for item in related_data:
                    answer_parts.append(f"<p>- {item['source']} <strong>{item['relation']}</strong> {item['target']}（相关度：{item['weight']}/10）</p>")
                answer = "\n".join(answer_parts)
            else:
                answer = "<p>抱歉，暂时无法获取回答。</p>"
        
        # 生成推荐（保持原有逻辑）
        recommendations = []
        if related_data:
            for item in sorted(related_data, key=lambda x: x['weight'], reverse=True)[:5]:
                recommendations.append({
                    "entity": item['target'] if item['source'] == main_entity else item['source'],
                    "reason": f"{item['source']} {item['relation']} {item['target']}",
                    "weight": item['weight']
                })
        
        return {
            "answer": answer,
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
        
=======
import markdown  # 新增：导入markdown库
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
        """使用DeepSeek大模型回答问题，结合知识图谱数据增强"""
        # 提取问题中的核心实体
        entities = [node for node in self.G.nodes if node in question]
        related_data = []
        if entities:
            # 获取相关实体的关系数据
            main_entity = max(entities, key=lambda x: len(x))
            related_data = self.query_relation(main_entity)
        
        # 构建知识图谱上下文
        kg_context = ""
        if related_data:
            kg_context = "根据知识图谱，我获取到以下相关信息：\n"
            for item in related_data:
                kg_context += f"- {item['source']} {item['relation']} {item['target']}（相关度：{item['weight']}/10）\n"
        
        # 调用DeepSeek API
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deepseek_api_key}"
            }
            
            # 构建提示词
            prompt = f"""请基于以下上下文信息回答问题。如果上下文没有相关信息，也可以根据你的知识回答。
上下文信息：
{kg_context}

问题：{question}
"""
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个前端技术专家，擅长解答各种前端技术问题。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            response = requests.post(
                self.deepseek_api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            # 关键修改：将Markdown格式的答案转换为HTML
            answer_markdown = response.json()["choices"][0]["message"]["content"]
            # 转换Markdown为HTML，并添加基础样式类
            answer = markdown.markdown(
                answer_markdown,
                extensions=[
                    'extra',  # 支持表格、代码块等扩展
                    'codehilite'  # 代码高亮（可选）
                ]
            )
            
        except Exception as e:
            print(f"DeepSeek API调用失败: {str(e)}")
            #  fallback到原有逻辑
            answer = "抱歉，暂时无法获取回答。"
            # 对fallback答案也进行HTML格式化
            if related_data:
                answer_parts = [f"<h4>关于「{main_entity}」的相关知识：</h4>"]
                for item in related_data:
                    answer_parts.append(f"<p>- {item['source']} <strong>{item['relation']}</strong> {item['target']}（相关度：{item['weight']}/10）</p>")
                answer = "\n".join(answer_parts)
            else:
                answer = "<p>抱歉，暂时无法获取回答。</p>"
        
        # 生成推荐（保持原有逻辑）
        recommendations = []
        if related_data:
            for item in sorted(related_data, key=lambda x: x['weight'], reverse=True)[:5]:
                recommendations.append({
                    "entity": item['target'] if item['source'] == main_entity else item['source'],
                    "reason": f"{item['source']} {item['relation']} {item['target']}",
                    "weight": item['weight']
                })
        
        return {
            "answer": answer,
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
        
>>>>>>> 55ae8cf3380320f92bf5bdce500c69b000d8bbf0
        return {"nodes": nodes, "edges": edges}