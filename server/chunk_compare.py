"""Chunk Size 对比: 300 vs 500 vs 800 — 评测召回命中率与延迟"""
import sys, os, time, json, statistics, requests

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from config import Config
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDoc

QUESTIONS = [
    ("公司的考勤制度是什么？", ["考勤"]),
    ("如何报销差旅费用？", ["报销"]),
    ("React 前端代码怎么写？", ["React"]),
    ("新员工入职要准备什么材料？", ["入职"]),
    ("Python 写代码有什么规范要求？", ["Python"]),
    ("密码应该多久换一次？", ["信息安全"]),
    ("员工表现不好会被开除吗？", ["绩效"]),
    ("项目上线前要注意哪些事情？", ["项目开发"]),
    ("数据库表怎么命名才规范？", ["数据库"]),
    ("加班和请假有什么规定？", ["考勤"]),
]

BASE = "http://127.0.0.1:5000/api"
SIZES = [300, 500, 800]


def get_token():
    r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "123456"}, timeout=10)
    return r.json()["data"]["token"]


def ask(token, question):
    t0 = time.perf_counter()
    r = requests.post(f"{BASE}/qa/ask", json={"question": question},
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
                      timeout=120)
    ms = (time.perf_counter() - t0) * 1000
    d = r.json()
    if d.get("code") != 200:
        return None, ms, d.get("message", "?")
    return d["data"], ms, None


def check_hit(sources, keywords):
    titles = " ".join(s.get("title", "") for s in sources)
    return any(kw in titles for kw in keywords)


def rebuild_index(chunk_size):
    """直接替换 RAG 引擎的文本分割器并重建索引（不重启 Flask）"""
    from rag_engine import get_rag_engine
    from app import app, db
    from models import Document
    import chromadb

    rag = get_rag_engine()

    # 1. 更新分割器
    rag.text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=Config.CHUNK_OVERLAP,
        separators=['\n\n', '\n', '。', '！', '？', '；', '.', '!', '?', ' ', ''],
        length_function=len,
    )

    # 2. 清空 Chroma
    try:
        coll = rag.vector_store._collection
        ids = coll.get()["ids"]
        if ids:
            coll.delete(ids=ids)
    except Exception:
        pass

    # 3. 从 MySQL 读取所有文档，重新分块 + 向量化
    with app.app_context():
        docs = Document.query.filter_by(status=1).all()
        total = 0
        for doc in docs:
            splits = rag.text_splitter.split_text(doc.content)
            if not splits:
                continue
            lcdocs = [LCDoc(page_content=s, metadata={"title": doc.title, "chunk_index": i, "doc_id": str(doc.id)})
                      for i, s in enumerate(splits)]
            ids = [f"doc_{doc.id}_{doc.title}_chunk_{i}" for i in range(len(splits))]
            rag.vector_store.add_documents(lcdocs, ids=ids)
            doc.chunk_count = len(splits)
            total += len(splits)
        db.session.commit()
    return total


def main():
    print("=" * 55)
    print("  Chunk Size 对比: 300 vs 500 vs 800")
    print("  问题数:", len(QUESTIONS))
    print("=" * 55)

    token = get_token()

    # 备份当前 chunk_size
    original = Config.CHUNK_SIZE

    results = {}
    for size in SIZES:
        print(f"\n[chunk_size={size}] 重建索引...", end=" ", flush=True)
        chunks = rebuild_index(size)
        print(f"{chunks} 块")
        time.sleep(2)

        print(f"{'问题':<28s} {'延迟':>7s} {'来源':>4s} {'命中':>4s}")
        print("-" * 48)
        case_results = []
        for q, kws in QUESTIONS:
            data, lat, err = ask(token, q)
            if err:
                print(f"  {q[:25]:25s} | {lat:6.0f}ms | FAIL: {err}")
                case_results.append({"q": q, "hit": False, "lat_ms": lat, "src_n": 0, "err": err})
                continue
            hit = check_hit(data["sources"], kws)
            sn = len(data["sources"])
            case_results.append({"q": q, "hit": hit, "lat_ms": lat, "src_n": sn, "ans_len": len(data.get("answer", ""))})
            print(f"  {q[:25]:25s} | {lat:6.0f}ms | {sn:>4} | {'OK' if hit else 'MISS'}")
            time.sleep(0.5)

        lats = [r["lat_ms"] for r in case_results if not r.get("err")]
        hits = sum(1 for r in case_results if r["hit"])
        results[size] = {
            "chunks": chunks,
            "hit_count": hits,
            "hit_rate": hits / len(QUESTIONS) * 100,
            "avg_lat": statistics.mean(lats) if lats else 0,
            "med_lat": statistics.median(lats) if lats else 0,
            "p95_lat": sorted(lats)[int(len(lats) * 0.95) - 1] if len(lats) >= 20 else (max(lats) if lats else 0),
            "avg_src": statistics.mean([r["src_n"] for r in case_results if not r.get("err")]),
            "avg_ans": statistics.mean([r["ans_len"] for r in case_results if not r.get("err")]),
        }

    # ---- 报告 ----
    print("\n" + "=" * 55)
    print("  对比结果")
    print("=" * 55)
    print(f"  {'指标':<16} | {'300':>8} | {'500':>8} | {'800':>8}")
    print(f"  {'─'*16}┼{'─'*10}┼{'─'*10}┼{'─'*10}")
    for label, key, fmt in [
        ("向量块数", "chunks", "{}"),
        ("命中率", "hit_rate", "{:.1f}%"),
        ("平均延迟", "avg_lat", "{:.0f}ms"),
        ("中位延迟", "med_lat", "{:.0f}ms"),
        ("P95延迟", "p95_lat", "{:.0f}ms"),
        ("平均来源数", "avg_src", "{:.1f}"),
        ("平均回答字", "avg_ans", "{:.0f}"),
    ]:
        vals = [fmt.format(results[s][key]) for s in SIZES]
        print(f"  {label:<16} | {vals[0]:>8} | {vals[1]:>8} | {vals[2]:>8}")

    best = max(SIZES, key=lambda s: results[s]["hit_rate"])
    tie = [s for s in SIZES if results[s]["hit_rate"] == results[best]["hit_rate"]]
    if len(tie) > 1:
        best = min(tie, key=lambda s: results[s]["avg_lat"])
        print(f"\n  Hit rate tie ({results[best]['hit_rate']:.0f}%), picked lowest latency: chunk_size={best}")
    else:
        print(f"\n  >> Best chunk_size = {best} (hit_rate {results[best]['hit_rate']:.0f}%)")

    # 恢复默认值
    print(f"\n  Restore chunk_size={original}...", end=" ", flush=True)
    rebuild_index(original)
    print("Done")

    # 保存
    with open("chunk_compare_report.json", "w", encoding="utf-8") as f:
        json.dump({str(k): {sk: sv for sk, sv in v.items() if sk != "cases"}
                   for k, v in results.items()}, f, ensure_ascii=False, indent=2)
    print("  📄 报告已保存: chunk_compare_report.json")


if __name__ == "__main__":
    main()
