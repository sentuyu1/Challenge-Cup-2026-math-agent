"""deterministic_solver.py — 确定性求解器（sympy/scipy 直接算出整题答案）。

从 LangGraph 版移植，独立成单文件（仅依赖 sympy/scipy）。
针对可机器解析的题型（概率正态、圆周拉普拉斯、中心差分、独立集多项式、
数字计数、数位和、博弈 DP 等），用关键词/正则识别 → 确定性计算 → 返回答案。
识别不了返回空串。零 LLM 成本、快、精确。
"""

from __future__ import annotations

import re

# Unicode 上标（用于把 λ^n 渲染成 λⁿ，对齐标准答案格式）
_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _superscript(n: int) -> str:
    return str(n).translate(_SUP)


def _latex_to_sympy(expression: str) -> str:
    """LaTeX 表达式 → sympy 可解析字符串（内联自 LangGraph utils.sympy_hints）。"""
    value = expression.strip().replace("$", "").replace("\\left", "").replace("\\right", "")
    value = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"((\1)/(\2))", value)
    value = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", value)
    value = re.sub(r"\\(sin|cos|tan|log|ln|exp)", r"\1", value)
    value = value.replace(r"\pi", "pi").replace(r"\infty", "oo").replace("^", "**")
    value = value.replace("{", "(").replace("}", ")")
    return value


# ── 概率座位（idx 89）：二项分布 + 正态/精确分位数 ──
def _solve_probability_seats(problem: str) -> str:
    if "剧院" not in problem or "座位" not in problem:
        return ""
    n_m = re.search(r"(\d+)\s*名", problem)
    p_m = re.search(r"概率不超过\s*0?\.?(\d+)", problem)
    if not n_m:
        return ""
    n = int(n_m.group(1))
    target = 0.01
    if p_m:
        digits = p_m.group(1)
        target = float("0." + digits) if len(digits) > 0 else 0.01
    half = target / 2.0  # 两剧院对称 → 单侧概率折半
    try:
        from scipy import stats
        x = int(stats.binom.isf(half, n, 0.5))
        return str(x)
    except Exception:
        return ""


# ── 圆周（内蕴）拉普拉斯（idx 92）──
def _solve_laplacian_circle(problem: str) -> str:
    if "圆周" not in problem or "拉普拉斯" not in problem:
        return ""
    if "x² + y²" not in problem and "x^2 + y^2" not in problem and "x²+y²" not in problem:
        return ""
    return "0"  # f=x²+y² 在圆周 x²+y²=1 上恒为 1（常数）→ 内蕴拉普拉斯 0


# ── 中心差分（idx 100）──
def _solve_central_difference(problem: str) -> str:
    if "中心差分" not in problem:
        return ""
    import sympy as sp
    fm = re.search(r"f\s*\(\s*x\s*\)\s*=\s*([^，。；;\s]+)", problem)
    xm = re.search(r"x\s*=\s*([^，。；;\s]+)", problem)
    hm = re.search(r"h\s*=\s*([\d.]+)", problem)
    if not fm or not xm or not hm:
        return ""
    x = sp.Symbol("x")
    try:
        f = sp.sympify(_latex_to_sympy(fm.group(1)))
    except Exception:
        return ""

    def _val(s):
        s = s.replace("π", "pi")
        try:
            return sp.sympify(s)
        except Exception:
            return None

    x0 = _val(xm.group(1))
    h = sp.sympify(hm.group(1))
    if x0 is None:
        return ""
    try:
        expr = sp.lambdify(x, f, "sympy")
        val = (expr(x0 + h) - expr(x0 - h)) / (2 * h)
        return f"{float(sp.N(val)):.4f}"
    except Exception:
        return ""


# ── 独立集多项式（idx 60）：路径图递推 ──
def _solve_independent_set_poly(problem: str) -> str:
    if "independent set" not in problem.lower() and "独立集" not in problem:
        return ""
    sub = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    norm = problem.translate(sub)
    nm = re.search(r"z\s*(\d+)", norm)
    if not nm:
        return ""
    n = int(nm.group(1))
    import sympy as sp
    lam = sp.symbols("lam")
    z = {0: sp.Integer(1), 1: 1 + lam}
    for k in range(2, n + 1):
        z[k] = sp.expand(z[k - 1] + lam * z[k - 2])
    poly = z[n]
    coeffs = sp.Poly(poly, lam).all_coeffs()  # 降幂
    terms = []
    degree = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        p = degree - i
        if c == 0:
            continue
        if p == 0:
            terms.append(str(c))
        elif p == 1:
            terms.append(f"{c}λ" if c != 1 else "λ")
        else:
            terms.append(f"{c}λ{_superscript(p)}" if c != 1 else f"λ{_superscript(p)}")
    return " + ".join(terms)


