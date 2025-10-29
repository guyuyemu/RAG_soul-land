"""
FastAPI后端应用 - RAG知识问答系统
提供文件管理、知识图谱生成和问答接口
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import shutil
import json
import uvicorn
from datetime import datetime

from rag_system import EnhancedRAGSystem
from knowledge_graph import KnowledgeGraphBuilder
from config import RAGConfig

# 初始化FastAPI应用
app = FastAPI(
    title="RAG知识问答系统",
    description="基于检索增强生成的智能问答系统，支持文件管理、知识图谱和问答功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
rag_system: Optional[EnhancedRAGSystem] = None
kg_builder: Optional[KnowledgeGraphBuilder] = None
config = RAGConfig()

# 确保必要的目录存在
DOCUMENTS_DIR = Path(config.DOCUMENTS_DIR)
DOCUMENTS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# 挂载静态文件目录
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


# ==================== 数据模型 ====================

class QueryRequest(BaseModel):
    """问答请求模型"""
    query: str
    top_k: Optional[int] = None
    use_cache: bool = True
    custom_instruction: Optional[str] = None
    enable_followup: Optional[bool] = None


class QueryResponse(BaseModel):
    """问答响应模型"""
    query: str
    answer: str
    retrieved_chunks: List[Dict]
    processing_time: float
    followup_questions: Optional[List[str]] = None


class FileInfo(BaseModel):
    """文件信息模型"""
    filename: str
    size: int
    upload_time: str
    path: str


class KnowledgeGraphRequest(BaseModel):
    """知识图谱生成请求模型"""
    top_n: int =10


# ==================== 系统初始化 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化RAG系统"""
    global rag_system, kg_builder
    
    print("=" * 60)
    print("正在启动RAG系统...")
    print("=" * 60)
    
    try:
        # 初始化RAG系统
        rag_system = EnhancedRAGSystem()
        
        # 初始化知识图谱构建器
        kg_builder = KnowledgeGraphBuilder(custom_words=config.CUSTOM_WORDS)
        
        print("✓ RAG系统启动成功")
        print("=" * 60)
    except Exception as e:
        print(f"✗ RAG系统启动失败: {str(e)}")
        print("系统将以有限功能模式运行")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    print("\n正在关闭RAG系统...")


# ==================== 健康检查 ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径 - 返回API文档链接"""
    return """
    <html>
        <head>
            <title>RAG知识问答系统</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    background: rgba(255, 255, 255, 0.95);
                    padding: 40px;
                    border-radius: 10px;
                    color: #2c3e50;
                }
                h1 { color: #667eea; }
                a {
                    color: #667eea;
                    text-decoration: none;
                    font-weight: bold;
                }
                a:hover { text-decoration: underline; }
                .endpoint {
                    background: #f8f9fa;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 4px solid #667eea;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 RAG知识问答系统</h1>
                <p>欢迎使用基于检索增强生成的智能问答系统</p>
                
                <h2>📚 主要功能</h2>
                <div class="endpoint">
                    <strong>文件管理:</strong> 上传、查看、删除文档
                </div>
                <div class="endpoint">
                    <strong>知识图谱:</strong> 自动生成实体关系图谱
                </div>
                <div class="endpoint">
                    <strong>智能问答:</strong> 基于文档内容的精准回答
                </div>
                
                <h2>📖 API文档</h2>
                <p>访问 <a href="/docs">/docs</a> 查看完整的API文档</p>
                <p>访问 <a href="/redoc">/redoc</a> 查看ReDoc格式文档</p>
                
                <h2>🚀 快速开始</h2>
                <p>1. 上传文档: POST /api/files/upload</p>
                <p>2. 生成知识图谱: POST /api/knowledge-graph/generate</p>
                <p>3. 提问: POST /api/qa</p>
            </div>
        </body>
    </html>
    """


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "rag_system": "initialized" if rag_system else "not initialized",
        "kg_builder": "initialized" if kg_builder else "not initialized",
        "timestamp": datetime.now().isoformat()
    }


# ==================== 文件管理接口 ====================

