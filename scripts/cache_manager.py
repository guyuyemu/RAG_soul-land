"""
缓存管理模块 - 管理查询缓存
"""

import json
from pathlib import Path
from typing import Dict, Optional


class CacheManager:
    """缓存管理器 - 管理查询结果缓存，提升重复查询的响应速度"""
    
    def __init__(self, cache_file: Path):
        """
        初始化缓存管理器
        
        参数:
            cache_file: 缓存文件路径
        """
        self.cache_file = cache_file
        self.cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """从文件加载缓存数据"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"加载缓存: {len(self.cache)} 条记录")
            except Exception as e:
                print(f"缓存文件损坏，重新创建缓存: {e}")
                self.cache = {}
    
    def save_cache(self):
        """保存缓存到文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def get(self, query: str) -> Optional[Dict]:
        """
        获取缓存的查询结果
        
        参数:
            query: 查询文本
            
        返回:
            缓存的结果字典，如果不存在则返回None
        """
        return self.cache.get(query)
    
    def set(self, query: str, result: Dict):
        """
        设置缓存
        
        参数:
            query: 查询文本
            result: 查询结果字典
        """
        self.cache[query] = result
        self.save_cache()
    
    def clear(self):
        """清除所有缓存"""
        self.cache = {}
        self.save_cache()
    
    def size(self) -> int:
        """
        获取缓存大小
        
        返回:
            缓存中的查询数量
        """
        return len(self.cache)
