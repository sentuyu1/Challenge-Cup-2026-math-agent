"""
skills.py — 数学领域 skill 手册分类与选段（移植自 ICMA）

18 个领域的解题方法论手册（skills_pythonscripts/），确定性分类后注入对应领域的
手册指导模型解题。零 LLM 成本：高精度 domain_override 规则 + 关键词匹配兜底。

来源：
  - 手册目录 skills_pythonscripts/ ← ICMA 的 skills_pythonscripts/
  - 选段逻辑 skill_excerpt.py ← ICMA 的 utils/skill_excerpt.py
  - 分类规则 ← ICMA 的 utils/skills_loader.py + nodes/classifier_node.py
"""

import re
from pathlib import Path

from skill_excerpt import select_skill_excerpt

SKILLS_DIR = Path(__file__).resolve().parent / "skills_pythonscripts"

# ── 领域关键词表（移植自 ICMA skills_loader.py DOMAIN_ALIASES）──────────────
DOMAIN_ALIASES = {
    "概率论": ["依概率", "依分布", "几乎必然", "随机变量", "分布函数", "概率收敛",
               "中心极限定理", "大数定律", "贝叶斯", "全概率", "二项分布", "泊松分布",
               "指数分布", "正态分布", "矩母函数", "特征函数"],
    "随机过程": ["Brownian", "布朗", "Wiener", "首达时", "停时", "鞅", "Markov链",
                 "马尔可夫", "Poisson过程", "泊松过程", "生灭过程", "更新过程", "随机游走"],
    "数学分析": ["一致收敛", "函数列", "函数项级数", "逐点收敛", "极限函数", "可导",
                 "导数列", "Taylor", "泰勒", "幂级数", "含参积分", "广义积分", "上确界",
                 "Fourier变换", "Cauchy数列", "完备度量空间", "差商", "Laplacian on circle"],
    "统计推断": ["最大似然", "MLE", "置信区间", "假设检验", "拒绝域", "显著性水平",
                 "p值", "样本", "估计量", "无偏", "方差估计", "极大似然", "矩估计",
                 "Fisher", "第二类错误", "功效", "似然比", "检验统计量", "临界值",
                 "统计图形", "直方图", "散点图", "箱线图", "时间数列", "时间序列",
                 "趋势变动", "季节变动", "移动平均", "指数平滑", "样本均值", "样本方差"],
    "复分析": ["留数", "解析", "全纯", "Cauchy", "柯西", "Laurent", "洛朗", "极点"],
    "抽象代数": ["有限域", "群", "环", "理想", "同态", "子群", "正规子群", "域扩张",
                 "Galois", "分裂域", "二面体群", "换位子群", "Sylow"],
    "高等代数": ["矩阵", "特征值", "特征向量", "线性空间", "秩", "行列式", "二次型",
                 "极小多项式", "对称多项式", "特征多项式", "二元域", "max-plus", "热带代数"],
    "常微分方程": ["常微分", "ODE", "初值问题", "通解", "特解", "Wronskian"],
    "偏微分方程": ["偏微分", "PDE", "热方程", "波动方程", "Laplace方程", "边值问题",
                   "形式伴随", "散度型", "formal adjoint", "divergence-form"],
    "泛函分析": ["Banach", "Hilbert", "有界线性算子", "泛函", "弱收敛", "紧算子"],
    "拓扑学": ["拓扑", "开集", "闭集", "紧致", "连通", "同胚", "基本群"],
    "微分几何": ["流形", "曲率", "测地线", "联络", "切空间", "第一基本形式"],
    "数值分析": ["插值", "Newton", "迭代", "误差", "数值积分", "Runge-Kutta", "中心差分",
                 "数值微分", "复化", "梯形公式", "Simpson", "Romberg", "Frobenius",
                 "条件数", "Euler", "稳定区间", "Doolittle", "LU分解", "有限差分",
                 "有限元", "有限体积", "截断误差", "finite difference", "finite element",
                 "condition number", "numerical discretization"],
    "测度积分": ["测度", "可测", "Lebesgue", "勒贝格", "几乎处处", "支配收敛", "Fatou"],
    "运筹学": ["线性规划", "单纯形", "对偶", "运输问题", "排队", "决策树", "指派问题",
               "整数规划", "分支定界", "最短路", "关键路径", "目标规划", "KKT",
               "调度", "资源分配", "linear programming", "simplex", "scheduling",
               "branch and bound", "assignment problem", "maximum flow"],
    "离散数学": ["图", "树", "组合", "递推", "生成函数", "布尔", "命题逻辑", "数论",
                 "整除", "素数", "丢番图", "同余", "鸽巢", "组合博弈", "拉丁方"],
    "非基础及进阶课程": ["欧氏几何", "平面几何", "凸几何", "射影几何", "外心", "内心",
                         "垂心", "角平分线", "外接圆", "内切圆", "根轴", "极点极线",
                         "切弦角", "circumcenter", "orthocenter", "circumcircle",
                         "radical axis", "polar line"],
    "线性回归": ["回归", "最小二乘", "OLS", "残差", "t检验", "F检验", "R方", "标准误",
                 "SSE", "SSR", "SST", "ANOVA", "方差分析表", "均值响应", "预测区间",
                 "Gauss-Markov", "Durbin-Watson", "BLUE", "偏F", "多重共线性", "VIF",
                 "异方差", "内生性", "工具变量", "非参数回归", "非线性回归", "残差图", "自相关"],
}


