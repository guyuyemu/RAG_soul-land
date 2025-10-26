"""
主入口文件 - 启动RAG系统
"""
from rag_system import EnhancedRAGSystem


def main():
    """主函数 - 初始化并启动RAG系统"""
    # 创建增强版RAG系统实例
    # 所有参数都可以省略，将使用config.py中的默认值
    rag_system = EnhancedRAGSystem()
    
    # 检查是否成功加载文档
    if not rag_system.documents:
        print("\n系统无法启动：没有可用的文档")
        print("请在 'documents' 文件夹中添加文档后重试")
        return
    
    # 启动交互式问答模式
    rag_system.interactive_mode()


if __name__ == "__main__":
    main()
