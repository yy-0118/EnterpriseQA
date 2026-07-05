"""
企业知识库问答系统 — RAG 效果 Benchmark

测试维度:
  (1) 检索命中率 — 预期文档是否出现在 Top-K 结果中
  (2) 响应延迟 — 平均 / P50 / P95 毫秒数
  (3) 回答质量 — 长度、结构完整性、来源引用率
  (4) 边缘场景 — 简短查询、长查询、领域外问题、空查询

用法: python benchmark.py
"""
import json, time, requests, statistics, sys, os

BASE = "http://127.0.0.1:5000/api"
MAX_QA_WAIT = 120  # 单个问答最大等待秒数

# ============================================================
# 测试用例定义 (问题, 分类, 预期命中文档标题关键词, 难度)
# ============================================================
TEST_CASES = [
    # ---- 简单命中（关键词直接出现在文档标题中） ----
    {
        "question": "公司的考勤制度是什么？",
        "category": "人事制度",
        "expected_hit": ["考勤"],      # 预期来源标题包含此关键词
        "min_sources": 1,
        "difficulty": "easy",
    },
    {
        "question": "如何报销差旅费用？",
        "category": "财务管理",
        "expected_hit": ["报销"],
        "min_sources": 1,
        "difficulty": "easy",
    },
    {
        "question": "React 前端代码怎么写？",
        "category": "技术文档",
        "expected_hit": ["React"],
        "min_sources": 1,
        "difficulty": "easy",
    },
    {
        "question": "新员工入职要准备什么材料？",
        "category": "人事制度",
        "expected_hit": ["入职"],
        "min_sources": 1,
        "difficulty": "easy",
    },
    {
        "question": "Python 写代码有什么规范要求？",
        "category": "技术文档",
        "expected_hit": ["Python"],
        "min_sources": 1,
        "difficulty": "easy",
    },

    # ---- 中等难度（需要语义理解，标题不直接命中） ----
    {
        "question": "密码应该多久换一次？公司对密码有什么要求？",
        "category": "信息安全",
        "expected_hit": ["信息安全"],
        "min_sources": 1,
        "difficulty": "medium",
    },
    {
        "question": "员工表现不好会被开除吗？",
        "category": "人事制度",
        "expected_hit": ["绩效"],  # PIP/绩效改进计划
        "min_sources": 1,
        "difficulty": "medium",
    },
    {
        "question": "项目上线前要注意哪些事情？",
        "category": "技术流程",
        "expected_hit": ["项目开发"],
        "min_sources": 1,
        "difficulty": "medium",
    },
    {
        "question": "数据库表怎么命名才规范？",
        "category": "技术文档",
        "expected_hit": ["数据库"],
        "min_sources": 1,
        "difficulty": "medium",
    },

    # ---- 困难（跨文档综合、隐含语义） ----
    {
        "question": "员工请假有什么流程？能请多少天？",
        "category": "跨制度综合",
        "expected_hit": ["考勤"],
        "min_sources": 1,
        "difficulty": "hard",
    },
    {
        "question": "公司对加班和请假有什么规定？请假会被扣钱吗？",
        "category": "跨制度综合",
        "expected_hit": ["考勤"],
        "min_sources": 1,
        "difficulty": "hard",
    },

    # ---- 边缘场景 ----
    {
        "question": "绩效",
        "category": "短查询",
        "expected_hit": ["绩效"],
        "min_sources": 1,
        "difficulty": "edge",
    },
    {
        "question": "今天天气怎么样？",
        "category": "领域外",
        "expected_hit": [],
        "min_sources": 0,
        "difficulty": "edge",
    },
    {
        "question": "",
        "category": "空查询",
        "expected_hit": [],
        "min_sources": 0,
        "difficulty": "edge",
    },
]

# ============================================================
# 工具函数
# ============================================================