@app.get("/api/files", response_model=List[FileInfo])
async def list_files():
    """获取所有已上传的文件列表"""
    try:
        files = []
        for file_path in DOCUMENTS_DIR.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "upload_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "path": str(file_path.relative_to(DOCUMENTS_DIR))
                })
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文档文件"""
    try:
        # 检查文件类型
        allowed_extensions = {'.txt', '.md', '.pdf', '.docx', '.doc'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}"
            )
        
        # 保存文件
        file_path = DOCUMENTS_DIR / file.filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 重新初始化RAG系统以加载新文件
        global rag_system
        rag_system = EnhancedRAGSystem()
        
        return {
            "message": "文件上传成功",
            "filename": file.filename,
            "size": file_path.stat().st_size,
            "path": str(file_path.relative_to(DOCUMENTS_DIR))
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """删除指定文件"""
    try:
        file_path = DOCUMENTS_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="不是有效的文件")
        
        # 删除文件
        file_path.unlink()
        
        # 重新初始化RAG系统
        global rag_system
        rag_system = EnhancedRAGSystem()
        
        return {
            "message": "文件删除成功",
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")


@app.get("/api/files/{filename}/download")
async def download_file(filename: str):
    """下载指定文件"""
    try:
        file_path = DOCUMENTS_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")


# ==================== 知识图谱接口 ====================

@app.post("/api/knowledge-graph/generate")
async def generate_knowledge_graph(
    background_tasks: BackgroundTasks,
    request: KnowledgeGraphRequest = KnowledgeGraphRequest()
):
    """生成知识图谱"""
    if not rag_system or not rag_system.documents:
        raise HTTPException(status_code=400, detail="没有可用的文档，请先上传文档")
    
    try:
        global kg_builder
        kg_builder = KnowledgeGraphBuilder(custom_words=config.CUSTOM_WORDS)
        
        # 构建知识图谱
        kg_builder.build_graph_from_documents(rag_system.documents)
        
        # 生成可视化
        output_path = OUTPUT_DIR / "knowledge_graph.html"
        if output_path.exists():
            output_path.unlink()
        kg_builder.visualize_interactive(
            output_path=str(output_path),
            top_n=request.top_n
        )
        
        # 获取统计信息
        stats = kg_builder.get_statistics()
        
        return {
            "message": "知识图谱生成成功",
            "html_url": f"/outputs/knowledge_graph.html",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识图谱生成失败: {str(e)}")


@app.get("/api/knowledge-graph/view")
async def view_knowledge_graph():
    """查看知识图谱"""
    graph_path = OUTPUT_DIR / "knowledge_graph.html"
    
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="知识图谱未生成，请先生成知识图谱")
    
    return FileResponse(
        path=graph_path,
        media_type='text/html'
    )

"""
@app.get("/api/knowledge-graph/stats")
async def get_knowledge_graph_stats():
    if not kg_builder or not kg_builder.graph:
        raise HTTPException(status_code=400, detail="知识图谱未生成")
    
    try:
        stats = kg_builder.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
"""

@app.get("/api/knowledge-graph/entity/{entity_name}")
async def get_entity_info(entity_name: str):
    """获取指定实体的详细信息"""
    if not kg_builder or not kg_builder.graph:
        raise HTTPException(status_code=400, detail="知识图谱未生成")
    
    try:
        neighbors = kg_builder.get_entity_neighbors(entity_name)
        
        if "error" in neighbors:
            raise HTTPException(status_code=404, detail=neighbors["error"])
        
        return neighbors
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体信息失败: {str(e)}")


# ==================== 问答接口 ====================

@app.post("/api/qa", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """智能问答接口"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    if not rag_system.documents:
        raise HTTPException(status_code=400, detail="没有可用的文档，请先上传文档")
    
    try:
        # 执行RAG查询
        result = rag_system.ask(
            query=request.query,
            use_cache=request.use_cache,
            top_k=request.top_k,
            custom_instruction=request.custom_instruction,
            enable_followup=request.enable_followup
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")


@app.get("/api/qa/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    try:
        return {
            "cache_size": rag_system.cache_manager.size(),
            "cache_dir": str(config.CACHE_DIR),
            "cache_file": config.CACHE_FILE
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@app.delete("/api/qa/cache")
async def clear_cache():
    """清除问答缓存"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    try:
        rag_system.cache_manager.clear()
        return {"message": "缓存已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


# ==================== 系统信息接口 ====================

@app.get("/api/system/stats")
async def get_system_stats():
    """获取系统统计信息"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG系统未初始化")
    
    try:
        stats = {
            "documents": {
                "total": len(rag_system.documents),
                "chunks": len(rag_system.document_chunks),
                "titles": [doc['title'] for doc in rag_system.documents]
            },
            "retriever": rag_system.retriever.get_statistics() if rag_system.retriever else None,
            "cache": {
                "size": rag_system.cache_manager.size()
            },
            "config": {
                "chunk_size": config.CHUNK_SIZE,
                "chunk_overlap": config.CHUNK_OVERLAP,
                "default_top_k": config.DEFAULT_TOP_K,
                "rerank_top_k": config.RERANK_TOP_K,
                "custom_words_count": len(config.CUSTOM_WORDS)
            }
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")


# ==================== 主函数 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("启动RAG知识问答系统后端服务")
    print("=" * 60)
    print(f"文档目录: {DOCUMENTS_DIR.absolute()}")
    print(f"输出目录: {OUTPUT_DIR.absolute()}")
    print("=" * 60)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=4210,
        reload=True,  # 开发模式下启用热重载
        log_level="info"
    )
