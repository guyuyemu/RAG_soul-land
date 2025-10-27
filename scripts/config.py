"""
配置文件 - 存储RAG系统的所有配置参数
"""
from pathlib import Path
from typing import List
from custom_words import CUSTOM_WORDS

class RAGConfig:
    """RAG系统配置类"""
    
    # 文档处理配置
    DOCUMENTS_DIR = "documents"
    CHUNK_SIZE = 300  # 文档分块大小（字符数）
    CHUNK_OVERLAP = 50  # 分块重叠大小（字符数）
    
    CUSTOM_WORDS = CUSTOM_WORDS
    
    # bge-large-zh-v1.5是专为中文优化的高质量嵌入模型
    EMBEDDING_MODEL_NAME = "bge-large-zh-v1.5"
    #本地部署
    #LLM_API_URL = "本地地址"
    #调用API
    LLM_API_URL = "LLM_API_URL"
    LLM_API_KEY = "LLM_API_KEY"
    # 检索配置
    DEFAULT_TOP_K = 10  # 默认检索返回的文档块数量
    RERANK_TOP_K = 6  # 重排序后返回的文档块数量
    ENABLE_SCORE_DETAILS = True  # 是否启用详细评分信息
    
    # 生成配置
    MAX_TOKENS = 800  # 最大生成token数
    TEMPERATURE = 0.5  # 生成温度（0-1，越高越随机）
    ENABLE_CITATION = True  # 是否在回答中包含引用来源
    ENABLE_FOLLOWUP = False  # 是否生成后续问题建议
    
    # 缓存配置
    CACHE_DIR = ".rag_cache"
    CACHE_FILE = "query_cache.json"
    
    
    @classmethod
    def get_cache_path(cls) -> Path:
        """获取缓存文件路径"""
        cache_dir = Path(cls.CACHE_DIR)
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / cls.CACHE_FILE
