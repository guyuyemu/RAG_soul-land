import os
from typing import List, Dict
from pathlib import Path
from tqdm import tqdm


class DocumentLoader:
    """文档加载器类"""
    
    def __init__(self, documents_dir: str = "documents"):
        """
        初始化文档加载器
        
        参数:
            documents_dir: 文档文件夹路径
        """
        self.documents_dir = documents_dir
        
        # 如果文档文件夹不存在，创建它
        if not os.path.exists(documents_dir):
            os.makedirs(documents_dir)
            print(f"已创建文档文件夹: {documents_dir}")
    
    def load_text_file(self, file_path: str) -> str:
        """
        加载单个文本文件
        
        参数:
            file_path: 文件路径
            
        返回:
            文件内容
        """
        try:
            # 尝试多种编码方式
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    return content
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，使用二进制模式读取
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
            return content
            
        except Exception as e:
            print(f"\n加载文件失败 {file_path}: {str(e)}")
            return ""
    
    def load_all_documents(self) -> List[Dict[str, str]]:
        """
        从文档文件夹加载所有支持的文档
        
        返回:
            文档列表，每个文档包含标题和内容
        """
        documents = []
        
        # 支持的文件扩展名
        supported_extensions = ['.txt', '.md', '.py', '.json', '.csv', '.log']
        
        # 遍历文档文件夹并收集所有支持的文件
        if not os.path.exists(self.documents_dir):
            print(f"警告：文档文件夹 '{self.documents_dir}' 不存在")
            return documents
        
        # 先收集所有符合条件的文件路径
        supported_files = []
        for root, dirs, files in os.walk(self.documents_dir):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in supported_extensions:
                    file_path = os.path.join(root, file)
                    supported_files.append(file_path)
        
        # 使用进度条加载文件
        print(f"\n开始加载 {len(supported_files)} 个文档...")
        for file_path in tqdm(supported_files, desc="加载文档", unit="个"):
            content = self.load_text_file(file_path)
            
            if content.strip():  # 只添加非空文档
                # 使用相对路径作为标题
                relative_path = os.path.relpath(file_path, self.documents_dir)
                documents.append({
                    "title": relative_path,
                    "content": content
                })
        
        print(f"总共成功加载了 {len(documents)} 个文档")
        return documents
    
    def get_document_stats(self) -> Dict[str, int]:
        """
        获取文档文件夹的统计信息
        
        返回:
            统计信息字典
        """
        stats = {
            "total_files": 0,
            "total_size": 0,
            "file_types": {}
        }
        
        if not os.path.exists(self.documents_dir):
            return stats
        
        # 收集所有文件以显示进度
        all_files = []
        for root, dirs, files in os.walk(self.documents_dir):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        # 显示统计进度
        for file_path in tqdm(all_files, desc="统计文件", unit="个"):
            file_ext = os.path.splitext(file_path)[1].lower()
            
            stats["total_files"] += 1
            stats["total_size"] += os.path.getsize(file_path)
            
            if file_ext in stats["file_types"]:
                stats["file_types"][file_ext] += 1
            else:
                stats["file_types"][file_ext] = 1
        
        return stats