def get_token():
    resp = requests.post(f"{BASE}/auth/login", json={
        "username": "admin", "password": "123456"
    }, timeout=10)
    return resp.json()["data"]["token"]


def ask(token, question, timeout=MAX_QA_WAIT):
    """发送问答请求并计时"""
    start = time.perf_counter()
    try:
        resp = requests.post(
            f"{BASE}/qa/ask",
            json={"question": question},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            timeout=timeout,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        if resp.status_code == 200:
            return resp.json()["data"], elapsed_ms, None
        else:
            return None, elapsed_ms, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.Timeout:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return None, elapsed_ms, "TIMEOUT"
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return None, elapsed_ms, str(e)


def check_hit(sources, expected_keywords):
    """检查来源是否命中预期文档"""
    if not expected_keywords:
        return len(sources) == 0  # 预期无来源
    source_titles = " ".join(s.get("title", "") for s in sources)
    hits = [kw for kw in expected_keywords if kw in source_titles]
    return len(hits) > 0, hits


# ============================================================
# 报告输出
# ============================================================

def print_header(title, char="="):
    print(f"\n{char * 60}")
    print(f"  {title}")
    print(char * 60)


def print_section(title):
    print(f"\n  ┌─ {title}")


# ============================================================
# 主流程
# ============================================================

def main():
    print_header("企业知识库 RAG 系统 Benchmark", "█")
    print(f"  测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  测试用例: {len(TEST_CASES)} 个")
    print(f"  系统地址: {BASE}")

    # 检查系统状态
    token = get_token()
    qa_status = requests.get(f"{BASE}/qa/status", timeout=5).json()
    docs_info = requests.get(
        f"{BASE}/kb/documents?page_size=99",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    ).json()

    ollama_ok = qa_status["data"]["ollama_available"]
    doc_count = docs_info["data"]["total"]
    print(f"  Ollama: {'ONLINE' if ollama_ok else 'OFFLINE'}")
    print(f"  知识库: {doc_count} 篇文档")

    # ========================================
    # 执行测试
    # ========================================
    print_header("开始执行 Benchmark...", "-")

    results = []
    latencies = []
    errors = 0
    total_hits = 0
    total_expected = 0
    total_sources = 0

    for i, tc in enumerate(TEST_CASES, 1):
        q = tc["question"]
        label = q[:30] + ("..." if len(q) > 30 else "") if q else "(空查询)"
        cat = tc["category"]

        sys.stdout.write(f"  [{i:2d}/{len(TEST_CASES)}] [{tc['difficulty']:5s}] {cat:8s} | {label:35s} ... ")
        sys.stdout.flush()

        data, latency_ms, error = ask(token, q)

        if error:
            print(f"FAIL ({latency_ms:6.0f}ms) {error}")
            errors += 1
            results.append({"case": tc, "error": error, "latency_ms": latency_ms})
            continue

        latencies.append(latency_ms)
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        mode = data.get("mode", "?")
        history_id = data.get("history_id", "?")

        # 评估指标
        ans_len = len(answer)
        src_count = len(sources)
        total_sources += src_count

        # 来源命中检查
        hit, hit_kws = check_hit(sources, tc["expected_hit"])
        if hit:
            total_hits += 1
        if tc["expected_hit"]:
            total_expected += 1

        # 回答质量指标
        has_structure = any(
            marker in answer for marker in ["###", "**", "1.", "- ", "##", "> "]
        )
        has_citation = "文档" in answer or "来源" in answer or "参考" in answer
        has_no_refuse = "无法回答" not in answer[:100] and "找不到" not in answer[:100]

        status = "OK" if hit else ("MISS" if tc["expected_hit"] else "--")
        print(
            f"{status:4s} | "
            f"{latency_ms:6.0f}ms | "
            f"ans={ans_len:4d}字 | "
            f"src={src_count} | "
            f"mode={mode[:8]} | "
            f"struct={'Y' if has_structure else 'N'} "
            f"cite={'Y' if has_citation else 'N'}"
        )

        results.append({
            "i": i,
            "question": q,
            "category": cat,
            "difficulty": tc["difficulty"],
            "latency_ms": round(latency_ms, 1),
            "answer_len": ans_len,
            "source_count": src_count,
            "hit": hit,
            "mode": mode,
            "has_structure": has_structure,
            "has_citation": has_citation,
            "error": None,
        })

        # 请求间隔
        if i < len(TEST_CASES):
            time.sleep(1)

    # ========================================
    # 统计报告
    # ========================================
    print_header("Benchmark 报告")

    # ---- 1. 核心指标 ----
    print_section("1. 核心指标")
    total = len(TEST_CASES)
    success = total - errors
    hit_rate = (total_hits / total_expected * 100) if total_expected > 0 else 0
    avg_sources = total_sources / success if success > 0 else 0

    print(f"     总测试数 : {total}")
    print(f"     成功率   : {success}/{total} ({success/total*100:.1f}%)")
    print(f"     来源命中 : {total_hits}/{total_expected} ({hit_rate:.1f}%)")
    print(f"     平均来源 : {avg_sources:.1f} 篇/问")

    # ---- 2. 延迟分析 ----
    print_section("2. 响应延迟 (ms)")
    if latencies:
        lat_sorted = sorted(latencies)
        print(f"     最小值   : {min(latencies):.0f} ms")
        print(f"     平均值   : {statistics.mean(latencies):.0f} ms")
        print(f"     中位数   : {statistics.median(latencies):.0f} ms")
        p90_idx = int(len(lat_sorted) * 0.9)
        p95_idx = int(len(lat_sorted) * 0.95)
        print(f"     P90      : {lat_sorted[min(p90_idx, len(lat_sorted)-1)]:.0f} ms")
        print(f"     P95      : {lat_sorted[min(p95_idx, len(lat_sorted)-1)]:.0f} ms")
        print(f"     最大值   : {max(latencies):.0f} ms")

    # ---- 3. 按难度分析 ----
    print_section("3. 按难度维度")
    for diff in ["easy", "medium", "hard", "edge"]:
        group = [r for r in results if r.get("difficulty") == diff and not r.get("error")]
        if not group:
            continue
        avg_lat = statistics.mean([r["latency_ms"] for r in group])
        hits = sum(1 for r in group if r.get("hit"))
        checks = sum(1 for r in group if r.get("hit") is not None and any(
            tc["expected_hit"] for tc in TEST_CASES
            if tc["question"] == r["question"]
        ))
        struct_rate = sum(1 for r in group if r.get("has_structure")) / len(group) * 100
        cite_rate = sum(1 for r in group if r.get("has_citation")) / len(group) * 100
        avg_ans_len = statistics.mean([r["answer_len"] for r in group])
        print(
            f"     {diff:6s} | "
            f"avg {avg_lat:6.0f}ms | "
            f"ans {avg_ans_len:5.0f}字 | "
            f"结构 {struct_rate:3.0f}% | "
            f"引用 {cite_rate:3.0f}% | "
            f"{len(group)} cases"
        )

    # ---- 4. 回答质量 ----
    print_section("4. 回答质量")
    valid = [r for r in results if not r.get("error")]
    if valid:
        struct_rate = sum(1 for r in valid if r.get("has_structure")) / len(valid) * 100
        cite_rate = sum(1 for r in valid if r.get("has_citation")) / len(valid) * 100
        avg_ans_len = statistics.mean([r["answer_len"] for r in valid])
        rag_ratio = sum(1 for r in valid if r.get("mode") == "RAG模式") / len(valid) * 100
        print(f"     结构化率 : {struct_rate:.0f}%")
        print(f"     来源引用 : {cite_rate:.0f}%")
        print(f"     平均回答 : {avg_ans_len:.0f} 字")
        print(f"     RAG模式  : {rag_ratio:.0f}%")

    # ---- 5. 按类别分析 ----
    print_section("5. 按知识类别")
    from collections import defaultdict
    cat_stats = defaultdict(list)
    for tc, r in zip(TEST_CASES, [r for r in results]):
        cat = tc["category"]
        if not r.get("error"):
            cat_stats[cat].append(r)
    for cat, group in sorted(cat_stats.items()):
        avg_lat = statistics.mean([r["latency_ms"] for r in group])
        hits = sum(1 for r in group if r.get("hit"))
        checks = sum(1 for tc in TEST_CASES
                     if tc["category"] == cat and tc["expected_hit"]
                     and any(r["question"] == tc["question"] for r in group))
        print(f"     {cat:12s} | avg {avg_lat:6.0f}ms | {len(group)} cases | {hits} hits")

    # ---- 6. 逐条结果 ----
    print_section("6. 逐条结果明细")
    for r in results:
        q_short = (r["question"] or "(空)")[:40]
        if r.get("error"):
            print(f"     {'FAIL':4s} | {q_short:42s} | {r['error']}")
        else:
            struct_mark = "S" if r.get("has_structure") else " "
            cite_mark = "C" if r.get("has_citation") else " "
            hit_mark = "HIT" if r.get("hit") else ("---" if r.get("source_count") == 0 else "MIS")
            print(
                f"     {hit_mark:4s} | "
                f"{r['latency_ms']:6.0f}ms | "
                f"{r['answer_len']:4d}字 | "
                f"src={r['source_count']} | "
                f"{struct_mark}{cite_mark} | "
                f"{q_short}"
            )

    # ---- 7. 评分 ----
    print_section("7. 综合评分")
    if latencies:
        latency_score = max(0, 100 - statistics.median(latencies) / 100)
    else:
        latency_score = 0
    retrieval_score = hit_rate
    quality_score = ((struct_rate + cite_rate) / 2) if valid else 0
    overall = (latency_score * 0.25 + retrieval_score * 0.45 + quality_score * 0.30)

    print(f"     检索命中 (45%) : {retrieval_score:.1f}/100")
    print(f"     回答质量 (30%) : {quality_score:.1f}/100")
    print(f"     响应速度 (25%) : {latency_score:.1f}/100")
    print(f"     {'─' * 30}")
    grade = "A" if overall >= 85 else ("B" if overall >= 70 else ("C" if overall >= 55 else "D"))
    print(f"     综合评分        : {overall:.1f}/100  (等级: {grade})")

    # 总结建议
    print_section("8. 优化建议")
    suggestions = []
    if hit_rate < 80:
        suggestions.append("检索命中率偏低 → 增大 chunk_overlap, 或增加文档数量")
    if latencies and statistics.median(latencies) > 15000:
        suggestions.append("响应偏慢 → 考虑更换更快的模型 或 启用 GPU 加速")
    if avg_sources < 1.5:
        suggestions.append("平均来源数偏少 → 增大 RETRIEVAL_TOP_K")
    if cite_rate < 70:
        suggestions.append("来源引用率低 → 优化 Prompt 模版, 强制要求引用来源")
    if not suggestions:
        suggestions.append("系统整体表现良好！建议持续扩充知识库规模以提升覆盖度。")
    for s in suggestions:
        print(f"     • {s}")

    # 保存结果
    report_path = os.path.join(os.path.dirname(__file__), "benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ollama_ok": ollama_ok,
            "doc_count": doc_count,
            "total_cases": total,
            "success": success,
            "hit_rate": hit_rate,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "median_latency_ms": statistics.median(latencies) if latencies else 0,
            "p95_latency_ms": lat_sorted[min(p95_idx, len(lat_sorted)-1)] if latencies else 0,
            "overall_score": round(overall, 1),
            "results": results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n  📄 详细报告已保存: {report_path}")
    print_header("Benchmark 完成", "█")


if __name__ == "__main__":
    main()
