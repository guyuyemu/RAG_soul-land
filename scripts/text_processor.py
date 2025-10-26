"""
文本处理模块 - 负责文本分块和预处理
使用jieba进行中文文本处理，支持自定义词典
"""
from typing import List
import re
import jieba
import jieba.posseg as pseg


class TextProcessor:
    """文本处理器 - 处理中文文本分块和分词"""
    
    def __init__(
        self, 
        chunk_size: int = 300, 
        chunk_overlap: int = 50,
        custom_words: List[str] = None
    ):
        """
        初始化文本处理器
        
        参数:
            chunk_size: 文档分块大小（字符数）
            chunk_overlap: 分块重叠大小（字符数）
            custom_words: 自定义词典列表（领域专有名词）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self._load_custom_dictionary(custom_words or [])
        
        # 加载停用词
        self.stop_words = self._load_chinese_stopwords()
    
    def _load_custom_dictionary(self, custom_words: List[str]) -> None:
        """
        加载自定义词典到jieba分词器
        用于识别领域专有名词，避免被拆分
        
        参数:
            custom_words: 自定义词列表
        """
        for word in custom_words:
            # 添加到jieba词典，设置较高词频确保不被拆分
            jieba.add_word(word, freq=10000)
        
        if custom_words:
           # print(f"已加载 {len(custom_words)} 个自定义词汇: {', '.join(custom_words)}")
            print(f"已加载 {len(custom_words)} 个自定义词汇")
    
    def _load_chinese_stopwords(self) -> set:
        """
        加载中文停用词
        
        返回:
            停用词集合
        """
        # 常用中文停用词
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
            '看', '好', '自己', '这', '那', '里', '为', '与', '而', '且', '或', '但',
            '因为', '所以', '如果', '虽然', '然而', '因此', '于是', '并且', '以及',
            '以', '及', '等', '等等', '之', '其', '中', '对', '从', '把', '被', '让'
        }
        return stopwords
    
    def split_into_chunks(self, text: str) -> List[str]:
        """
        将文本智能分块，避免句子被截断
        使用中文句子分割规则
        
        参数:
            text: 要分块的文本
            
        返回:
            分块后的文本列表
        """
        # 按照中文标点符号（句号、问号、感叹号、省略号等）分句
        sentence_delimiters = r'[。！？；\n]+'
        sentences = [s.strip() for s in re.split(sentence_delimiters, text) if s.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # 如果当前块加上新句子超过指定大小，则结束当前块
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append("".join(current_chunk))
                
                # 重叠处理：从上一个块的末尾取部分内容
                overlap_sentences = []
                overlap_length = 0
                for sent in reversed(current_chunk):
                    overlap_sentences.insert(0, sent)
                    overlap_length += len(sent)
                    if overlap_length >= self.chunk_overlap:
                        break
                
                current_chunk = overlap_sentences
                current_length = overlap_length
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # 添加最后一个块
        if current_chunk:
            chunks.append("".join(current_chunk))
        
        return chunks
    
    def tokenize_and_filter(self, text: str) -> List[str]:
        """
        使用jieba进行中文分词并过滤停用词
        
        参数:
            text: 要处理的文本
            
        返回:
            过滤后的词列表
        """
        words = jieba.lcut(text)
        
        # 过滤停用词和无效词
        filtered_words = [
            word for word in words
            if word not in self.stop_words and self._is_valid_word(word)
        ]
        
        return filtered_words
    
    def tokenize_with_pos(self, text: str) -> List[tuple]:
        """
        使用jieba进行分词并标注词性
        可用于更精细的文本分析
        
        参数:
            text: 要处理的文本
            
        返回:
            (词, 词性)元组列表
        """
        return [(word, flag) for word, flag in pseg.cut(text)]
    
    def _is_valid_word(self, word: str) -> bool:
        """
        判断词是否有效（包含中文字符或字母数字，且长度大于1）
        
        参数:
            word: 待判断的词
            
        返回:
            是否为有效词
        """
        # 过滤单字符和纯标点
        if len(word) < 1:
            return False
        
        # 检查是否包含中文字符或字母数字
        return bool(re.search(r'[\u4e00-\u9fff]|[a-zA-Z0-9]', word))
