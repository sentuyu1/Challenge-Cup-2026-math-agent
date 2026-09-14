# -*- coding: utf-8 -*-
"""kg_bridge.py — 题型知识图谱接入桥（面向 Challenge-Cup-2026-math-agent）。

职责：把目标系统 `skills.classify(problem)` 返回的【中文题型类别】映射到
`knowledge_graph.retrieve_kg` 所需的【domain_en】，再检索图谱方法论文本，
供 user_agent.py 在推理前注入提示词。

设计原则（与目标系统一致）：
- 惰性 import（skills / knowledge_graph 在函数内 import），跟随系统风格。
- 确定性查询表 + 关键词，无向量库、零 API。
- 全程 try/except，任何异常或无法映射都返回空串，绝不抛异常（不打扰主流程）。
- 与现有 KnowledgeCards / skill_context / icma_rag 并存，不替换它们。
"""

from __future__ import annotations

__all__ = ["CATEGORY_TO_DOMAIN", "kg_hint", "domain_for_cn"]

# ============ 中文题型类别(目标系统 skills.classify 返回值) → 图谱 domain_en ============
# 目标系统 18 类：偏微分方程、复分析、常微分方程、微分几何、抽象代数、拓扑学、数值分析、
#   数学分析、概率论、泛函分析、测度积分、离散数学、线性回归、统计推断、运筹学、随机过程、
#   非基础及进阶课程、高等代数。
# 图谱 18 个 domain_en：algebra/linear_algebra/calculus/complex_analysis/geometry/
#   number_theory/combinatorics/graph_theory/probability/differential_equations/
#   partial_differential_equations/topology/real_analysis/functional_analysis/
#   abstract_algebra/operations_research/numerical_analysis/mathematical_physics。
# 语义一一对应则直连；图谱没有的类别→尽量贴近（二级关键词按文本再判）；仍歧义→空串(不注入)。
CATEGORY_TO_DOMAIN: dict[str, str] = {
    "偏微分方程": "partial_differential_equations",
    "复分析": "complex_analysis",
    "常微分方程": "differential_equations",
    "抽象代数": "abstract_algebra",
    "拓扑学": "topology",
    "数值分析": "numerical_analysis",
    "数学分析": "calculus",            # 数学分析/微积分 → calculus
    "概率论": "probability",
    "泛函分析": "functional_analysis",
    "测度积分": "real_analysis",        # 测度/积分 → real_analysis
    "运筹学": "operations_research",
    "微分几何": "geometry",            # 系统无 geometry，用 geometry 节点贴近
    "随机过程": "probability",         # 随机过程是概率延伸
    "高等代数": "linear_algebra",      # 高等代数含线性代数主体
    # 线性回归 / 统计推断 / 非基础及进阶课程 → 无图谱专属节点，留空（主映射不注入，
    #   靠下方 _coarse_domain_by_keyword 兜底）
    "线性回归": "",
    "统计推断": "",
    "非基础及进阶课程": "",
    "离散数学": "",                   # 宽泛类，由 _coarse_domain_by_keyword 子判定
}

# 目标系统把"离散数学"一类集中；但实际题可能落数论/组合/图论，
# 用关键词在问题文本上做一次} 判定，选最贴近的图谱节点。
_DISCRETE_KEYWORD_DOMAIN = [
    ("number_theory", ["素数", "整除", "同余", "gcd", "lcm", "modulo", "分解质因数", "数论", "prime", "divisib", "余数"]),
    ("graph_theory", ["图", "顶点", "边", "节点", "最短路径", "匹配", "连通", "graph", "vertex", "node", "edge"]),
    ("combinatorics", ["组合", "排列", "count", "计数", "组合数", "binom", "鸽巢", "容斥", "ways", "排列组合"]),
    ("linear_algebra", ["矩阵", "行列式", "特征值", "向量空间", "秩", "逆矩阵", "方阵", "矩阵", "rank", "matrix", "eigen"]),
    ("calculus", ["极限", "导数", "微分", "积分", "连续", "收敛", "中值", "极值", "函数", "gradient", "limit", "derivative", "integral", "continuous"]),
    ("algebra", ["方程", "方程组", "不等式", "多项式", "根", "解", "恒等", "二次", "equation", "polynomial", "inequality", "solve", "sqrt", "根号", "实数", "整数解"]),
]
# 注：顺序即优先级。上两面向不同题型的通用关键词一段先后命中时取先者；
#     linear_algebra/calculus/algebra 放在组合/数论/图论之后，避免把题错标成代数系。
_COARSE_KEYWORD_DOMAIN = {
    "离散数学": _DISCRETE_KEYWORD_DOMAIN,
    "线性回归": [("linear_algebra", ["矩阵", "向量", "回归", "最小二乘", "least", "linear"]),
                ("calculus", ["导数", "微分", "斜率", "梯度"])],
    "统计推断": [("probability", ["概率", "期望", "方差", "假设检验", "置信", "检验", "正态分布", "分布"]),
                ("real_analysis", ["收敛", "序列", "极限"])],
    "非基础及进阶课程": [],
}


def domain_for_cn(category: str, problem: str = "") -> str:
    """把中文类别映射为图谱 domain_en；歧义/无法映射时返回空串（'' = 不注入）。

    category 为空或不在表内 → ''。
    对映射为空但有 _COARSE_KEYWORD_DOMAIN 的类别，用 problem 关键词兜底选最近节点。
    """
    if not category:
        return ""
    d = CATEGORY_TO_DOMAIN.get(category)
    if d is None:
        return ""
    if d:
        return d
    # d 为空：尝试关键词兜底
    p = problem or ""
    coarse = _COARSE_KEYWORD_DOMAIN.get(category, [])
    for domain_en, kws in coarse:
        if any(k.lower() in p.lower() for k in kws):
            return domain_en
    return ""


def kg_hint(problem: str, max_len: int = 1400):
    """返回 (domain_en, hint_str)。

    domain_en=图谱节点 key；hint_str=图谱方法论文本（含图谱题型标识），
    无法分类/无法映射/检索异常时返回 ("", "")。绝不抛异常。
    """
    try:
        if not problem:
            return "", ""
        from skills import classify                      # 目标系统分类器
        from knowledge_graph import retrieve_kg          # 图谱检索（随附 knowledge_graph.py）
        category = classify(problem)
        domain_en = domain_for_cn(category, problem)
        if not domain_en:
            return "", ""
        hint = retrieve_kg(domain_en, problem, use_extension=True, max_len=max_len)
        return (domain_en, hint) if hint else ("", "")
    except Exception:  # noqa: BLE001
        return "", ""


if __name__ == "__main__":
    # 自检：打印 18 类中文类别的映射结果
    print("=== CATEGORY_TO_DOMAIN 覆盖检查 ===")
    for c in sorted(CATEGORY_TO_DOMAIN):
        print(f"  {c} -> {CATEGORY_TO_DOMAIN[c] or '(空, 靠关键词兜底)'}")
    print("=== 端到端示例 ===")
    for q in ["求满足 x^3+y^3=91 的整数对", "热传导方程初边值问题", "求矩阵 A 的特征值", "用排列组合计数"]:
        de, h = kg_hint(q)
        print(f"  {q!r}: domain={de or '空'}  hint_len={len(h)}")