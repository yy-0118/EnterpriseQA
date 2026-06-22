"""
重建向量索引 — 将MySQL中所有文档重新向量化导入Chroma
用法: python rebuild_index.py
"""
import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Document
from rag_engine import get_rag_engine, check_ollama_alive

# 检查 Ollama
ok, msg = check_ollama_alive()
print(f'Ollama状态: {msg}')
if not ok:
    print('❌ Ollama 不可用，无法重建索引')
    sys.exit(1)

rag = get_rag_engine()

# 如果向量库已有数据，先清空
try:
    collection = rag.vector_store._collection
    if collection.count() > 0:
        print(f'清空旧向量数据 ({collection.count()} 块)...')
        all_ids = collection.get()['ids']
        if all_ids:
            collection.delete(ids=all_ids)
        print('已清空')
except Exception as e:
    print(f'清空失败: {e}')

# 从MySQL读取所有文档
with app.app_context():
    docs = Document.query.filter_by(status=1).all()
    print(f'\n找到 {len(docs)} 篇文档，开始向量化...\n')

    total_chunks = 0
    for doc in docs:
        print(f'  [{doc.id}] {doc.title} ... ', end='', flush=True)
        try:
            n = rag.add_documents(
                [{'id': doc.id, 'title': doc.title, 'content': doc.content}],
                doc_id_prefix=f'doc_{doc.id}'
            )
            doc.chunk_count = n
            print(f'{n} 块 ✅')
            total_chunks += n
        except Exception as e:
            print(f'失败: {e}')
            doc.chunk_count = 0

    db.session.commit()

print(f'\n✅ 完成！共 {total_chunks} 个向量块，{len(docs)} 篇文档')
