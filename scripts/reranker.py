"""
重排序模块 - 使用LLM对检索结果进行重排序
"""
from typing import List, Dict


class Reranker:
    """重排序器 - 使用LLM提升检索结果的相关性排序"""
    
    def __init__(self, llm_client):
        """
        初始化重排序器
        
        参数:
            llm_client: LLM客户端，用于调用大语言模型
        """
        self.llm_client = llm_client
    
    def rerank(self, query: str, search_results: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        使用LLM对检索结果进行重排序
        通过让LLM判断文档与查询的相关性来优化排序
        
        参数:
            query: 用户查询
            search_results: 初始检索结果
            top_k: 重排序后返回的数量
            
        返回:
            重排序后的文档块列表
        """
        # 如果结果数量不超过top_k，直接返回
        if len(search_results) <= top_k:
            return search_results
        
        # 构建重排序提示词
        prompt = self._build_rerank_prompt(query, search_results)
        
        # 调用LLM进行重排序
        try:
            rerank_response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=100,
                temperature=0.0  # 使用确定性输出
            )
            
            # 解析LLM返回的排序索引
            reranked_indices = self._parse_rerank_response(rerank_response, len(search_results))
            
            # 根据重排序结果返回文档块
            return [search_results[i] for i in reranked_indices[:top_k]]
            
        except Exception as e:
            print(f"重排序失败: {e}")
            # 失败时返回原始排序的前top_k结果
            return search_results[:top_k]
    
    def _build_rerank_prompt(self, query: str, search_results: List[Dict]) -> str:
        """
        构建重排序提示词
        
        参数:
            query: 用户查询
            search_results: 检索结果
            
        返回:
            提示词字符串
        """
        # 构建文档块列表
        document_list = "\n".join([
            f"{i}. {chunk['content'][:200]}..."
            for i, chunk in enumerate(search_results)
        ])
        
        prompt = f"""请根据与以下查询的相关性，对提供的文档块进行排序。
只返回排序后的索引（从0开始），用逗号分隔，不添加任何解释。

查询: {query}

文档块:
{document_list}

排序后的索引（从最相关到最不相关）:"""
        
        return prompt
    
    def _parse_rerank_response(self, response: str, max_index: int) -> List[int]:
        """
        解析LLM返回的重排序结果
        
        参数:
            response: LLM返回的字符串
            max_index: 最大有效索引
            
        返回:
            排序后的索引列表
        """
        # 解析逗号分隔的索引
        reranked_indices = []
        for idx_str in response.split(','):
            idx_str = idx_str.strip()
            if idx_str.isdigit():
                idx = int(idx_str)
                if 0 <= idx < max_index:
                    reranked_indices.append(idx)
        
        # 添加未被LLM排序的索引（保持原始顺序）
        remaining_indices = [
            i for i in range(max_index)
            if i not in reranked_indices
        ]
        
        return reranked_indices + remaining_indices
