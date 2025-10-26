"""
RAG系统主模块 - 整合所有组件
"""
import sys
import time
from typing import List, Dict, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from config import RAGConfig
from text_processor import TextProcessor
from retriever import Retriever
from reranker import Reranker
from generator import AnswerGenerator
from cache_manager import CacheManager

# 导入外部依赖（假设这些模块已存在）
from document_loader import DocumentLoader
#from local_llm_client import LocalLLMClient
from llm_client import YunWuAIClient

class EnhancedRAGSystem:
    """增强版RAG（检索增强生成）系统 - 使用bge-large-zh-v1.5进行语义检索"""
    
    def __init__(
        self,
        documents_dir: str = None,
        api_key: str = None,
        api_url: str = None,
        embedding_model_name: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        cache_dir: str = None
    ):
        """
        初始化增强版RAG系统
        
        参数:
            documents_dir: 文档文件夹路径
            api_url: 本地大模型API地址
            embedding_model_name: 嵌入模型名称（默认使用bge-large-zh-v1.5）
            chunk_size: 文档分块大小
            chunk_overlap: 分块重叠大小
            cache_dir: 缓存目录
        """
        print("=" * 60)
        print("初始化增强版RAG系统（bge-large-zh-v1.5 + jieba分词）...")
        print("=" * 60)
        
        # 加载配置
        self.config = RAGConfig()
        documents_dir = documents_dir or self.config.DOCUMENTS_DIR
        api_url = api_url or self.config.LLM_API_URL
        api_key = api_key or self.config.LLM_API_KEY
        embedding_model_name = embedding_model_name or self.config.EMBEDDING_MODEL_NAME
        chunk_size = chunk_size or self.config.CHUNK_SIZE
        chunk_overlap = chunk_overlap or self.config.CHUNK_OVERLAP
        
        with tqdm(total=5, desc="系统初始化", ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            pbar.set_description("初始化文本处理器")
            self.text_processor = TextProcessor(
                chunk_size, 
                chunk_overlap,
                custom_words=self.config.CUSTOM_WORDS
            )
            pbar.update(1)
            
            pbar.set_description("初始化文档加载器")
            self.doc_loader = DocumentLoader(documents_dir)
           # self.llm_client = LocalLLMClient(api_url)
            self.llm_client = YunWuAIClient(api_key,api_url)
            pbar.update(1)
            
            pbar.set_description("加载嵌入模型")
            try:
                self.embedding_model = SentenceTransformer(embedding_model_name)
                embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                pbar.update(1)
            except Exception as e:
                print(f"\n✗ 加载模型失败: {str(e)}")
                print(f"提示: 首次使用会自动从HuggingFace下载模型")
                print(f"      或手动下载到本地: {embedding_model_name}")
                sys.exit(1)
            
            pbar.set_description("初始化缓存管理器")
            cache_path = Path(cache_dir or self.config.CACHE_DIR) / self.config.CACHE_FILE
            self.cache_manager = CacheManager(cache_path)
            pbar.update(1)
            
            pbar.set_description("初始化完成")
            pbar.update(1)
        
        print(f"✓ 成功加载 bge-large-zh-v1.5 模型 (向量维度: {embedding_dim})")
        
        # 存储文档数据
        self.documents = []
        self.document_chunks = []
        
        # 初始化其他组件（在加载文档后）
        self.retriever = None
        self.reranker = None
        self.generator = None
        
        # 加载并处理文档
        self._load_and_process_documents()
    
    def _load_and_process_documents(self):
        """加载并处理文档"""
        print("\n" + "=" * 60)
        print("文档处理流程")
        print("=" * 60)
        
        doc_stats = self.doc_loader.get_document_stats()
        print(f"文档文件夹: {self.doc_loader.documents_dir}")
        print(f"文件总数: {doc_stats['total_files']} | 总大小: {doc_stats['total_size'] / 1024:.2f} KB")
        
        # 加载所有文档
        self.documents = self.doc_loader.load_all_documents()
        
        if not self.documents:
            print("\n警告：没有找到任何文档！")
            print(f"请在 '{self.doc_loader.documents_dir}' 文件夹中添加文档文件")
            return
        
        print("\n正在分块处理文档...")
        for doc in tqdm(self.documents, desc="文档分块", ncols=80):
            chunks = self.text_processor.split_into_chunks(doc["content"])
            
            for chunk_idx, chunk_content in enumerate(chunks):
                self.document_chunks.append({
                    "title": doc["title"],
                    "chunk_id": f"{doc['title']}_chunk_{chunk_idx + 1}",
                    "content": chunk_content,
                    "original_doc": doc,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks)
                })
        
        print(f"✓ 完成分块: {len(self.documents)} 个文档 → {len(self.document_chunks)} 个文档块")
        
        print("\n正在初始化语义检索器...")
        self.retriever = Retriever(
            embedding_model=self.embedding_model,
            document_chunks=self.document_chunks
        )
        
        stats = self.retriever.get_statistics()
        print(f"✓ 检索器就绪: {stats['model_name']} | 维度: {stats['embedding_dimension']} | 方法: 语义检索")
        
        # 初始化重排序器和生成器
        self.reranker = Reranker(self.llm_client)
        self.generator = AnswerGenerator(
            llm_client=self.llm_client,
            max_tokens=self.config.MAX_TOKENS,
            temperature=self.config.TEMPERATURE,
            enable_citation=self.config.ENABLE_CITATION
        )
        
        print(f"\n已加载文档: {', '.join([doc['title'] for doc in self.documents])}")
    
    def ask(
        self, 
        query: str, 
        use_cache: bool = True, 
        top_k: int = None,
        custom_instruction: Optional[str] = None,
        enable_followup: bool = None,
        show_score_details: bool = None
    ) -> Dict:
        """
        完整的RAG流程：语义检索 + 重排序 + 生成
        
        参数:
            query: 用户查询
            use_cache: 是否使用缓存
            top_k: 检索的文档块数量
            custom_instruction: 自定义生成指令
            enable_followup: 是否生成后续问题建议
            show_score_details: 是否显示详细评分信息
            
        返回:
            包含检索结果和生成回答的字典
        """
        print(f"\n{'='*60}")
        print(f"问题: {query}")
        print('='*60)
        
        top_k = top_k or self.config.DEFAULT_TOP_K
        enable_followup = enable_followup if enable_followup is not None else self.config.ENABLE_FOLLOWUP
        show_score_details = show_score_details if show_score_details is not None else self.config.ENABLE_SCORE_DETAILS
        
        # 检查缓存
        if use_cache:
            cached_result = self.cache_manager.get(query)
            if cached_result:
                print("✓ 使用缓存结果")
                return cached_result
        
        start_time = time.time()
        
        with tqdm(total=3, desc="RAG处理流程", ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            pbar.set_description("检索相关文档")
            retrieved_chunks = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                return_score_details=show_score_details
            )
            pbar.update(1)
            
            if not retrieved_chunks:
                print("\n✗ 未找到相关文档")
                result = {
                    "query": query,
                    "retrieved_chunks": [],
                    "answer": self.generator._generate_no_context_response(query),
                    "processing_time": time.time() - start_time
                }
                self.cache_manager.set(query, result)
                return result
            
            #print(f"\n✓ 找到 {len(retrieved_chunks)} 个相关文档块")
            #if show_score_details:
                #for i, chunk in enumerate(retrieved_chunks, 1):
                   # print(f"  [{i}] {chunk['title']} (chunk {chunk['chunk_index'] + 1}) - 相关度: {chunk['score']:.4f}")
            
            pbar.set_description("重排序优化")
            reranked_chunks = self.reranker.rerank(
                query,
                retrieved_chunks,
                top_k=self.config.RERANK_TOP_K
            )
            pbar.update(1)
            
            pbar.set_description("生成回答")
            if enable_followup:
                generation_result = self.generator.generate_with_followup(
                    query=query,
                    context_chunks=reranked_chunks
                )
                answer = generation_result["answer"]
                followup_questions = generation_result.get("followup_questions", [])
            else:
                answer = self.generator.generate(
                    query=query,
                    context_chunks=reranked_chunks,
                    custom_instruction=custom_instruction
                )
                followup_questions = []
            pbar.update(1)
        
        processing_time = time.time() - start_time
        print(f"✓ 处理完成 (耗时: {processing_time:.2f}秒)")
        
        # 构建结果
        result = {
            "query": query,
            "retrieved_chunks": reranked_chunks,
            "answer": answer,
            "processing_time": processing_time
        }
        
        if followup_questions:
            result["followup_questions"] = followup_questions
        
        # 存入缓存
        self.cache_manager.set(query, result)
        
        return result
    
    def interactive_mode(self):
        """交互式问答模式"""
        print("\n" + "=" * 60)
        print("增强版RAG系统已就绪！")
        print("=" * 60)
        print("使用说明:")
        print("  • 输入问题进行查询")
        print("  • 输入 'quit' 或 'exit' 退出")
        print("  • 输入 'stats' 查看系统统计")
        print("  • 输入 'clear cache' 清除缓存")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n请输入问题: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("\n感谢使用RAG系统，再见！")
                    break
                
                if user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                
                if user_input.lower() == 'clear cache':
                    self.cache_manager.clear()
                    print("✓ 缓存已清除")
                    continue
                
                if not user_input:
                    print("请输入有效的问题")
                    continue
                
                # 执行RAG查询
                result = self.ask(user_input)
                
                # 显示回答
                print("\n" + "=" * 60)
                print("回答:")
                print("=" * 60)
                print(result["answer"])
                
                if "followup_questions" in result and result["followup_questions"]:
                    print("\n" + "-" * 60)
                    print("您可能还想了解:")
                    for i, q in enumerate(result["followup_questions"], 1):
                        print(f"  {i}. {q}")
                
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\n\n检测到中断信号，退出系统...")
                break
            except Exception as e:
                print(f"\n✗ 错误: {str(e)}")
    
    def _show_stats(self):
        """显示系统统计信息"""
        print("\n" + "=" * 60)
        print("系统统计信息")
        print("=" * 60)
        print(f"文档总数: {len(self.documents)}")
        print(f"文档块总数: {len(self.document_chunks)}")
        print(f"自定义词典: {len(self.config.CUSTOM_WORDS)} 个专有名词")
        
        if self.retriever:
            stats = self.retriever.get_statistics()
            print(f"\n嵌入模型:")
            print(f"  • 模型: {stats['model_name']}")
            print(f"  • 类型: {stats['model_type']}")
            print(f"  • 维度: {stats['embedding_dimension']}")
            print(f"  • 方法: {stats['retrieval_method']}")
        
        print(f"\n缓存查询数: {self.cache_manager.size()}")
        
        doc_stats = self.doc_loader.get_document_stats()
        print(f"\n文档统计:")
        print(f"  • 文件数: {doc_stats['total_files']}")
        print(f"  • 总大小: {doc_stats['total_size'] / 1024:.2f} KB")
        
        if doc_stats['file_types']:
            print(f"  • 文件类型: {', '.join([f'{ext}({count})' for ext, count in doc_stats['file_types'].items()])}")
        print("=" * 60)
