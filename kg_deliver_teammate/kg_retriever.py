# -*- coding: utf-8 -*-
"""kg_retriever.py — 图谱统一检索器（一站式查询入口，自动判题 + 聚合三路资源）。

定位：把零散的图谱检索入口（题型方法论 / 命中定理 / 模板—定理图经验）聚合成
一个「自动判题型 → 一键检索」的入口，方便人工查询或程序集成。

 ① 题型方法论   knowledge_graph.retrieve_kg  → 核心方法 / 流程 / 陷阱 + 领域摘要 + 综合竞赛参考
 ② 命中定理     theorem_kg.theorem_hint      → 定理表述 / 前置结论 / 证据链（自动同名消歧）
 ③ 图经验       kg_fast_retriever.retrieve_experience → 相似模板步骤 + 定理表

设计约束：
  - 零新增依赖：仅复用同目录 knowledge_graph / theorem_kg / kg_fast_retriever；
  - 任一资源不可用自动降级（缺文件/缺模型/异常 → 该段跳过），绝不抛异常；
  - 题型自动判定用内置中英文关键词（无需目标系统的 skills.classify，交付包自包含）。

用法：
  python kg_retriever.py "求 2^2023 除以 7 的余数"            # CLI 一键检索
  python kg_retriever.py "..." --domain number_theory        # 显式指定题型（跳过自动判定）
  python kg_retriever.py --selftest                          # 自检 3 题
  python kg_retriever.py --stats                             # 图谱统计
  from kg_retriever import unified_retrieve, auto_domain     # 程序内调用
"""
from __future__ import annotations

import argparse
import os
import sys

__all__ = ["auto_domain", "unified_retrieve", "retriever_stats"]

# 让本文件可直接被 import（其所在目录即交付包根目录）
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# ===================== 题型自动判定关键词（交付包自包含，无需外部分类器） =====================

_KEYWORDS_EN = {
    "topology": ["topolog", "compact", "connected", "homeomorph", "hausdorff", "neighborhood", "open set", "closed set", "dense"],
    "real_analysis": ["measure", "lebesgue", "integrabl", "almost everywhere", "monotone convergence", "riemann", "uniform convergence"],
    "functional_analysis": ["banach", "hilbert", "operator", "normed", "bounded linear", "dual space", "functional"],
    "abstract_algebra": ["group", "ring", "field", "module", "isomorph", "homomorph", "galois", "subgroup", "ideal", "normal subgroup"],
    "complex_analysis": ["cauchy", "residue", "analytic function", "meromorph", "laurent", "contour", "holomorphic", "harmonic function"],
    "numerical_analysis": ["eigenvalue", "eigenvector", "matrix", "determinant", "gaussian elimination", "newton", "iteration", "interpolat"],
    "differential_equations": ["differential equation", "ode", "integrating factor", "first order", "second order", "wronskian"],
    "partial_differential_equations": ["partial differential", "pde", "laplace equation", "heat equation", "wave equation", "poisson", "separation of variables"],
    "algebra": ["polynomial", "equation", "inequality", "quadratic", "roots", "factor"],
    "linear_algebra": ["linear transformation", "vector space", "linear independent", "span", "basis", "rank"],
    "calculus": ["derivative", "integral", "limit", "series", "continu", "taylor", "differential"],
    "probability": ["probability", "random variable", "expectation", "variance", "distribution", "markov"],
    "combinatorics": ["combination", "permutation", "count", "binomial", "pigeonhole", "generating function"],
    "number_theory": ["prime", "modulo", "congruence", "gcd", "lcm", "euler", "divisib"],
    "geometry": ["triangle", "circle", "angle", "polygon", "euclidean", "coordinate geometry"],
    "graph_theory": ["graph", "vertex", "edge", "matching", "bipartite", "connected graph", "tree"],
    "operations_research": ["linear programming", "optimiz", "assignment", "shortest path", "scheduling", "network flow"],
    "mathematical_physics": ["bessel", "legendre", "fourier", "green function", "special function", "laguerre"],
}

_KEYWORDS_CN = {
    "topology": ["拓扑", "紧致", "同胚", "豪斯多夫", "邻域", "开集", "闭集", "稠密"],
    "real_analysis": ["测度", "勒贝格", "黎曼", "几乎处处", "单调收敛", "一致收敛", "可测"],
    "functional_analysis": ["巴拿赫", "希尔伯特", "算子", "范数", "有界线性", "对偶空间", "泛函"],
    "abstract_algebra": ["群论", "子群", "同构", "同态", "伽罗瓦", "正规子群", "环论", "理想", "域论"],
    "complex_analysis": ["留数", "柯西积分", "解析函数", "亚纯", "洛朗", "围道", "全纯", "复变", "调和函数"],
    "numerical_analysis": ["高斯消元", "牛顿迭代", "插值", "数值"],
    "differential_equations": ["微分方程", "常微分", "积分因子", "朗斯基", "通解"],
    "partial_differential_equations": ["偏微分", "拉普拉斯方程", "热传导", "波动方程", "泊松", "分离变量"],
    "algebra": ["不等式", "多项式", "方程", "二次", "因式", "恒等式", "数列", "代数式", "求值", "化简"],
    "linear_algebra": ["线性变换", "向量空间", "线性无关", "张成", "线性方程组", "秩", "特征值", "特征向量", "矩阵", "行列式"],
    "calculus": ["导数", "微分", "极限", "级数", "泰勒", "洛必达", "极值", "单调性", "定积分"],
    "probability": ["概率", "随机变量", "期望", "方差", "分布", "条件概率"],
    "combinatorics": ["组合", "排列", "计数", "二项式", "鸽巢", "抽屉", "母函数", "递推", "染色"],
    "number_theory": ["素数", "质数", "整除", "同余", "最大公约", "最小公倍", "欧拉函数", "因数", "约数", "数论", "余数"],
    "geometry": ["三角形", "圆", "角", "多边形", "几何", "相似", "全等", "切线", "垂线", "中点", "圆锥曲线", "面积", "体积"],
    "graph_theory": ["图论", "顶点", "边", "匹配", "二分图", "连通图", "欧拉回路", "最短路"],
    "operations_research": ["线性规划", "优化", "指派", "调度", "网络流"],
    "mathematical_physics": ["贝塞尔", "勒让德", "傅里叶", "格林函数", "特殊函数", "拉盖尔"],
}