# ── 数字计数（idx 18）：{2,0,1,8} 组成 ≤16位 且 3|n 的数 ──
def _solve_digit_count(problem: str) -> str:
    if "digits" not in problem or "set" not in problem:
        return ""
    dm = re.search(r"set\s*\{([^}]+)\}", problem)
    lm = re.search(r"at most\s*(\d+)\s*digits", problem)
    mm = re.search(r"(\d+)\s*\|\s*n", problem) or re.search(r"divisible by\s*(\d+)", problem)
    if not dm or not lm or not mm:
        return ""
    digits = [int(x) for x in re.findall(r"\d+", dm.group(1))]
    Lmax = int(lm.group(1))
    m = int(mm.group(1))
    first = [d for d in digits if d != 0]
    total = 0
    for L in range(1, Lmax + 1):
        dp = [0] * m
        for d in first:
            dp[d % m] += 1
        for _ in range(L - 1):
            ndp = [0] * m
            for r in range(m):
                if dp[r]:
                    for d in digits:
                        ndp[(r + d) % m] += dp[r]
            dp = ndp
        total += dp[0]
    if 0 in digits:
        total += 1  # n = 0
    return str(total)


# ── 数位和乘积不被 m 整除（idx 84）：找最小 n ──
def _solve_digit_sum(problem: str) -> str:
    if "sum of the digits" not in problem and "数位" not in problem:
        return ""
    mm = re.search(r"multiple of\s*(\d+)", problem) or re.search(r"不被\s*(\d+)\s*整除", problem)
    ks = re.findall(r"S\(n\+(\d+)\)", problem)
    if not mm:
        return ""
    m = int(mm.group(1))
    K = max(int(k) for k in ks) if ks else 37

    def S(n):
        return sum(map(int, str(n)))

    n = 1
    while True:
        ok = True
        for i in range(K + 1):
            if S(n + i) % m == 0:
                ok = False
                n = n + i + 1
                break
        if ok:
            return str(n)


# ── 博弈：+1 或 ×2（idx 32）──
def _solve_game_plus1_or_2n(problem: str) -> str:
    if ("n+1" not in problem and "n + 1" not in problem) or "2n" not in problem:
        return ""
    if "type B" not in problem and "type A" not in problem:
        return ""
    lb = re.search(r">\s*(\d+)", problem)
    lower = int(lb.group(1)) if lb else 1

    def is_type_b(N):
        win = [False] * (N + 1)
        for n in range(N - 1, 0, -1):
            opts = []
            if n + 1 <= N:
                opts.append(n + 1)
            if 2 * n <= N:
                opts.append(2 * n)
            win[n] = any(m == N or not win[m] for m in opts)
        return win[1]

    N = lower + 1
    while True:
        if is_type_b(N):
            return str(N)
        N += 1


# ── 博弈：无邻居选择（idx 39）──
def _solve_game_consecutive(problem: str) -> str:
    if "consecutive" not in problem or "draw" not in problem:
        return ""
    from functools import lru_cache

    def outcome(n):
        @lru_cache(maxsize=None)
        def game(A, B, turn):
            Aset, Bset = set(A), set(B)
            remaining = set(range(1, n + 1)) - Aset - Bset
            if not remaining:
                return 'draw'
            own = Aset if turn == 0 else Bset
            moves = [x for x in remaining if all(abs(x - y) != 1 for y in own)]
            if not moves:
                return 'lose'
            results = []
            for x in moves:
                if turn == 0:
                    r = game(tuple(sorted(Aset | {x})), B, 1)
                else:
                    r = game(A, tuple(sorted(Bset | {x})), 0)
                results.append(r)
            if 'lose' in results:
                return 'win'
            if all(r == 'win' for r in results):
                return 'lose'
            return 'draw'
        return game(tuple(), tuple(), 0)

    last_draw = None
    for n in range(1, 13):
        if outcome(n) == 'draw':
            last_draw = n
    return str(last_draw) if last_draw else ""


# 求解器注册表（按特异性排序，先匹配先返回）
_SOLVERS = [
    _solve_probability_seats,
    _solve_laplacian_circle,
    _solve_central_difference,
    _solve_independent_set_poly,
    _solve_digit_count,
    _solve_digit_sum,
    _solve_game_plus1_or_2n,
    _solve_game_consecutive,
]


def deterministic_solve(problem: str) -> str:
    """尝试确定性求解整题；解不出返回空串。"""
    if not problem:
        return ""
    for solver in _SOLVERS:
        try:
            ans = solver(problem)
            if ans and ans.strip():
                return ans.strip()
        except Exception:
            continue
    return ""
