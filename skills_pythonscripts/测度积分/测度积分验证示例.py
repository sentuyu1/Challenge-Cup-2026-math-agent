# 测度积分：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是提供给数学智能体的提示资料，包含可摘取的 Python/SymPy 核验片段，不是可直接运行的完整程序。

## 使用规则
- 先从题面确定底空间、$\sigma$-代数、测度、函数定义域和“几乎处处”的量词；题面没有给出的测度或支配函数不得补造。
- 每个结论要同时说明可测性、积分存在性和适用定理的前提；Riemann 积分的直觉不能替代 Lebesgue 条件。
- 只在条件完整时建议符号或数值核验；核验应检查原定义或原积分，不能只将候选结论回代自身。

## 知识点 1：测度、外测度与可测性
- 识别可数可加性、单调性、连续性，以及 Caratheodory 可测性条件。
- 集合运算题先写明补集、可数并交所在的 $\sigma$-代数；区分“零测集”和“空集”。
- 若函数以指标函数、简单函数或分层集合给出，先验证各层集合可测。

## 知识点 2：Lebesgue 积分与简单函数
- 非负简单函数 $\varphi=\sum a_i\mathbf 1_{E_i}$ 满足 $\int\varphi\,d\mu=\sum a_i\mu(E_i)$；一般函数先分解为正负部。
- 可积的判据是 $\int |f|\,d\mu<\infty$，不能只证明形式积分存在。
- 处理分段函数时分别核对每一段的可测性、绝对可积性和端点归属。

## 知识点 3：收敛定理
- 单调收敛定理：非负且 $f_n\uparrow f$；结论允许积分为无穷大。
- Fatou 引理：非负函数列，方向为 $\int\liminf f_n\le\liminf\int f_n$。
- 支配收敛定理：逐点几乎处处收敛并存在 $g\in L^1$ 使 $|f_n|\le g$；必须把支配函数写出来。
- 换极限与积分前，明确使用的是单调、支配还是一致可积等条件。

## 知识点 4：$L^p$ 空间与不等式
- $\|f\|_p=(\int|f|^p)^{1/p}$，$p=\infty$ 使用本性上确界；先确认函数等价类和测度空间。
- Holder 不等式要求 $1/p+1/q=1$；Minkowski 给出三角不等式。不要把不同 $p$ 的范数大小关系脱离测度空间直接比较。

## 知识点 5：Fubini、Tonelli 与 Radon--Nikodym
- 非负函数可用 Tonelli；符号函数交换二重积分通常需要绝对可积性以使用 Fubini。
- Radon--Nikodym 导数需先核对绝对连续性 $\nu\ll\mu$ 和 $\sigma$-有限等前提。

## Python 代码片段：绝对可积与简单函数
```python
import sympy as sp

# 从题面填入 f、x、a、b；先检查绝对可积，再报告积分。
absolute_integral = sp.integrate(sp.Abs(f), (x, a, b))
if absolute_integral.is_finite is False:
    raise ValueError("题设函数未通过绝对可积检查")
integral_value = sp.integrate(f, (x, a, b))

# 对简单函数 sum(a_i * 1_{E_i})，由题面给出的系数与测度组成。
simple_integral = sum(coefficient * measure for coefficient, measure in layers)
```

## Python 代码片段：极限与积分的换序核验
```python
import sympy as sp

# 仅在题面已给出收敛/支配条件时做符号交叉检查；代码不能证明 a.e. 支配。
n = sp.symbols("n", integer=True, positive=True)
pointwise_limit = sp.limit(f_n, n, sp.oo)
candidate_integral = sp.integrate(pointwise_limit, (x, a, b))
term_integrals = sp.integrate(f_n, (x, a, b))
limit_of_integrals = sp.limit(term_integrals, n, sp.oo)
check = sp.simplify(candidate_integral - limit_of_integrals)
```

## Python 代码片段：$L^p$ 范数与 Holder 检查
```python
import sympy as sp

# p、q 必须由题面满足 1/p + 1/q = 1。
norm_f_p = sp.integrate(sp.Abs(f) ** p, (x, a, b)) ** (sp.S.One / p)
norm_g_q = sp.integrate(sp.Abs(g) ** q, (x, a, b)) ** (sp.S.One / q)
pairing = sp.integrate(sp.Abs(f * g), (x, a, b))
holder_gap = sp.simplify(norm_f_p * norm_g_q - pairing)  # 应在可用时非负
```

## 输出契约
- 给出所用定理及全部前提、关键等式和最终结论；涉及“几乎处处”时必须保留该限定。
- 若条件不足，明确说明无法交换极限/积分或无法应用定理，不能以示例数据替代题面。
- 只摘取与当前题目匹配的代码片段，并将其中的变量、边界和参数全部替换为题面数据。

## 模块级验证代码（与测度积分 skill 的 19 个主知识点对应）

## Python 代码片段：模块1 Lebesgue 测度基础
```python
import sympy as sp

interval_measure = sp.simplify(upper - lower)
countable_union_bound = sp.simplify(sum(measures))
measure_residual = sp.simplify(measure_union - countable_union_bound)
```

## Python 代码片段：模块2 可测函数
```python
import sympy as sp

x = sp.symbols("x", real=True)
level_set = sp.solve_univariate_inequality(function >= threshold, x)
measurable_indicator = sp.Piecewise((1, function >= threshold), (0, True))
```

## Python 代码片段：模块3 Lebesgue 积分
```python
import sympy as sp

positive_part = sp.Max(function, 0)
negative_part = sp.Max(-function, 0)
integral_value = sp.integrate(positive_part, (x, lower, upper)) - sp.integrate(
    negative_part, (x, lower, upper)
)
```

