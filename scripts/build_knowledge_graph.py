"""
知识图谱构建脚本 - 从已上传文档生成知识图谱
运行此脚本会基于documents文件夹中的文档生成知识图谱
"""
import sys
from pathlib import Path

from config import RAGConfig
from knowledge_graph import KnowledgeGraphBuilder
from document_loader import DocumentLoader


def main():
    """主函数 - 构建并可视化知识图谱"""
    print("=" * 60)
    print("知识图谱生成工具")
    print("=" * 60)
    
    # 加载配置
    config = RAGConfig()
    
    # 初始化文档加载器
    print(f"\n正在加载文档...")
    doc_loader = DocumentLoader(config.DOCUMENTS_DIR)
    documents = doc_loader.load_all_documents()
    
    if not documents:
        print(f"\n错误: 在 '{config.DOCUMENTS_DIR}' 文件夹中没有找到任何文档")
        print("请先添加文档文件后再运行此脚本")
        sys.exit(1)
    
    print(f"✓ 成功加载 {len(documents)} 个文档")
    for doc in documents:
        print(f"  • {doc['title']}")
    
    # 初始化知识图谱构建器
    kg_builder = KnowledgeGraphBuilder(custom_words=config.CUSTOM_WORDS)
    
    # 构建知识图谱
    kg_builder.build_graph_from_documents(documents)
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("知识图谱统计")
    print("=" * 60)
    stats = kg_builder.get_statistics()
    print(f"实体总数: {stats['total_entities']}")
    print(f"关系总数: {stats['total_relations']}")
    print(f"图节点数: {stats['graph_nodes']}")
    print(f"图边数: {stats['graph_edges']}")
    print(f"平均度数: {stats['avg_degree']:.2f}")
    
    print("\n高频实体 Top 10:")
    for i, (entity, freq) in enumerate(stats['top_entities'], 1):
        print(f"  {i}. {entity} (出现 {freq} 次)")
    
    # 创建输出目录
    output_dir = Path("knowledge_graphs")
    output_dir.mkdir(exist_ok=True)
    
    # 生成可视化
    print("\n" + "=" * 60)
    print("生成可视化")
    print("=" * 60)
    
    interactive_path = kg_builder.visualize_interactive(
        output_path=str(output_dir / "knowledge_graph.html"),
        top_n=10  
    )
    
    # 完成
    top_n=10
    print("\n" + "=" * 60)
    print("知识图谱生成完成！")
    print("=" * 60)
    print(f"\n生成的文件:")
    print(f"  • 交互网页: {interactive_path}")
    print(f"\n💡 提示: 在浏览器中打开 {interactive_path} 查看交互式知识图谱")
    print(f"  图谱已优化为显示前{top_n}%高频实体，确保可视化清晰美观")


if __name__ == "__main__":
    main()
