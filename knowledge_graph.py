"""
knowledge_graph.py — 数学定理/知识图谱检索（技术创新展示模块）

图谱数据 knowledge_graph.json：18 学科 × 知识模块（从 18 本 skill 手册构建）。
检索：题面命中知识点名（子串）→ 返回该知识点所在学科 + 相关知识点速查。
集成开关 MATH_AGENT_GRAPH=1（默认关，不影响评测主力路径）。
"""

import json
import os
import re

_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_graph.json")

# 题面含这些词的题，把知识点按词命中也算（知识点名可能和题面措辞不同）
_KEYWORDS = {
    "离散数学": ["组合", "递推", "数论", "整除", "素数", "同余", "图", "博弈", "容斥", "鸽巢",
                "生成函数", "卡特兰", "欧拉", "中国剩余", "排列", "计数", "集合",
                "graph", "prime", "modulo", "combin", "permutation", "gcd", "game", "player",
                "induction", "board", "coloring", "tournament"],
    "高等代数": ["矩阵", "行列式", "特征值", "线性空间", "二次型", "多项式", "对角化", "秩",
                "matrix", "determinant", "eigenvalue", "eigenvector", "polynomial", "linear",
                "rank", "diagonal", "vector space"],
    "复分析": ["复变", "留数", "解析函数", "柯西", "洛朗", "全纯", "极点", "共形",
              "residue", "contour", "holomorphic", "analytic", "cauchy", "laurent", "pole",
              "conformal", "integral of"],
    "数学分析": ["极限", "连续", "导数", "积分", "级数", "一致收敛", "上确界", "幂级数", "泰勒",
                "limit", "continuous", "derivative", "integral", "series", "convergence",
                "supremum", "taylor"],
    "概率论": ["概率", "随机变量", "期望", "方差", "分布", "条件概率", "贝叶斯",
              "probability", "random", "expectation", "variance", "distribution", "prob"],
    "数值分析": ["数值", "插值", "牛顿", "差分", "迭代", "误差", "条件数", "有限元",
                "numerical", "interpolation", "newton", "finite difference", "iteration",
                "truncation error", "condition number", "central difference"],
    "偏微分方程": ["偏微分", "热方程", "波动方程", "拉普拉斯", "边值", "散度", "伴随",
                 "pde", "heat", "wave equation", "laplacian", "boundary value", "partial differential"],
    "常微分方程": ["常微分", "初值", "通解", "龙格", "微分方程",
                  "ode", "initial value", "general solution", "wronskian", "bernoulli equation"],
    "抽象代数": ["群", "环", "域", "同态", "子群", "伽罗瓦", "分裂域", "理想", "商群",
                "group", "subgroup", "homomorphism", "galois", "field", "sylow", "ideal",
                "dihedral", "splitting"],
    "线性回归": ["回归", "最小二乘", "拟合", "残差", "异方差", "多重共线性", "决定系数",
                "regression", "least squares", "residual", "heteroscedastic", "vif", "ols"],
    "统计推断": ["估计", "置信", "假设检验", "样本", "p值", "无偏", "似然",
                "estimate", "confidence", "hypothesis", "sample", "likelihood", "unbiased", "p-value"],
    "随机过程": ["马尔可夫", "布朗", "泊松过程", "鞅", "平稳过程", "随机游走",
                "markov", "brownian", "poisson process", "martingale", "random walk", "stationary"],
    "测度积分": ["测度", "勒贝格", "可测", "几乎处处", "收敛定理", "积分",
                "measure", "lebesgue", "measurable", "almost everywhere", "dominated", "fatou"],
    "拓扑学": ["拓扑", "开集", "紧致", "连通", "同胚", "基本群",
              "topolog", "compact", "connected", "homeomorph", "open cover", "closed set"],
    "微分几何": ["曲率", "测地线", "流形", "高斯", "黎曼", "法向量",
                "curvature", "geodesic", "manifold", "gauss", "riemann", "surface"],
    "泛函分析": ["巴拿赫", "希尔伯特", "算子", "泛函", "弱收敛", "范数",
                "banach", "hilbert", "operator", "functional", "bounded", "norm"],
    "运筹学": ["线性规划", "单纯形", "运输", "整数规划", "对偶", "排队", "指派", "调度", "赛程",
               "schedule", "tournament", "linear programming", "simplex", "minimize the total cost",
               "maximum flow", "shortest path", "optimization"],
    "非基础及进阶课程": ["几何", "圆", "三角", "凸", "内心", "外心", "角平分线", "共线", "共圆",
                         "triangle", "circumcircle", "polygon", "四边形", "chessboard", "grid",
                         "convex", "bisector", "inscribed"],
}


def _load():
    with open(_GRAPH, encoding="utf-8") as f:
        return json.load(f)


def graph_query(problem: str, top_per_discipline: int = 4) -> str:
    """按题面命中学科 → 返回「相关定理/知识点速查」。无命中返回空串。"""
    if os.environ.get("MATH_AGENT_GRAPH", "0") != "1":
        return ""
    text = (problem or "").casefold()
    g = _load()
    # 命中学科：关键词匹配 + 知识点名子串命中
    hits = set()
    matched_topics = []
    for disc, kws in _KEYWORDS.items():
        if any(kw.casefold() in text for kw in kws):
            hits.add(disc)
    for node in g["nodes"]:
        name = node["name"].casefold()
        # 知识点名里的判别词（去掉修饰）出现在题面即命中
        if len(node["name"]) <= 30 and name in text:
            hits.add(node["discipline"])
            matched_topics.append(node["name"])
    if not hits:
        return ""
    # 组速查文本
    parts = [f"知识图谱定位到学科：{'、'.join(sorted(hits))}"]
    if matched_topics:
        parts.append("直接命中的知识点：" + "；".join(matched_topics[:6]))
    for disc in sorted(hits):
        topics = [n["name"] for n in g["nodes"] if n["discipline"] == disc]
        parts.append(f"\n[{disc} 相关定理/知识点]" + "、".join(topics[:top_per_discipline]))
    return "\n".join(parts)