def auto_domain(problem: str) -> str:
    """用内置中英文关键词判定题型 domain_en；无命中返回 ""。"""
    if not problem:
        return ""
    t = problem.lower()
    for d, kws in _KEYWORDS_EN.items():
        if any(k in t for k in kws):
            return d
    for d, kws in _KEYWORDS_CN.items():
        if any(k in t for k in kws):
            return d
    return ""


# ===================== 统一检索 =====================

def unified_retrieve(problem: str, domain: str = "", max_len: int = 2400) -> dict:
    """聚合三路检索，返回 {"domain": str, "text": str}。

    domain 为空时自动判定；任一子检索失败自动跳过，text 为空时返回 ""。
    """
    if not problem:
        return {"domain": domain, "text": ""}
    if not domain:
        domain = auto_domain(problem)
    parts: list[str] = []

    # ① 题型方法论（含领域摘要 + 综合竞赛参考 + 扩展题解）
    if domain:
        try:
            from knowledge_graph import retrieve_kg
            block = retrieve_kg(domain, problem, max_len=min(1100, max_len))
            if block:
                parts.append(block)
        except Exception:  # noqa: BLE001
            pass

    # ② 命中定理 + 证据链（自动同名消歧）
    try:
        from theorem_kg import theorem_hint
        _n, block = theorem_hint(problem=problem, domain=domain, max_len=min(700, max_len))
        if block:
            parts.append(block)
    except Exception:  # noqa: BLE001
        pass

    # ③ 模板—定理图经验（相似模板步骤 + 定理表；依赖 numpy + 本地嵌入模型，缺失自动跳过）
    try:
        from kg_fast_retriever import retrieve_experience
        block = retrieve_experience(problem, domain=domain, max_len=min(600, max_len))
        if block:
            parts.append(block)
    except Exception:  # noqa: BLE001
        pass

    text = "\n".join(parts)
    if len(text) > max_len:
        text = text[:max_len] + "\n…(已截断)"
    return {"domain": domain, "text": text}


def retriever_stats() -> dict:
    """汇总三类图谱统计（各子模块失败返回占位）。"""
    st = {"available": True}
    try:
        from knowledge_graph import kg_stats
        st["kg"] = kg_stats()
    except Exception:  # noqa: BLE001
        st["kg"] = {"error": "unavailable"}
    try:
        from theorem_kg import theorem_stats
        st["theorem"] = theorem_stats()
    except Exception:  # noqa: BLE001
        st["theorem"] = {"error": "unavailable"}
    try:
        from kg_fast_retriever import retriever_stats as _r
        st["graph"] = _r()
    except Exception:  # noqa: BLE001
        st["graph"] = {"available": False}
    return st


# ===================== CLI =====================

_SELFTEST = [
    ("求 2^2023 除以 7 的余数", "number_theory"),
    ("Compute the residue of 1/(z^2+1) at z=i", "complex_analysis"),
    ("求矩阵 [[2,1],[1,2]] 的特征值与特征向量", "linear_algebra"),
]


def _fmt_stats(st: dict) -> str:
    lines = []
    kg = st.get("kg") or {}
    if isinstance(kg, dict) and "n_nodes" in kg:
        lines.append(f"题型图谱: {kg.get('n_nodes')} 个题型节点")
    th = st.get("theorem") or {}
    if isinstance(th, dict) and "n_theorems" in th:
        lines.append(f"定理图谱: {th.get('n_theorems')} 个定理实体（{th.get('n_ambig_groups', 0)} 组同名消歧）")
    g = st.get("graph") or {}
    if isinstance(g, dict) and g.get("available"):
        lines.append(f"模板—定理图: {g.get('n_templates_vectors', 0)} 条模板向量")
    else:
        lines.append("模板—定理图: 不可用（缺嵌入模型/产物，检索自动降级）")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="kg_retriever", description="图谱统一检索器")
    ap.add_argument("query", nargs="?", default="", help="题目文本")
    ap.add_argument("--domain", default="", help="题型 domain_en（显式指定，跳过自动判定）")
    ap.add_argument("--selftest", action="store_true", help="自检 3 题")
    ap.add_argument("--stats", action="store_true", help="图谱统计")
    args = ap.parse_args(argv)

    if args.stats:
        print(_fmt_stats(retriever_stats()))
        return 0

    if args.selftest:
        print("=== 自检（自动判题 + 统一检索）===")
        for q, expect in _SELFTEST:
            r = unified_retrieve(q)
            hit = r["domain"] == expect
            print(f"[{'OK' if hit else 'DIFF'}] 判定={r['domain']}（期望 {expect}） 输出 {len(r['text'])} 字")
        return 0

    q = (args.query or "").strip()
    if not q:
        ap.print_help()
        return 1

    r = unified_retrieve(q, domain=args.domain)
    if not r["text"]:
        print(f"[未命中] 无法为题目检索到图谱内容（判定题型: {r['domain'] or '空'}）。")
        return 1
    print(f"【题型】{r['domain'] or '（未判定）'}")
    print(r["text"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