## Python 代码片段：模块4 简单函数积分
```python
import sympy as sp

simple_integral = sp.simplify(sum(value * measure_set for value, measure_set in simple_terms))
simple_function = sum(value * sp.Heaviside(x - endpoint) for value, endpoint in simple_terms)
```

## Python 代码片段：模块5 Lp 空间与范数
```python
import sympy as sp

p = sp.symbols("p", positive=True)
lp_power = sp.integrate(sp.Abs(function) ** p, (x, lower, upper))
lp_norm = sp.simplify(lp_power ** (1 / p))
```

## Python 代码片段：模块6 单调收敛定理（Levi 引理）
```python
import sympy as sp

limit_function = sp.limit(monotone_sequence, n, sp.oo)
limit_of_integrals = sp.limit(sp.integrate(monotone_sequence, (x, lower, upper)), n, sp.oo)
integral_of_limit = sp.integrate(limit_function, (x, lower, upper))
monotone_gap = sp.simplify(limit_of_integrals - integral_of_limit)
```

## Python 代码片段：模块7 控制收敛定理
```python
import sympy as sp

pointwise_limit = sp.limit(function_sequence, n, sp.oo)
dominated_gap = sp.simplify(
    sp.limit(sp.integrate(function_sequence, (x, lower, upper)), n, sp.oo)
    - sp.integrate(pointwise_limit, (x, lower, upper))
)
dominating_integral = sp.integrate(dominating_function, (x, lower, upper))
```

## Python 代码片段：模块8 Fatou 引理
```python
import sympy as sp

fatou_left = sp.integrate(sp.limitinf(nonnegative_sequence, n), (x, lower, upper))
fatou_right = sp.limitinf([sp.integrate(nonnegative_sequence.subs(n, k), (x, lower, upper))
                            for k in index_values])
fatou_gap = sp.simplify(fatou_right - fatou_left)
```

## Python 代码片段：模块9 Lp 范数不等式
```python
import sympy as sp

holder_gap = sp.simplify(lp_norm(f * g, 1) - lp_norm(f, p) * lp_norm(g, q))
minkowski_gap = sp.simplify(lp_norm(f + g, p) - lp_norm(f, p) - lp_norm(g, p))
```

## Python 代码片段：模块10 Fubini 定理
```python
import sympy as sp

x, y = sp.symbols("x y", real=True)
iterated_xy = sp.integrate(sp.integrate(integrand, (y, y_lower, y_upper)),
                           (x, x_lower, x_upper))
iterated_yx = sp.integrate(sp.integrate(integrand, (x, x_lower, x_upper)),
                           (y, y_lower, y_upper))
fubini_gap = sp.simplify(iterated_xy - iterated_yx)
```

## Python 代码片段：模块11 绝对连续函数与 Newton--Leibniz 公式
```python
import sympy as sp

x, t = sp.symbols("x t", real=True)
reconstructed = function_at_left + sp.integrate(derivative.subs(x, t), (t, left, x))
newton_leibniz_gap = sp.simplify(reconstructed - function)
```

## Python 代码片段：模块12 Radon--Nikodym 定理
```python
import sympy as sp

candidate_density = sp.simplify(sp.diff(cumulative_measure, x))
measure_reconstruction = sp.integrate(candidate_density, (x, lower, upper))
rn_gap = sp.simplify(measure_reconstruction - total_measure)
```

## Python 代码片段：模块13 Chebyshev 不等式
```python
import sympy as sp

chebyshev_bound = sp.simplify(variance / deviation ** 2)
event_indicator_expectation = sp.simplify(sp.integrate(indicator * density, (x, lower, upper)))
```

## Python 代码片段：模块14 Holder 不等式
```python
import sympy as sp

lhs = sp.integrate(sp.Abs(f * g), (x, lower, upper))
rhs = lp_norm(f, p) * lp_norm(g, q)
holder_residual = sp.simplify(rhs - lhs)
```

## Python 代码片段：模块15 Minkowski 不等式
```python
import sympy as sp

lhs = lp_norm(f + g, p)
rhs = lp_norm(f, p) + lp_norm(g, p)
minkowski_residual = sp.simplify(rhs - lhs)
```

## Python 代码片段：模块16 a.e. 收敛与 Lp 收敛
```python
import sympy as sp

almost_everywhere_limit = sp.limit(function_sequence, n, sp.oo)
lp_error = sp.integrate(sp.Abs(function_sequence - limit_function) ** p,
                        (x, lower, upper)) ** (1 / p)
lp_limit = sp.limit(lp_error, n, sp.oo)
```

## Python 代码片段：模块17 卷积
```python
import sympy as sp

t = sp.symbols("t", real=True)
convolution = sp.integrate(first_function(t) * second_function(x - t),
                           (t, -sp.oo, sp.oo))
convolution_check = sp.simplify(sp.integrate(convolution, (x, -sp.oo, sp.oo))
                                - total_first * total_second)
```

## Python 代码片段：模块18 测度构造与绝对连续
```python
import sympy as sp

density_ratio = sp.simplify(sp.diff(measure_numerator, x) / sp.diff(measure_denominator, x))
absolute_continuity_gap = sp.simplify(measure_numerator - sp.integrate(
    density_ratio * sp.diff(measure_denominator, x), (x, lower, upper)))
```

## Python 代码片段：模块21 竞赛拓展——可积性判定与反例
```python
import sympy as sp

near_zero_order = sp.limit(sp.log(abs(function)) / sp.log(x), x, 0, dir="+")
tail_order = sp.limit(sp.log(abs(function)) / sp.log(x), x, sp.oo)
absolute_integral = sp.integrate(sp.Abs(function), (x, lower, upper))
```
