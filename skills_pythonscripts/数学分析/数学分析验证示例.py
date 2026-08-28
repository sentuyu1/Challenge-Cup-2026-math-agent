# 数学分析：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是供数学智能体使用的说明型提示资料，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整程序。

## 使用规则
- 从题面保留定义域、端点、参数范围和量词；逐点/一致、条件/绝对收敛和端点单侧行为必须分开验证。
- 积分、极限、求导和求和的交换都要给出定理依据，例如支配收敛、一致收敛或适当的可积性条件。
- 纯欧氏几何、统计抽样、PDE 形式伴随及代数结构应转相应目录；圆周受限 Laplacian 依题面按数学分析处理。

## 知识点 1：极限、连续与可导
- 极限先检查左右极限、路径依赖和定义域；多元极限不能只沿一条路径验证。
- 连续性和可导性分别判断；导数存在不自动给出高阶可导。
- 中值定理、Taylor 展开使用前确认区间和光滑阶数。

## 知识点 2：级数与幂级数
- 正项级数用比较、比值或根值判别；交错级数要同时说明项单调趋零。
- 幂级数给出收敛半径后，端点必须逐个单独判断。
- 函数项级数逐点收敛不等于一致收敛；Weierstrass 判别法要提供可和的上界。

## 知识点 3：广义积分与含参积分
- 无穷区间、无界被积函数和端点奇异性分开处理；绝对收敛比条件收敛更强。
- 含参积分求导/换序需验证局部一致收敛、支配条件或 Leibniz 规则的前提。
- Beta/Gamma、Fourier 变换和积分变换必须说明参数范围及归一化约定。

## 知识点 4：确界、变差与函数方程
- 确界题给上界及逼近上界的序列/构造；有界不自动取得最大值。
- 有界变差、绝对连续和可微性的关系不能倒置。
- 函数方程先代入零、对称点和可组合变量，再用连续性、单调性或有界性等题设条件排除伪解。

## Python 代码片段：极限、连续与可导的核验
```python
import sympy as sp

x = sp.symbols("x", real=True)
# f、point 与 candidate_limit 均由题面或独立推导给出。
left_limit = sp.limit(f, x, point, dir="-")
right_limit = sp.limit(f, x, point, dir="+")
two_sided_limit = sp.limit(f, x, point)
derivative = sp.diff(f, x)
limit_gap = sp.simplify(two_sided_limit - candidate_limit)
```

## Python 代码片段：Taylor 展开、幂级数与端点
```python
import sympy as sp

x = sp.symbols("x", real=True)
# expansion_point、order、series_term 与系数 a_n 由题面给出。
taylor = sp.series(f, x, expansion_point, order)
n = sp.symbols("n", integer=True, positive=True)
inverse_radius = sp.limit(sp.Abs(a_n.subs(n, n + 1) / a_n), n, sp.oo)
radius = sp.simplify(1 / inverse_radius)
left_endpoint_check = sp.summation(series_term.subs(x, left_endpoint), (n, start_index, sp.oo))
right_endpoint_check = sp.summation(series_term.subs(x, right_endpoint), (n, start_index, sp.oo))
```

## Python 代码片段：广义积分与含参积分
```python
import sympy as sp

x, parameter = sp.symbols("x parameter", real=True)
# 端点、参数范围与 integrand 均由题面提供。
improper_value = sp.integrate(integrand, (x, lower_bound, upper_bound))
parameter_derivative = sp.diff(integrand, parameter)
differentiated_integral = sp.integrate(parameter_derivative, (x, lower_bound, upper_bound))
endpoint_limit = sp.limit(sp.integrate(integrand, (x, lower_bound, cutoff)), cutoff, upper_bound)
```

## Python 代码片段：函数列的一致性抽查
```python
import sympy as sp

n = sp.symbols("n", integer=True, positive=True)
x = sp.symbols("x", real=True)
pointwise_limit = sp.limit(function_sequence, n, sp.oo)
difference = sp.simplify(function_sequence - pointwise_limit)
# 仅在题面给出候选上界 M_n 时检查 M_n 的可和/趋零性质；代码不能证明一致收敛本身。
majorant_limit = sp.limit(majorant_n, n, sp.oo)
```

## 输出契约
- 最终答案须包含定义域/参数条件、所用定理、端点或一致性检查和明确结论。
- 题面缺少足以交换极限、积分或级数的条件时，报告条件不足而不擅自补全。
- SymPy 片段用于计算候选极限、导数和积分；一致收敛、支配条件和端点论证必须在文字中完整给出。

## 模块级验证代码（与数学分析 skill 的 7 个主知识点对应）

## Python 代码片段：模块1 极限、连续与可导
```python
import sympy as sp

x, h = sp.symbols("x h", real=True)
limit_value = sp.limit(expression, x, limit_point, dir=direction)
difference_quotient = sp.simplify((function.subs(x, x0 + h) - function.subs(x, x0)) / h)
derivative_value = sp.limit(difference_quotient, h, 0)
```

## Python 代码片段：模块2 高阶导数、Taylor 展开与幂级数
```python
import sympy as sp

x = sp.symbols("x", real=True)
taylor = sp.series(function, x, expansion_point, order).removeO()
coefficient = sp.expand(taylor).coeff(x - expansion_point, coefficient_index)
radius = 1 / sp.limit(abs(coefficient_sequence) ** (1 / n), n, sp.oo)
```

## Python 代码片段：模块3 广义积分与含参积分
```python
import sympy as sp

x, parameter = sp.symbols("x parameter", positive=True)
integral_value = sp.integrate(integrand, (x, lower_endpoint, upper_endpoint))
parameter_derivative = sp.simplify(sp.diff(integral_family, parameter).subs(parameter, parameter0))
endpoint_limit = sp.limit(integral_value, x, singular_endpoint, dir=approach_direction)
```

## Python 代码片段：模块4 数项级数、函数项级数与一致收敛
```python
import sympy as sp

n, x = sp.symbols("n x", integer=True, positive=True)
partial_sum = sp.summation(term, (n, 1, N))
series_sum = sp.summation(term, (n, 1, sp.oo))
majorant_limit = sp.limit(sp.sup(abs(term), (x, domain_left, domain_right)), n, sp.oo)
```

## Python 代码片段：模块5 确界、有界变差与积分基本性质
```python
import sympy as sp

n, x = sp.symbols("n x", integer=True, positive=True)
sequence_limit = sp.limit(sequence_term, n, sp.oo)
lower_bound = sp.inf(sequence_term, n)
upper_bound = sp.sup(sequence_term, n)
total_variation = sp.integrate(abs(sp.diff(function, x)), (x, interval_left, interval_right))
```

## Python 代码片段：模块6 函数列及极限换序
```python
import sympy as sp

n, x = sp.symbols("n x", integer=True, positive=True)
pointwise = sp.limit(function_sequence, n, sp.oo)
integral_gap = sp.simplify(
    sp.limit(sp.integrate(function_sequence, (x, left, right)), n, sp.oo)
    - sp.integrate(pointwise, (x, left, right))
)
sup_gap = sp.limit(sup_norm_difference, n, sp.oo)
```

## Python 代码片段：模块7 竞赛拓展（Fourier/极值/策略）
```python
import sympy as sp

t, omega = sp.symbols("t omega", real=True)
fourier_coefficient = sp.integrate(function * sp.exp(-sp.I * omega * t), (t, -sp.pi, sp.pi))
constraint_gap = sp.factor(objective.subs(variable, candidate_value) - claimed_bound)
```