def _has_any(text: str, cues) -> bool:
    for cue in cues:
        needle = str(cue or "").casefold()
        if not needle:
            continue
        if re.fullmatch(r"[a-z0-9-]{2,4}", needle):
            if re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text):
                return True
        elif needle in text:
            return True
    return False


def _has_cue_groups(text: str, *groups) -> bool:
    return all(_has_any(text, group) for group in groups)


def _domain_override(problem: str, categories) -> str:
    """高精度边界规则：判别快 LLM 分类常混淆的领域（移植自 ICMA classifier_node）。"""
    text = re.sub(r"\s+", " ", str(problem or "")).casefold()
    available = set(categories)

    numerical_cues = ("数值分析", "条件数", "有限差分", "有限元", "有限体积", "截断误差",
                      "数值微分", "数值积分", "离散化", "中心差分", "前向差分", "后向差分",
                      "差分公式", "病态矩阵", "condition number", "finite difference",
                      "finite element", "finite volume", "truncation error",
                      "numerical differentiation", "numerical integration",
                      "numerical discretization", "newton-cotes")
    if "数值分析" in available and _has_any(text, numerical_cues):
        return "数值分析"

    regression_cues = ("计量经济", "线性回归", "非参数回归", "非线性回归", "回归系数",
                       "逐步回归", "异方差", "内生性", "工具变量", "残差图", "残差",
                       "最小二乘", "ols", "gauss-markov", "多重共线性", "vif",
                       "durbin-watson", "拟合优度", "regression coefficient",
                       "heteroscedastic", "endogeneity", "instrumental variable")
    if "线性回归" in available and _has_any(text, regression_cues):
        return "线性回归"

    stats_cues = ("统计图形", "直方图", "散点图", "箱线图", "条形图", "时间数列", "时间序列",
                  "趋势变动", "季节变动", "循环变动", "不规则变动", "季节调整", "移动平均",
                  "指数平滑", "自相关图", "抽样分布", "总体参数", "样本均值", "样本方差",
                  "频数分布", "集中趋势", "histogram", "box plot", "time series",
                  "seasonal adjustment", "moving average", "exponential smoothing",
                  "sampling distribution")
    normal_parameter_question = _has_cue_groups(
        text, ("正态分布", "normal distribution"),
        ("两个参数", "参数分别", "parameters", "mean and variance", "mean and standard deviation"))
    data_summary_question = _has_cue_groups(
        text, ("数据", "data"), ("分散程度", "离散程度", "集中趋势", "频数分布", "dispersion"))
    if "统计推断" in available and (_has_any(text, stats_cues) or normal_parameter_question or data_summary_question):
        return "统计推断"

    pde_direct = ("偏微分方程", "partial differential equation", "形式伴随", "formal adjoint",
                  "散度型", "divergence-form", "热方程", "波动方程", "poisson equation")
    pde_adjoint = _has_cue_groups(text, ("伴随算子", "adjoint operator", "adjoint"),
                                  ("c_0^", "\\partial_i", "∂_i", "微分算子", "differential operator", "omega"))
    if "偏微分方程" in available and (_has_any(text, pde_direct) or pde_adjoint):
        return "偏微分方程"

    abstract_cues = ("galois", "分裂域", "splitting field", "域扩张", "field extension",
                     "正规子群", "normal subgroup", "换位子群", "commutator subgroup",
                     "二面体群", "dihedral group", "sylow", "商群", "quotient group",
                     "理想", "ideal of", "有限域", "finite field")
    if "抽象代数" in available and _has_any(text, abstract_cues):
        return "抽象代数"

    analysis_cues = ("数学分析", "一致收敛", "uniform convergence", "逐点收敛",
                     "pointwise convergence", "极限函数", "limit function", "广义积分",
                     "improper integral", "含参积分", "power series", "幂级数", "上确界",
                     "supremum", "fourier transform", "fourier 变换", "cauchy数列",
                     "cauchy sequence", "完备度量空间", "taylor expansion", "泰勒展开")
    circle_laplacian = _has_cue_groups(text, ("圆周", "on the circle", "restricted to the circle"),
                                       ("拉普拉斯算子", "laplacian"))
    if "数学分析" in available and (_has_any(text, analysis_cues) or circle_laplacian):
        return "数学分析"

    or_direct = ("运筹学", "线性规划", "linear programming", "单纯形", "simplex method",
                 "运输问题", "transportation problem", "整数规划", "integer programming",
                 "分支定界", "branch and bound", "指派问题", "assignment problem",
                 "关键路径", "critical path", "最大流", "maximum flow", "最短路",
                 "shortest path", "目标规划", "排队模型", "queueing model")
    scheduling_optimisation = _has_cue_groups(text, ("schedule", "scheduling", "赛程", "调度"),
                                              ("minimize the total cost", "minimum total cost",
                                               "最小总成本", "费用最小"))
    allocation_game = _has_cue_groups(text, ("boxes", "箱子"), ("pebbles", "石子"),
                                      ("distributes", "分配"), ("each subsequent round", "随后每轮", "每一轮"))
    if "运筹学" in available and (_has_any(text, or_direct) or scheduling_optimisation or allocation_game):
        return "运筹学"

    high_algebra_cues = ("高等代数", "minimal polynomial", "极小多项式", "symmetric polynomial",
                         "对称多项式", "characteristic polynomial", "特征多项式", "eigenvalue",
                         "特征值", "linear space", "线性空间", "quadratic form", "二次型",
                         "jordan form", "jordan 标准形", "max-plus", "tropical algebra", "热带代数")
    if "高等代数" in available and _has_any(text, high_algebra_cues):
        return "高等代数"

    diff_geo_markers = ("曲率", "curvature", "测地线", "geodesic", "流形", "manifold",
                        "第一基本形式", "second fundamental form", "frenet", "weingarten",
                        "gauss-bonnet", "法曲率", "主曲率", "平均曲率", "torsion")
    classic_geometry = ("切弦角定理", "tangent-chord theorem", "极点极线", "polar line",
                        "la hire", "根轴", "radical axis", "共轴", "coaxal", "外心",
                        "circumcenter", "内心", "incenter", "垂心", "orthocenter", "圆周角",
                        "angle bisector", "角平分线", "circumcircle", "外接圆", "内切圆")
    polygon_geometry = _has_cue_groups(text,
        ("convex polygon", "convex quadrilateral", "convex polyhedron", "凸多边形", "凸四边形", "凸多面体",
         "m-gon", "-gon", "n-sided polygon", "-sided polygon"),
        ("area", "diagonal", "face", "visible", "circumscribed", "面积", "对角线", "面可见", "外切"))
    triangle_geometry = _has_cue_groups(text,
        ("triangle", "三角形"),
        (" angle ", " angles ", "\\angle", "tangent", "circumcenter", "circumcircle", "bisector",
         "角", "切线", "外心", "外接圆", "平分线"))
    if ("非基础及进阶课程" in available and not _has_any(text, diff_geo_markers)
            and (_has_any(text, classic_geometry) or polygon_geometry or triangle_geometry)):
        return "非基础及进阶课程"

    number_theory_floor = _has_cue_groups(text, ("prime", "素数"), ("floor", "\\lfloor", "取整"),
                                          ("integer", "整数"))
    diophantine_radical = _has_cue_groups(text, ("pairs of positive integers", "正整数对"),
                                          ("cube root", "\\sqrt[3]", "立方根"), ("satisfy", "满足"))
    if "离散数学" in available and (number_theory_floor or diophantine_radical):
        return "离散数学"

    return None


_categories_cache = None


def _get_categories():
    global _categories_cache
    if _categories_cache is None:
        _categories_cache = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())
    return _categories_cache


def classify(problem: str) -> str:
    """确定性分类：高精度 domain_override 规则优先，关键词匹配兜底。"""
    cats = _get_categories()
    override = _domain_override(problem, cats)
    if override:
        return override
    scores = {}
    for cat in cats:
        kws = DOMAIN_ALIASES.get(cat, []) + [cat]
        scores[cat] = sum(1 for kw in kws if kw and kw in problem)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "离散数学"  # 组合/数论/博弈是奥数题主体


_doc_cache = {}


def get_skill_document(category: str) -> str:
    if category not in _doc_cache:
        f = SKILLS_DIR / category / f"{category}skill.md"
        try:
            _doc_cache[category] = f.read_text(encoding="utf-8")
        except Exception:
            _doc_cache[category] = ""
    return _doc_cache[category]


def skill_context(problem: str, limit: int = 2600):
    """返回 (category, excerpt)：分类 + 从手册选与题目最相关的模块。"""
    category = classify(problem)
    doc = get_skill_document(category)
    excerpt = select_skill_excerpt(doc, problem, limit) if doc else ""
    return category, excerpt
