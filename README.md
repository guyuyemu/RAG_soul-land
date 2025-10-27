# 斗罗大陆RAG系统

基于 **bge-large-zh-v1.5** 模型的中文 RAG（检索增强生成）系统，专为中文内容优化，支持语义检索、智能问答和知识图谱可视化。

## ✨ 核心特性

### 🔍 智能检索系统
- **语义检索**：使用 bge-large-zh-v1.5 模型进行深度语义理解
- **本地模型**：支持本地模型加载，无需联网下载
- **详细评分**：提供完整的相似度计算过程和评分解释
- **进度可视化**：所有处理过程都有清晰的进度条显示

### 📝 中文文本处理
- **jieba 分词**：专业的中文分词工具
- **自定义词典**：支持领域专有名词识别（如"唐门"、"唐三"、"外门弟子"）
- **智能分块**：基于句子边界的智能文本分块
- **停用词过滤**：内置中文停用词表

### 🤖 LLM 生成增强
- **提示词工程**：结构化的提示词构建系统
- **多模型支持**：兼容 OpenAI、Anthropic 等主流 LLM
- **上下文整合**：自动整合检索结果和用户问题
- **来源追溯**：生成的回答自动标注信息来源

### 🕸️ 知识图谱可视化
- **实体提取**：自动识别文本中的关键实体
- **关系挖掘**：提取 30+ 种实体间关系类型
- **交互式展示**：支持缩放、拖拽、搜索的 HTML 可视化
- **智能过滤**：展示前 500 个高频实体，减少冗余

## 📦 安装依赖

