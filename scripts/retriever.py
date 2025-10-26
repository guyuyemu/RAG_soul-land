"""
检索模块 - 使用bge-large-zh-v1.5进行语义检索
提供详细的评分计算和解释
"""
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm


class Retriever:
    """检索器 - 使用bge-large-zh-v1.5进行高质量中文语义检索"""
    
    def __init__(
        self,
        embedding_model: SentenceTransformer,
        document_chunks: List[Dict]
    ):
        """
        初始化检索器
        
        参数:
            embedding_model: bge-large-zh-v1.5嵌入模型
            document_chunks: 文档块列表
        """
        self.embedding_model = embedding_model
        self.document_chunks = document_chunks
        
        print("正在使用 bge-large-zh-v1.5 生成文档嵌入向量...")
        chunk_contents = [chunk["content"] for chunk in document_chunks]
        
        self.chunk_embeddings = embedding_model.encode(
            chunk_contents,
            normalize_embeddings=True,  # 归一化嵌入向量，提升检索效果
            show_progress_bar=True,  # 显示进度条
            batch_size=32
        )
        print(f"✓ 成功生成 {len(document_chunks)} 个文档块的嵌入向量")
    
    def semantic_search(
        self, 
        query: str, 
        top_k: int = 5,
        return_details: bool = False
    ) -> List[Tuple[int, float]] | List[Dict]:
        """
        使用bge-large-zh-v1.5进行语义检索
        基于余弦相似度计算语义相关性
        
        bge模型特点:
        - 专为中文优化，理解中文语义和上下文
        - 支持长文本编码（最大512 tokens）
        - 归一化嵌入向量，余弦相似度等价于点积
        
        参数:
            query: 用户查询
            top_k: 返回的结果数量
            return_details: 是否返回详细评分信息
            
        返回:
            元组列表 [(文档块索引, 相似度分数), ...] 或详细信息字典列表
        """
        # 为查询添加指令前缀，提升检索效果（bge模型推荐做法）
        query_with_instruction = f"为这个句子生成表示以用于检索相关文章：{query}"
        
        # 生成查询向量
        query_embedding = self.embedding_model.encode(
            [query_with_instruction],
            normalize_embeddings=True
        )
        
        # 计算余弦相似度
        # 由于向量已归一化，余弦相似度 = 点积
        # 相似度范围: [0, 1]，值越大表示语义越相似
        similarities = cosine_similarity(query_embedding, self.chunk_embeddings)[0]
        
        # 获取最相关的文档块索引（降序排列）
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        if return_details:
            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                results.append({
                    'index': int(idx),
                    'score': score,
                    'score_type': 'bge_cosine_similarity',
                    'score_range': '[0, 1]',
                    'model': 'bge-large-zh-v1.5',
                    'explanation': (
                        f'BGE语义相似度: {score:.4f}\n'
                        f'使用bge-large-zh-v1.5模型计算查询与文档的语义相似程度\n'
                        f'分数越接近1表示语义越相关'
                    )
                })
            return results
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        return_score_details: bool = False
    ) -> List[Dict]:
        """
        执行语义检索，返回相关文档块
        
        参数:
            query: 用户查询
            top_k: 返回的结果数量
            return_score_details: 是否返回详细评分信息
            
        返回:
            相关文档块列表，每个块包含原始信息和相关度分数
        """
        if not self.document_chunks:
            return []
        
        # 使用bge-large-zh-v1.5进行语义检索
        search_results = self.semantic_search(
            query, top_k, return_details=return_score_details
        )
        
        retrieved_chunks = []
        for result in search_results:
            if return_score_details and isinstance(result, dict):
                chunk = self.document_chunks[result['index']].copy()
                chunk["score"] = result['score']
                chunk["score_details"] = result
            else:
                chunk_idx, relevance_score = result
                chunk = self.document_chunks[chunk_idx].copy()
                chunk["score"] = relevance_score
            
            retrieved_chunks.append(chunk)
        
        return retrieved_chunks
    
    def get_statistics(self) -> Dict:
        """
        获取检索器统计信息
        
        返回:
            包含模型信息和文档统计的字典
        """
        return {
            'model_name': 'bge-large-zh-v1.5',
            'model_type': 'Chinese Semantic Embedding',
            'embedding_dimension': self.chunk_embeddings.shape[1],
            'total_documents': len(self.document_chunks),
            'retrieval_method': 'Semantic Search (Cosine Similarity)'
        }
