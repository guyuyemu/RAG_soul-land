"""
生成模块 - 基于检索结果生成答案
"""
from typing import List, Dict, Optional


class AnswerGenerator:
    """答案生成器 - 基于检索到的文档块生成高质量回答"""
    
    def __init__(
        self, 
        llm_client, 
        max_tokens: int = 800, 
        temperature: float = 0.5,
        enable_citation: bool = True
    ):
        """
        初始化答案生成器
        
        参数:
            llm_client: LLM客户端，用于调用大语言模型
            max_tokens: 最大生成token数
            temperature: 生成温度（0-1，越高越随机，越低越确定）
            enable_citation: 是否在回答中包含引用来源
        """
        self.llm_client = llm_client
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.enable_citation = enable_citation
    
    def generate(
        self, 
        query: str, 
        context_chunks: List[Dict],
        custom_instruction: Optional[str] = None
    ) -> str:
        """
        基于检索到的文档块生成回答
        
        参数:
            query: 用户原始问题
            context_chunks: 检索并重排序后的相关文档块
            custom_instruction: 自定义生成指令（可选）
            
        返回:
            生成的回答文本
        """
        # 检查是否有可用的上下文
        if not context_chunks:
            return self._generate_no_context_response(query)
        
        # 构建结构化上下文文本
        context_text = self._build_structured_context(context_chunks)
        
        # 构建增强的生成提示词
        prompt = self._build_enhanced_prompt(
            query=query,
            context=context_text,
            custom_instruction=custom_instruction
        )
        
        # 调用LLM生成回答
        try:
            answer = self.llm_client.generate(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # 后处理：添加引用信息
            if self.enable_citation and answer:
                answer = self._add_citations(answer, context_chunks)
            
            return answer.strip()
            
        except Exception as e:
            print(f"生成回答时出错: {str(e)}")
            return f"抱歉，生成回答时遇到问题：{str(e)}"
    
    def _build_structured_context(self, context_chunks: List[Dict]) -> str:
        """
        构建结构化的上下文文本
        
        参数:
            context_chunks: 文档块列表
            
        返回:
            格式化的上下文文本，包含文档来源和相关度信息
        """
        context_parts = []
        
        for i, chunk in enumerate(context_chunks, 1):
            # 提取文档元信息
            title = chunk.get('title', '未知文档')
            content = chunk.get('content', '')
            score = chunk.get('score', 0.0)
            chunk_index = chunk.get('chunk_index', 0)
            total_chunks = chunk.get('total_chunks', 1)
            
            # 构建单个文档块的格式化文本
            context_part = f"""【文档片段 {i}】
来源: {title}
位置: 第 {chunk_index + 1}/{total_chunks} 段
相关度: {score:.2%}
内容:
{content}"""
            
            context_parts.append(context_part)
        
        return "\n\n" + "=" * 50 + "\n\n".join(context_parts)
    
    def _build_enhanced_prompt(
        self, 
        query: str, 
        context: str,
        custom_instruction: Optional[str] = None
    ) -> str:
        """
        构建增强的生成提示词，整合用户问题和检索到的支持性信息
        
        参数:
            query: 用户原始问题
            context: 结构化的上下文文本
            custom_instruction: 自定义指令
            
        返回:
            完整的提示词字符串
        """
        # 基础系统指令
        system_instruction = """你是一个专业的知识问答助手，擅长基于提供的文档内容回答问题。

# 核心原则
准确性优先: 严格基于提供的文档内容回答，不编造或推测信息
完整性: 充分利用所有相关文档片段，提供全面的回答
逻辑性: 回答应条理清晰，逻辑连贯
可追溯: 明确指出信息来源，便于用户验证

# 回答要求
- 如果文档中有明确答案，直接提供准确回答
- 如果文档中信息不完整，说明已知部分并指出缺失内容
- 如果文档中完全没有相关信息，明确告知无法回答
- 使用清晰的中文表达，避免冗长和重复
- 对于复杂问题，使用分点或分段的方式组织回答"""

        # 如果有自定义指令，添加到系统指令中
        if custom_instruction:
            system_instruction += f"\n\n# 特殊要求\n{custom_instruction}"
        
        # 构建完整提示词
        prompt = f"""{system_instruction}

# 参考文档
以下是检索到的相关文档片段，��相关度排序：
{context}

# 用户问题
{query}

# 回答格式
请按以下结构组织你的回答：

 **直接回答**: 首先用1-2句话直接回答核心问题（严格按照文档内容回答）
 **详细说明**: 如有必要，提供详细的解释和补充信息
 **信息来源**: 在回答末尾注明主要信息来源的文档（使用文档标题）

现在请基于以上文档内容回答问题："""
        
        return prompt
    
    def _generate_no_context_response(self, query: str) -> str:
        """
        当没有检索到相关文档时生成的回答
        
        参数:
            query: 用户问题
            
        返回:
            友好的无结果提示
        """
        return f"""抱歉，我在知识库中没有找到与「{query}」相关的信息。

建议：
1. 尝试使用不同的关键词重新提问
2. 确认问题是否在知识库的覆盖范围内
3. 如果是新问题，可能需要添加相关文档到知识库"""
    
    def _add_citations(self, answer: str, context_chunks: List[Dict]) -> str:
        """
        在回答末尾添加引用来源信息
        
        参数:
            answer: 生成的回答
            context_chunks: 使用的文档块
            
        返回:
            添加了引用信息的回答
        """
        # 提取唯一的文档来源
        sources = []
        seen_titles = set()
        
        for chunk in context_chunks:
            title = chunk.get('title', '未知文档')
            if title not in seen_titles:
                sources.append(title)
                seen_titles.add(title)
        
        # 如果回答中还没有来源信息，添加引用
        if sources and "来源" not in answer and "参考" not in answer:
            citation = "\n\n---\n**参考来源**: " + "、".join(sources)
            return answer + citation
        
        return answer
    
    def generate_with_followup(
        self, 
        query: str, 
        context_chunks: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """
        生成回答并提供后续问题建议（高级功能）
        
        参数:
            query: 用户问题
            context_chunks: 相关文档块
            conversation_history: 对话历史（可选）
            
        返回:
            包含回答和后续问题建议的字典
        """
        # 生成主要回答
        answer = self.generate(query, context_chunks)
        
        # 基于上下文生成后续问题建议
        followup_questions = self._generate_followup_questions(
            query, 
            context_chunks, 
            answer
        )
        
        return {
            "answer": answer,
            "followup_questions": followup_questions
        }
    
    def _generate_followup_questions(
        self, 
        query: str, 
        context_chunks: List[Dict],
        answer: str
    ) -> List[str]:
        """
        基于当前问答生成后续问题建议
        
        参数:
            query: 原始问题
            context_chunks: 使用的文档块
            answer: 生成的回答
            
        返回:
            后续问题列表
        """
        # 简单实现：基于文档内容提取关键主题
        # 实际应用中可以使用LLM生成更智能的后续问题
        topics = set()
        
        for chunk in context_chunks[:2]:  # 只使用前2个最相关的文档
            content = chunk.get('content', '')
            # 这里可以添加更复杂的主题提取逻辑
            # 简单示例：提取文档标题作为相关主题
            topics.add(chunk.get('title', ''))
        
        # 生成后续问题模板
        followup = []
        if topics:
            followup.append(f"关于{list(topics)[0]}还有哪些详细信息？")
            if len(topics) > 1:
                followup.append(f"{list(topics)[1]}与此有什么关联？")
        
        return followup[:3]  # 最多返回3个后续问题