\`\`\`
pip install -r requirements.txt
\`\`\`

## 🚀 快速开始

### 1. 准备文档

将文本文件放入 `documents/` 目录：

\`\`\`
documents/
├── 斗罗大陆_第1章.txt

├── 斗罗大陆_第2章.txt
└── ...
\`\`\`

**数据集已上传，可以直接使用**
### 2. 配置模型路径

编辑 `config.py`，设置本地模型路径：

\`\`\`python
EMBEDDING_MODEL_NAME = "path/to/bge-large-zh-v1.5"
\`\`\`

### 3. 配置自定义词典

在 `custom_words.py` 中添加领域专有名词：

\`\`\`python
custom_words = [
    "唐门",
    "唐三", 
    "外门弟子",
    "昊天锤",
    "蓝银草",
    # 添加更多专有名词...
]
\`\`\`

### 4. 运行 RAG 系统

\`\`\`bash
python main.py
\`\`\`

系统会自动：
- ✓ 加载文档并分块
- ✓ 生成嵌入向量（带进度条）
- ✓ 构建检索索引
- ✓ 启动交互式问答

### 5. 生成知识图谱

\`\`\`bash
python build_knowledge_graph.py
\`\`\`

生成文件：
- `knowledge_graph.html` - 交互式网页（推荐）

## 💡 使用示例

### 交互式问答

\`\`\`
请输入您的问题（输入 'quit' 退出）: 唐三是谁？

🔍 检索到 3 个相关文档片段

📄 文档 1 (相似度: 0.8523)
来源: 斗罗大陆_第1章.txt
内容: 唐三，唐门外门弟子，因偷学内门绝学为唐门所不容...

💬 AI 回答:
唐三是唐门的外门弟子，他因为偷学了唐门的内门绝学而被唐门追杀...

📚 信息来源:
• 斗罗大陆_第1章.txt
• 斗罗大陆_第2章.txt
\`\`\`

### 知识图谱浏览

打开 `knowledge_graph.html`，您可以：
- 🔍 **搜索实体**：快速定位特定角色或概念
- 🖱️ **拖拽节点**：调整图谱布局
- 🔎 **缩放视图**：鼠标滚轮缩放
- 👆 **查看详情**：悬停查看实体关系详情

## 🎨 知识图谱特性

### 实体识别

系统会自动识别以下类型的实体：
- **人名**：唐三、小舞、戴沐白
- **地名**：诺丁城、史莱克学院
- **组织**：唐门、武魂殿
- **物品**：昊天锤、蓝银草
- **概念**：魂力、魂环、魂技

### 关系类型

支持 30+ 种关系模式：

**身份关系**
- 是、为、乃、属于

**归属关系**  
- 来自、出身于、隶属于

**社交关系**
- 认识、结识、遇见、朋友

**战斗关系**
- 战斗、对战、击败、战胜

**能力关系**
- 拥有、获得、掌握、学会

**情感关系**
- 喜欢、爱、恨、敬佩

### 可视化说明

- **节点颜色**：
  - 🟣 紫色 = 自定义词典中的专有名词
  - 🔵 蓝色 = 低频实体
  - 🟠 橙色 = 中频实体  
  - 🔴 红色 = 高频实体

- **节点大小**：根据实体出现频率动态调整

- **边的粗细**：根据关系强度（共现次数）调整

- **边的颜色**：不同关系类型使用不同颜色

## ⚙️ 配置说明

### config.py

\`\`\`python
# 模型配置
EMBEDDING_MODEL_NAME = "/path/to/bge-large-zh-v1.5"  # 本地模型路径
EMBEDDING_DIMENSION = 1024  # bge-large-zh-v1.5 的向量维度

# 文本处理
CHUNK_SIZE = 500  # 文本块大小（字符数）
CHUNK_OVERLAP = 50  # 文本块重叠大小

# 检索配置
TOP_K = 5  # 返回前 K 个最相关文档
SIMILARITY_THRESHOLD = 0.3  # 相似度阈值

# LLM 配置
LLM_PROVIDER = 
LLM_MODEL = 
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1000

# 知识图谱配置
KG_MAX_ENTITIES = 500  # 最多展示实体数
KG_MIN_ENTITY_FREQ = 2  # 实体最小出现次数
\`\`\`

## 📊 评分系统

### 语义相似度评分

系统使用余弦相似度计算查询与文档的语义相关性：

\`\`\`
相似度 = cos(query_vector, doc_vector)
范围: [-1, 1]，通常在 [0, 1] 之间
\`\`\`

**评分解释**：
- 0.8 - 1.0：高度相关
- 0.6 - 0.8：较为相关
- 0.4 - 0.6：一般相关
- 0.0 - 0.4：弱相关

## 🔧 高级功能

### 自定义 LLM 提供商

\`\`\`python
from generator import Generator

# 使用 OpenAI
generator = Generator(provider="openai", model="gpt-4")

# 使用 Anthropic
generator = Generator(provider="anthropic", model="claude-3-opus-20240229")
\`\`\`

### 批量文档处理

\`\`\`python
from rag_system import RAGSystem

rag = RAGSystem()
rag.load_documents("documents/")  # 自动加载所有 .txt 文件
\`\`\`

### 导出知识图谱数据

\`\`\`python
from knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()
kg.build_from_documents(documents)

# 导出为 JSON
kg.export_json("output/graph.json")

# 导出为 GraphML（可用于 Gephi 等工具）
kg.export_graphml("output/graph.graphml")
\`\`\`

## 📁 项目结构

\`\`\`
scripts/
├── config.py                    # 配置文件
├── custom_words.py              # 配置专有词
├── text_processor.py            # 文本处理（jieba 分词）
├── retriever.py                 # 检索器（bge-large-zh-v1.5）
├── reranker.py                  # 重排序器
├── generator.py                 # LLM 生成器
├── cache_manager.py             # 缓存管理
├── knowledge_graph.py           # 知识图谱构建
├── rag_system.py                # RAG 系统主类
├── main.py                      # 主程序入口
├── build_knowledge_graph.py     # 知识图谱生成脚本

\`\`\`

## 🐛 常见问题

### Q: 模型加载失败？
A: 确保模型路径正确，且包含所有必需文件（config.json, pytorch_model.bin 等）

### Q: 分词效果不好？
A: 在 `text_processor.py` 中添加更多自定义词到 `custom_words` 列表

### Q: 知识图谱太复杂？
A: 调整 `KG_MAX_ENTITIES` 参数减少展示的实体数量

### Q: LLM 生成失败？
A: 检查 API 密钥是否正确设置在环境变量中

### Q: 内存不足？
A: 减小 `CHUNK_SIZE` 或 `TOP_K` 参数，或使用更小的模型

## 📝 更新日志

### v2.0.0 (当前版本)
- ✨ 替换为 bge-large-zh-v1.5 模型
- ✨ 集成 jieba 分词和自定义词典
- ✨ 新增知识图谱可视化功能
- ✨ 优化交互界面，添加进度条
- ✨ 增强 LLM 提示词工程
- ✨ 详细的评分计算和解释

### v1.0.0
- 🎉 初始版本发布

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 Issue 联系我们。
