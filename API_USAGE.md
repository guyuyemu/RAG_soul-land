# RAG知识问答系统 - API使用文档

## 快速开始

### 1. 安装依赖

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. 启动后端服务

\`\`\`bash
python app.py
\`\`\`

服务将在 `http://localhost:8080` 启动

### 3. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## API接口说明

### 健康检查

#### GET /api/health

检查系统运行状态

**响应示例:**
\`\`\`json
{
  "status": "healthy",
  "rag_system": "initialized",
  "kg_builder": "initialized",
  "timestamp": "2024-01-01T12:00:00"
}
\`\`\`

---

## 文件管理接口

### 1. 获取文件列表

#### GET /api/files

获取所有已上传的文档文件

**响应示例:**
\`\`\`json
[
  {
    "filename": "斗罗大陆.txt",
    "size": 1048576,
    "upload_time": "2024-01-01T12:00:00",
    "path": "斗罗大陆.txt"
  }
]
\`\`\`

### 2. 上传文件

#### POST /api/files/upload

上传新的文档文件

**请求:**
- Content-Type: multipart/form-data
- Body: file (文件)

**支持的文件格式:** .txt, .md, .pdf, .docx, .doc

**响应示例:**
\`\`\`json
{
  "message": "文件上传成功",
  "filename": "斗罗大陆.txt",
  "size": 1048576,
  "path": "斗罗大陆.txt"
}
\`\`\`

**curl示例:**
\`\`\`bash
curl -X POST "http://localhost:8000/api/files/upload" \
  -F "file=@斗罗大陆.txt"
\`\`\`

### 3. 删除文件

#### DELETE /api/files/{filename}

删除指定的文档文件

**路径参数:**
- filename: 文件名

**响应示例:**
\`\`\`json
{
  "message": "文件删除成功",
  "filename": "斗罗大陆.txt"
}
\`\`\`

**curl示例:**
\`\`\`bash
curl -X DELETE "http://localhost:8000/api/files/斗罗大陆.txt"
\`\`\`

### 4. 下载文件

#### GET /api/files/{filename}/download

下载指定的文档文件

**路径参数:**
- filename: 文件名

---

## 知识图谱接口

### 1. 生成知识图谱

#### POST /api/knowledge-graph/generate

从已上传的文档生成知识图谱

**请求体:**
\`\`\`json
{
  "top_n": 500
}
\`\`\`

**参数说明:**
- top_n: 显示前N个高频实体（默认500）

**响应示例:**
\`\`\`json
{
  "message": "知识图谱生成成功",
  "html_url": "/outputs/knowledge_graph.html",
  "statistics": {
    "total_entities": 1250,
    "custom_entities": 45,
    "total_relations": 3420,
    "graph_nodes": 500,
    "graph_edges": 1850,
    "relation_types": 28,
    "avg_degree": 7.4
  }
}
\`\`\`

**curl示例:**
\`\`\`bash
curl -X POST "http://localhost:8000/api/knowledge-graph/generate" \
  -H "Content-Type: application/json" \
  -d '{"top_n": 500}'
\`\`\`

### 2. 查看知识图谱

#### GET /api/knowledge-graph/view

在浏览器中查看生成的知识图谱

**访问:** http://localhost:8000/api/knowledge-graph/view

### 3. 获取图谱统计

#### GET /api/knowledge-graph/stats

获取知识图谱的统计信息

**响应示例:**
\`\`\`json
{
  "total_entities": 1250,
  "custom_entities": 45,
  "total_relations": 3420,
  "top_entities": [
    ["唐三", 156],
    ["唐门", 89],
    ["外门弟子", 67]
  ]
}
\`\`\`

### 4. 查询实体信息

#### GET /api/knowledge-graph/entity/{entity_name}

获取指定实体的详细关系信息

**路径参数:**
- entity_name: 实体名称（如"唐三"）

**响应示例:**
\`\`\`json
{
  "entity": "唐三",
  "outgoing": [
    {
      "target": "唐门",
      "relation": "来自",
      "weight": 5
    }
  ],
  "incoming": [
    {
      "source": "外门弟子",
      "relation": "成为",
      "weight": 3
    }
  ]
}
\`\`\`

---

## 问答接口

### 1. 提问

#### POST /api/qa

向系统提问，获取基于文档的智能回答

**请求体:**
\`\`\`json
{
  "query": "唐三是谁？",
  "top_k": 10,
  "use_cache": true,
  "custom_instruction": null,
  "enable_followup": false
}
\`\`\`

**参数说明:**
- query: 用户问题（必填）
- top_k: 检索文档块数量（可选，默认10）
- use_cache: 是否使用缓存（可选，默认true）
- custom_instruction: 自定义生成指令（可选）
- enable_followup: 是否生成后续问题（可选，默认false）

**响应示例:**
\`\`\`json
{
  "query": "唐三是谁？",
  "answer": "唐三是唐门外门弟子，因偷学内门绝学为唐门所不容...",
  "retrieved_chunks": [
    {
      "title": "斗罗大陆.txt",
      "content": "唐三，唐门外门弟子...",
      "score": 0.8956,
      "chunk_index": 0
    }
  ],
  "processing_time": 1.23,
  "followup_questions": [
    "唐三有什么特殊能力？",
    "唐门是什么组织？"
  ]
}
\`\`\`

**curl示例:**
\`\`\`bash
curl -X POST "http://localhost:8000/api/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "唐三是谁？",
    "top_k": 10,
    "use_cache": true
  }'
\`\`\`

### 2. 获取缓存统计

#### GET /api/qa/cache/stats

获取问答缓存的统计信息

**响应示例:**
\`\`\`json
{
  "cache_size": 25,
  "cache_dir": ".rag_cache",
  "cache_file": "query_cache.json"
}
\`\`\`

### 3. 清除缓存

#### DELETE /api/qa/cache

清除所有问答缓存

**响应示例:**
\`\`\`json
{
  "message": "缓存已清除"
}
\`\`\`

---

## 系统信息接口

### 获取系统统计

#### GET /api/system/stats

获取系统的详细统计信息

**响应示例:**
\`\`\`json
{
  "documents": {
    "total": 3,
    "chunks": 156,
    "titles": ["斗罗大陆.txt", "唐门秘籍.txt"]
  },
  "retriever": {
    "model_name": "bge-large-zh-v1.5",
    "model_type": "sentence-transformers",
    "embedding_dimension": 1024,
    "retrieval_method": "语义检索"
  },
  "cache": {
    "size": 25
  },
  "config": {
    "chunk_size": 300,
    "chunk_overlap": 50,
    "default_top_k": 10,
    "rerank_top_k": 6,
    "custom_words_count": 3
  }
}
\`\`\`

---

## 错误处理

所有API在出错时返回标准的HTTP错误码和错误信息：

**错误响应格式:**
\`\`\`json
{
  "detail": "错误描述信息"
}
\`\`\`

**常见错误码:**
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误
- 503: 服务不可用

---

## Python客户端示例

\`\`\`python
import requests

BASE_URL = "http://localhost:8000"

# 1. 上传文件
with open("斗罗大陆.txt", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/files/upload",
        files={"file": f}
    )
    print(response.json())

# 2. 生成知识图谱
response = requests.post(
    f"{BASE_URL}/api/knowledge-graph/generate",
    json={"top_n": 500}
)
print(response.json())

# 3. 提问
response = requests.post(
    f"{BASE_URL}/api/qa",
    json={
        "query": "唐三是谁？",
        "top_k": 10,
        "use_cache": True
    }
)
result = response.json()
print(f"问题: {result['query']}")
print(f"回答: {result['answer']}")
print(f"处理时间: {result['processing_time']}秒")
\`\`\`

---

## JavaScript客户端示例

\`\`\`javascript
const BASE_URL = "http://localhost:8000";

// 1. 上传文件
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${BASE_URL}/api/files/upload`, {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// 2. 生成知识图谱
async function generateKnowledgeGraph() {
  const response = await fetch(`${BASE_URL}/api/knowledge-graph/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ top_n: 500 })
  });
  
  return await response.json();
}

// 3. 提问
async function askQuestion(query) {
  const response = await fetch(`${BASE_URL}/api/qa`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: query,
      top_k: 10,
      use_cache: true
    })
  });
  
  const result = await response.json();
  console.log('问题:', result.query);
  console.log('回答:', result.answer);
  console.log('处理时间:', result.processing_time, '秒');
  
  return result;
}
\`\`\`

---

## 部署建议

### 开发环境

\`\`\`bash
python app.py
\`\`\`

### 生产环境

使用Gunicorn + Uvicorn workers:

\`\`\`bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
\`\`\`

### Docker部署

创建 `Dockerfile`:

\`\`\`dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
\`\`\`

构建和运行:

\`\`\`bash
docker build -t rag-system .
docker run -p 8000:8000 -v $(pwd)/documents:/app/documents rag-system
\`\`\`

---

## 性能优化建议

1. **启用缓存**: 对于重复的问题，缓存可以显著提升响应速度
2. **调整top_k**: 根据实际需求调整检索数量，过大会影响性能
3. **批量处理**: 对于大量文件，建议分批上传和处理
4. **异步处理**: 知识图谱生成等耗时操作可以使用后台任务
5. **负载均衡**: 生产环境建议使用多个worker进程

---

## 常见问题

**Q: 上传文件后系统没有响应？**
A: 系统会自动重新初始化RAG系统，大文件可能需要较长时间

**Q: 知识图谱生成失败？**
A: 确保已上传文档，且文档包含足够的实体和关系

**Q: 问答返回"未找到相关文档"？**
A: 检查文档内容是否与问题相关，或尝试调整top_k参数

**Q: 如何自定义专有名词？**
A: 修改 `config.py` 中的 `CUSTOM_WORDS` 列表

---

## 技术支持

如有问题，请查看系统日志或联系技术支持团队。
