"""
知识图谱生成模块 - 从文档中提取实体和关系，生成可视化知识图谱
"""
from typing import List, Dict, Tuple, Set
import re
from collections import defaultdict, Counter
import jieba.posseg as pseg
import networkx as nx
from pyvis.network import Network
from pathlib import Path
from tqdm import tqdm


class KnowledgeGraphBuilder:
    """知识图谱构建器 - 提取实体、识别关系、生成可视化图谱"""

    def __init__(self, custom_words: List[str] = None):
        """
        初始化知识图谱构建器

        参数:
            custom_words: 自定义词典（领域专有名词，如"唐门"、"唐三"等）
        """
        self.custom_words = set(custom_words or [])
        self.entities = set()  # 所有实体
        self.relations = []  # 所有关系 (实体1, 关系类型, 实体2)
        self.entity_frequency = Counter()  # 实体出现频率
        self.relation_details = defaultdict(list)  # 关系详细信息
        self.graph = nx.DiGraph()  # 有向图

        self.relation_patterns = [
            # 身份关系
            (r'(.+?)是(.+?)的(.+)', '身份'),
            (r'(.+?)担任(.+)', '担任'),
            (r'(.+?)成为(.+)', '成为'),
            
            # 归属关系
            (r'(.+?)属于(.+)', '属于'),
            (r'(.+?)来自(.+)', '来自'),
            (r'(.+?)出身(.+)', '出身'),
            
            # 位置关系
            (r'(.+?)位于(.+)', '位于'),
            (r'(.+?)在(.+?)中', '位于'),
            
            # 拥有关系
            (r'(.+?)拥有(.+)', '拥有'),
            (r'(.+?)获得(.+)', '获得'),
            (r'(.+?)得到(.+)', '得到'),
            
            # 技能关系
            (r'(.+?)使用(.+)', '使用'),
            (r'(.+?)施展(.+)', '施展'),
            (r'(.+?)掌握(.+)', '掌握'),
            (r'(.+?)修炼(.+)', '修炼'),
            (r'(.+?)学习(.+)', '学习'),
            
            # 教学关系
            (r'(.+?)教导(.+)', '教导'),
            (r'(.+?)指导(.+)', '指导'),
            (r'(.+?)传授(.+)', '传授'),
            
            # 战斗关系
            (r'(.+?)击败(.+)', '击败'),
            (r'(.+?)战胜(.+)', '战胜'),
            (r'(.+?)对战(.+)', '对战'),
            (r'(.+?)挑战(.+)', '挑战'),
            (r'(.+?)攻击(.+)', '攻击'),
            
            # 社交关系
            (r'(.+?)帮助(.+)', '帮助'),
            (r'(.+?)认识(.+)', '认识'),
            (r'(.+?)遇见(.+)', '遇见'),
            (r'(.+?)跟随(.+)', '跟随'),
            (r'(.+?)保护(.+)', '保护'),
            (r'(.+?)和(.+?)是(.+)', '关系'),
            (r'(.+?)与(.+?)(.+)', '关联'),
            
            # 创造关系
            (r'(.+?)创建(.+)', '创建'),
            (r'(.+?)建立(.+)', '建立'),
            (r'(.+?)制作(.+)', '制作'),
        ]

    def extract_entities(self, text: str) -> List[str]:
        """
        从文本中提取实体，优先识别自定义词典中的专有名词

        参数:
            text: 输入文本

        返回:
            实体列表
        """
        entities = []
        
        for custom_word in self.custom_words:
            if custom_word in text:
                # 计算出现次数
                count = text.count(custom_word)
                entities.extend([custom_word] * count)
                self.entity_frequency[custom_word] += count
        
        # 使用jieba分词提取其他实体
        words_with_pos = pseg.cut(text)

        for word, flag in words_with_pos:
            # 跳过已经在自定义词典中的词
            if word in self.custom_words:
                continue
                
            # nr: 人名, ns: 地名, nt: 机构名, nz: 其他专名
            if flag in ['nr', 'ns', 'nt', 'nz']:
                if len(word) >= 2:  # 至少2个字符
                    entities.append(word)
                    self.entity_frequency[word] += 1

        return entities

    def extract_relations(self, text: str, entities: List[str]) -> List[Tuple[str, str, str, str]]:
        """
        从文本中提取实体间的关系，返回详细的关系信息

        参数:
            text: 输入文本
            entities: 已提取的实体列表

        返回:
            关系四元组列表 [(实体1, 关系, 实体2, 上下文), ...]
        """
        relations = []
        entity_set = set(entities)

        for pattern, relation_type in self.relation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    entity1 = groups[0].strip()
                    entity2 = groups[1].strip()

                    # 验证是否为有效实体
                    if entity1 in entity_set and entity2 in entity_set:
                        # 提取上下文（匹配文本前后各20个字符）
                        start = max(0, match.start() - 20)
                        end = min(len(text), match.end() + 20)
                        context = text[start:end].replace('\n', ' ')
                        
                        relations.append((entity1, relation_type, entity2, context))

        sentences = re.split(r'[。！？；\n]+', text)
        for sentence in sentences:
            if len(sentence) < 5:  # 跳过太短的句子
                continue
                
            sentence_entities = [e for e in entity_set if e in sentence]

            # 如果句子中有2-5个实体，建立共现关系（避免过多实体导致关系爆炸）
            if 2 <= len(sentence_entities) <= 5:
                for i in range(len(sentence_entities) - 1):
                    entity1 = sentence_entities[i]
                    entity2 = sentence_entities[i + 1]  # 只连接相邻实体

                    # 提取两个实体之间的文本
                    start_idx = sentence.find(entity1) + len(entity1)
                    end_idx = sentence.find(entity2)

                    if 0 < start_idx < end_idx:
                        between_text = sentence[start_idx:end_idx].strip()
                        
                        words_with_pos = pseg.cut(between_text)
                        verbs = [w for w, f in words_with_pos if f.startswith('v') and len(w) >= 2]

                        if verbs:
                            relation_type = verbs[0]  # 使用第一个动词
                        else:
                            # 如果没有动词，检查是否有介词或连词
                            preps = [w for w, f in words_with_pos if f in ['p', 'c']]
                            if preps and len(between_text) <= 3:
                                relation_type = preps[0]
                            else:
                                continue  # 跳过没有明确关系的共现

                        relations.append((entity1, relation_type, entity2, sentence[:50]))

        return relations

    def build_graph_from_documents(self, documents: List[Dict]) -> None:
        """
        从文档列表构建知识图谱

        参数:
            documents: 文档列表，每个文档包含 'title' 和 'content'
        """
        print("\n" + "=" * 60)
        print("开始构建知识图谱")
        print("=" * 60)

        all_entities = []
        all_relations = []

        # 第一步：提取所有实体
        print("\n正在提取实体（优先识别自定义词典）...")
        for doc in tqdm(documents, desc="实体提取", ncols=80):
            content = doc.get('content', '')
            entities = self.extract_entities(content)
            all_entities.extend(entities)
            self.entities.update(entities)

        print(f"✓ 提取到 {len(self.entities)} 个唯一实体")
        
        custom_entities_found = [e for e in self.custom_words if e in self.entities]
        if custom_entities_found:
            print(f"✓ 识别到 {len(custom_entities_found)} 个自定义词典实体")
            top_custom = sorted(
                [(e, self.entity_frequency[e]) for e in custom_entities_found],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            print(f"  高频自定义实体: {', '.join([f'{e}({c})' for e, c in top_custom])}")

        # 第二步：提取关系
        print("\n正在提取实体关系...")
        for doc in tqdm(documents, desc="关系提取", ncols=80):
            content = doc.get('content', '')
            doc_entities = [e for e in self.entities if e in content]
            relations = self.extract_relations(content, doc_entities)
            all_relations.extend(relations)

        relation_dict = {}
        for entity1, relation, entity2, context in all_relations:
            key = (entity1, relation, entity2)
            if key not in relation_dict:
                relation_dict[key] = []
            relation_dict[key].append(context)
        
        self.relations = list(relation_dict.keys())
        self.relation_details = relation_dict

        print(f"✓ 提取到 {len(self.relations)} 个唯一关系")
        
        relation_types = Counter([r[1] for r in self.relations])
        print(f"✓ 关系类型统计: {dict(relation_types.most_common(10))}")

        # 第三步：构建图结构
        print("\n正在构建图结构...")
        for entity1, relation, entity2 in tqdm(self.relations, desc="构建图谱", ncols=80):
            # 添加节点
            if not self.graph.has_node(entity1):
                self.graph.add_node(
                    entity1,
                    frequency=self.entity_frequency[entity1],
                    type='custom' if entity1 in self.custom_words else 'entity'
                )

            if not self.graph.has_node(entity2):
                self.graph.add_node(
                    entity2,
                    frequency=self.entity_frequency[entity2],
                    type='custom' if entity2 in self.custom_words else 'entity'
                )

            # 添加边（关系）
            key = (entity1, relation, entity2)
            contexts = self.relation_details[key]
            
            if self.graph.has_edge(entity1, entity2):
                # 如果边已存在，合并关系
                self.graph[entity1][entity2]['weight'] += 1
                self.graph[entity1][entity2]['relations'].append(relation)
                self.graph[entity1][entity2]['contexts'].extend(contexts)
            else:
                self.graph.add_edge(
                    entity1,
                    entity2,
                    relation=relation,
                    weight=1,
                    relations=[relation],
                    contexts=contexts
                )

        print(f"✓ 图谱构建完成: {self.graph.number_of_nodes()} 个节点, {self.graph.number_of_edges()} 条边")

    def get_top_entities(self, top_n: int = 20) -> List[Tuple[str, int]]:
        """
        获取出现频率最高的实体

        参数:
            top_n: 返回前N个实体

        返回:
            (实体, 频率)列表
        """
        return self.entity_frequency.most_common(top_n)

    def get_entity_neighbors(self, entity: str, max_depth: int = 1) -> Dict:
        """
        获取实体的邻居节点

        参数:
            entity: 实体名称
            max_depth: 最大深度

        返回:
            邻居信息字典
        """
        if entity not in self.graph:
            return {"error": f"实体 '{entity}' 不在图谱中"}

        neighbors = {
            "entity": entity,
            "outgoing": [],  # 出边（该实体指向其他实体）
            "incoming": []   # 入边（其他实体指向该实体）
        }

        # 出边
        for target in self.graph.successors(entity):
            edge_data = self.graph[entity][target]
            neighbors["outgoing"].append({
                "target": target,
                "relation": edge_data.get('relation', '相关'),
                "weight": edge_data.get('weight', 1)
            })

        # 入边
        for source in self.graph.predecessors(entity):
            edge_data = self.graph[source][entity]
            neighbors["incoming"].append({
                "source": source,
                "relation": edge_data.get('relation', '相关'),
                "weight": edge_data.get('weight', 1)
            })

        return neighbors

    def visualize_interactive(self, output_path: str = "knowledge_graph.html", top_n: int=10) -> str:
        """
        生成交互式知识图谱网页（使用pyvis）- 美化版

        参数:
            output_path: 输出HTML文件路径
            top_n: 显示前N%个高频实体

        返回:
            输出文件路径
        """
        print(f"\n正在生成交互式知识图谱网页...")

        total_entities = len(self.entities)
        display_count = int(top_n*total_entities*0.01)
        print(f"  总实体数: {total_entities}, 显示前 {display_count} 个高频实体")

        # 获取高频实体子图
        top_entities = [e for e, _ in self.get_top_entities(display_count)]
        subgraph = self.graph.subgraph(top_entities)

        net = Network(
            height="950px",
            width="100%",
            bgcolor="#f8f9fa",
            font_color="#2c3e50",
            directed=True,
            notebook=False,
            cdn_resources='remote'
        )

        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "stabilization": {
              "enabled": true,
              "iterations": 200,
              "updateInterval": 25
            },
            "barnesHut": {
              "gravitationalConstant": -30000,
              "centralGravity": 0.5,
              "springLength": 150,
              "springConstant": 0.01,
              "damping": 0.7,
              "avoidOverlap": 0.8
            },
            "minVelocity": 0.75,
            "maxVelocity": 25
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": {
              "enabled": true
            },
            "zoomView": true,
            "dragView": true,
            "zoomSpeed": 0.5,
            "multiselect": true
          },
          "nodes": {
            "shape": "dot",
            "font": {
              "size": 15,
              "face": "Microsoft YaHei, SimHei, Arial",
              "color": "#2c3e50",
              "bold": {
                "color": "#1a252f"
              }
            },
            "borderWidth": 2.5,
            "borderWidthSelected": 4,
            "shadow": {
              "enabled": true,
              "color": "rgba(0,0,0,0.12)",
              "size": 6,
              "x": 2,
              "y": 2
            }
          },
          "edges": {
            "width": 2,
            "color": {
              "color": "#95a5a6",
              "highlight": "#e74c3c",
              "hover": "#3498db",
              "opacity": 0.75
            },
            "font": {
              "size": 14,
              "face": "Microsoft YaHei, SimHei, Arial",
              "color": "#2c3e50",
              "strokeWidth": 3,
              "strokeColor": "#ffffff",
              "align": "middle",
              "bold": {
                "color": "#1a252f",
                "size": 15
              }
            },
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.8,
                "type": "arrow"
              }
            },
            "smooth": {
              "enabled": true,
              "type": "continuous",
              "roundness": 0.5
            },
            "shadow": {
              "enabled": true,
              "color": "rgba(0,0,0,0.1)",
              "size": 5,
              "x": 2,
              "y": 2
            },
            "selectionWidth": 3
          },
          "layout": {
            "improvedLayout": true,
            "hierarchical": {
              "enabled": false
            }
          }
        }
        """)

        frequencies = [self.entity_frequency[node] for node in subgraph.nodes()]
        max_freq = max(frequencies) if frequencies else 1
        min_freq = min(frequencies) if frequencies else 1

        def get_node_color(entity, frequency):
            """根据实体类型和频率返回颜色"""
            if entity in self.custom_words:
                if frequency / max_freq > 0.7:
                    return '#8e44ad'  # 紫色 - 高频自定义实体
                else:
                    return '#9b59b6'  # 浅紫色 - 低频自定义实体
            
            # 普通实体使用渐变色
            if max_freq == min_freq:
                norm_freq = 0.5
            else:
                norm_freq = (frequency - min_freq) / (max_freq - min_freq)
            
            if norm_freq < 0.33:
                return '#3498db'  # 蓝色 - 低频
            elif norm_freq < 0.67:
                return '#f39c12'  # 橙色 - 中频
            else:
                return '#e74c3c'  # 红色 - 高频

        for node in subgraph.nodes():
            frequency = self.entity_frequency[node]
            node_color = get_node_color(node, frequency)
            is_custom = node in self.custom_words
            
            # 自定义实体节点更大
            base_size = 15 if is_custom else 10
            node_size = base_size + (frequency / max_freq) * 35
            
            # 构建详细的悬停信息
            node_type = "自定义实体" if is_custom else "实体"
            title = f"<b style='font-size:16px'>{node}</b><br>"
            title += f"<span style='color:#7f8c8d'>类型: {node_type}</span><br>"
            title += f"<span style='color:#7f8c8d'>出现次数: {frequency}</span><br>"
            title += "<span style='color:#95a5a6; font-size:12px'>点击查看详情</span>"
            
            net.add_node(
                node,
                label=node,
                title=title,
                size=node_size,
                color={
                    'background': node_color,
                    'border': '#2c3e50' if is_custom else '#34495e',
                    'highlight': {
                        'background': '#2ecc71',
                        'border': '#27ae60'
                    },
                    'hover': {
                        'background': '#1abc9c',
                        'border': '#16a085'
                    }
                },
                borderWidth=3 if is_custom else 2
            )

        for source, target, data in subgraph.edges(data=True):
            relations = data.get('relations', ['相关'])
            weight = data.get('weight', 1)
            contexts = data.get('contexts', [])
            
            # 合并多个关系
            relation_str = ', '.join(set(relations))
            
            # 边的宽度基于权重
            edge_width = 1.5 + min(weight * 1.5, 8)
            
            # 构建详细的悬停信息
            title = f"<div style='max-width:400px'>"
            title += f"<b style='font-size:15px'>{source}</b> → <b style='font-size:15px'>{target}</b><br>"
            title += f"<span style='color:#e74c3c'>关系: {relation_str}</span><br>"
            title += f"<span style='color:#3498db'>权重: {weight}</span><br>"
            
            # 添加上下文示例（最多3个）
            if contexts:
                title += "<br><b style='color:#2c3e50'>上下文示例:</b><br>"
                for i, ctx in enumerate(contexts[:3], 1):
                    title += f"<span style='font-size:12px; color:#7f8c8d'>{i}. {ctx[:60]}...</span><br>"
            
            title += "</div>"
            
            net.add_edge(
                source,
                target,
                label=relation_str,
                title=title,
                width=edge_width,
                color={
                    'color': '#95a5a6',
                    'highlight': '#e74c3c',
                    'hover': '#3498db'
                }
            )

        # 保存HTML
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        net.save_graph(str(output_path))

        self._enhance_html(output_path, display_count, total_entities)

        print(f"✓ 交互式图谱已保存: {output_path}")
        print(f"  在浏览器中打开查看: file://{output_path.absolute()}")
        print(f"\n💡 使用提示:")
        print(f"  • 鼠标滚轮缩放")
        print(f"  • 拖拽节点调整位置")
        print(f"  • 悬停查看详细关系信息")
        print(f"  • 紫色节点 = 自定义词典实体")
        print(f"  • 点击节点高亮相关连接")
        return str(output_path)

    def _enhance_html(self, html_path: Path, display_count: int, total_count: int):
        """
        增强HTML文件，添加自定义样式和说明

        参数:
            html_path: HTML文件路径
            display_count: 显示的实体数量
            total_count: 总实体数量
        """
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        enhanced_html = html_content.replace(
            '<body>',
            f'''<body>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                #header {{
                    background: rgba(255, 255, 255, 0.95);
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                #header h1 {{
                    margin: 0;
                    color: #2c3e50;
                    font-size: 28px;
                    font-weight: bold;
                }}
                #header p {{
                    margin: 10px 0 0 0;
                    color: #7f8c8d;
                    font-size: 14px;
                }}
                #stats {{
                    display: inline-block;
                    margin-top: 10px;
                    padding: 8px 16px;
                    background: #ecf0f1;
                    border-radius: 20px;
                    font-size: 13px;
                    color: #34495e;
                }}
                #legend {{
                    position: absolute;
                    top: 140px;
                    right: 20px;
                    background: rgba(255, 255, 255, 0.95);
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                    z-index: 1000;
                    max-width: 240px;
                }}
                #legend h3 {{
                    margin: 0 0 10px 0;
                    color: #2c3e50;
                    font-size: 16px;
                }}
                .legend-item {{
                    display: flex;
                    align-items: center;
                    margin: 8px 0;
                    font-size: 13px;
                }}
                .legend-color {{
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    margin-right: 10px;
                    border: 2px solid #2c3e50;
                }}
                #mynetwork {{
                    border-radius: 8px;
                    margin: 20px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                }}
            </style>
            <div id="header">
                <h1>🔍 知识图谱可视化</h1>
                <p>展示文档中的实体关系网络 | 鼠标滚轮缩放 | 拖拽节点调整位置 | 悬停查看详细关系</p>
                <div id="stats">
                    📊 显示 <strong>{display_count}</strong> / {total_count} 个高频实体
                </div>
            </div>
            <div id="legend">
                <h3>📊 图例说明</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background: #8e44ad;"></div>
                    <span>自定义实体（高频）</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #9b59b6;"></div>
                    <span>自定义实体（低频）</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #3498db;"></div>
                    <span>普通实体（低频）</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f39c12;"></div>
                    <span>普通实体（中频）</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #e74c3c;"></div>
                    <span>普通实体（高频）</span>
                </div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ecf0f1; font-size: 12px; color: #7f8c8d;">
                    <strong>提示：</strong><br>
                    • 节点大小 = 出现频率<br>
                    • 边的粗细 = 关系强度<br>
                    • 边标签 = 关系类型<br>
                    • 悬停边查看上下文<br>
                    • 支持多选和搜索
                </div>
            </div>
            '''
        )

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_html)

    def get_statistics(self) -> Dict:
        """
        获取知识图谱统计信息

        返回:
            统计信息字典
        """
        custom_entities_count = len([e for e in self.entities if e in self.custom_words])
        
        return {
            "total_entities": len(self.entities),
            "custom_entities": custom_entities_count,
            "total_relations": len(self.relations),
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
            "top_entities": self.get_top_entities(10),
            "relation_types": len(set([r[1] for r in self.relations])),
            "avg_degree": sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1)
        }
