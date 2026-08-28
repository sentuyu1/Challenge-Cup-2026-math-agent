# 常微分方程：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是面向数学智能体的验证说明，包含可摘取的 SymPy 代码片段，不是可直接运行的完整程序。

## 使用规则
- 先写出未知函数、自变量、阶数、初值/边值和允许的定义区间；积分或除法步骤可能丢失的常值解、奇异解必须单独检查。
- 得到通解后回代原方程，再代入初值或边值；不要只验证形式导数而遗漏定义域和解的存在区间。
- 数值近似只在题面给出步长、初值和算法时采用，并报告误差或稳定性条件。

## 知识点 1：一阶方程识别
- 可分离变量：分离后积分，并核对分母为零时的常值解。
- 一阶线性：$y'+P(x)y=Q(x)$，积分因子为 $\mu=e^{\int P\,dx}$。
- 齐次方程可令 $y=vx$；Bernoulli 方程用 $z=y^{1-n}$ 化为线性方程。
- 恰当方程先检验 $M_y=N_x$；若寻找积分因子，需说明它依赖的变量。

## 知识点 2：二阶与高阶线性方程
- 常系数齐次方程由特征根分类：不同实根、重根、共轭复根分别给出完整基解。
- 非齐次方程用待定系数法或参数变易法；共振时特解须乘足够次数的 $x$。
- Euler 方程令 $y=x^m$ 或 $x=e^t$，并保留 $x>0$ 或 $x<0$ 的区间限制。

## 知识点 3：降阶、Laplace 与方程组
- 不显含 $y$ 时令 $p=y'$；不显含 $x$ 时按 $p(y)=y'$ 降阶并注意 $p=0$ 情形。
- Laplace 变换题须带入初始值，并正确处理移位、卷积和阶跃函数。
- 线性方程组 $X'=AX$ 可用特征值/特征向量或矩阵指数；重复特征值时检查是否需要广义特征向量。

## 知识点 4：定性理论与建模
- 存在唯一性要检查初值附近的连续性和对 $y$ 的 Lipschitz 条件。
- 平衡点由 $f(y)=0$ 给出；一维稳定性看 $f'(y_*)$，相平面还应说明线性化或相轨线依据。
- 物理模型先写守恒、阻尼、外力或增长假设，再由量纲和初值检查结果。

## Python 代码片段：一阶或线性 ODE 的求解与回代
```python
import sympy as sp

x = sp.symbols("x", real=True)
y = sp.Function("y")
# 将 ode、初值 x0、y0 替换为题面给出的对象。
solution = sp.dsolve(ode, ics={y(x0): y0})
candidate = solution.rhs
residual = sp.simplify((ode.lhs - ode.rhs).subs(y(x), candidate).doit())
initial_gap = sp.simplify(candidate.subs(x, x0) - y0)
```

## Python 代码片段：常系数特征根与共振检查
```python
import sympy as sp

r = sp.symbols("r")
# coefficients 由题面二阶常系数方程给出，例如 [a, b, c] 表示 ar^2+br+c。
characteristic = sum(coef * r ** power for power, coef in enumerate(reversed(coefficients)))
roots = sp.solve(sp.Eq(characteristic, 0), r)
root_multiplicities = sp.roots(characteristic, r)
# 非齐次试探函数与 roots 有重合时，试探项需乘 x 的相应重数。
```

## Python 代码片段：平衡点与局部稳定性
```python
import sympy as sp

u = sp.symbols("u", real=True)
# rhs 是自治方程 u' = rhs 的右端。
equilibria = sp.solve(sp.Eq(rhs, 0), u)
stability = {point: sp.simplify(sp.diff(rhs, u).subs(u, point)) for point in equilibria}
# 一维情形中导数 < 0 表示局部渐近稳定，> 0 表示不稳定；=0 需另行分析。
```

## 输出契约
- 最终答案至少包含方程类型、通解/特解、初边值常数、有效区间和回代结论。
- 稳定性或相图题必须标注平衡点与稳定类别；题面没有指定数值方法时不凭空加入离散步长。
- 代码只用于回代和辅助求解，不能替代对奇异解、定义区间和定理条件的文字说明。

## 模块级验证代码（与常微分方程 skill 的 20 个模块对应）

## Python 代码片段：模块1 一阶可分离变量方程
```python
import sympy as sp

x = sp.symbols("x", real=True)
y = sp.Function("y")
separated_integral = sp.integrate(1 / y_symbol, y_symbol) - sp.integrate(rhs_x, x)
solution_residual = sp.simplify(sp.diff(candidate, x) - rhs_x * y_factor(candidate))
```

## Python 代码片段：模块2 一阶线性微分方程
```python
import sympy as sp

x = sp.symbols("x", real=True)
integrating_factor = sp.exp(sp.integrate(P, x))
linear_solution = sp.simplify((sp.integrate(integrating_factor * Q, x) + constant) /
                              integrating_factor)
```

## Python 代码片段：模块3 一阶齐次方程
```python
import sympy as sp

v, x = sp.symbols("v x", real=True)
reduced_rhs = sp.simplify(rhs.subs(y, v * x) - v)
homogeneous_integral = sp.integrate(1 / reduced_rhs, v) - sp.log(abs(x))
```

## Python 代码片段：模块4 一阶 Bernoulli 方程
```python
import sympy as sp

x = sp.symbols("x", real=True)
z = sp.Function("z")(x)
transformed_equation = sp.simplify((1 - exponent) * y_symbol ** (-exponent) * ode_rhs)
bernoulli_solution = sp.dsolve(sp.Eq(sp.diff(z, x) + (1 - exponent) * P * z,
                                     (1 - exponent) * Q))
```

## Python 代码片段：模块5 可降阶二阶方程（不显含 y）
```python
import sympy as sp

x = sp.symbols("x", real=True)
p = sp.Function("p")(x)
reduced_equation = sp.simplify(ode.subs(sp.diff(y(x), x, 2), sp.diff(p, x)))
```

## Python 代码片段：模块6 可降阶二阶方程（不显含 x）
```python
import sympy as sp

y, p = sp.symbols("y p", real=True)
reduced_rhs = sp.simplify(p * sp.diff(p, y))
first_integral = sp.integrate(reduced_rhs, y)
```

## Python 代码片段：模块7 二阶常系数齐次线性方程
```python
import sympy as sp

r = sp.symbols("r")
characteristic = sp.Poly(a * r ** 2 + b * r + c, r)
root_data = sp.roots(characteristic.as_expr(), r)
```

## Python 代码片段：模块8 常系数非齐次——多项式型
```python
import sympy as sp

x = sp.symbols("x", real=True)
trial = sum(coefficients[i] * x ** i for i in range(trial_degree + 1))
undetermined = sp.solve(sp.Poly(linear_operator(trial) - forcing, x).coeffs(), coefficients)
```

## Python 代码片段：模块9 常系数非齐次——指数型
```python
import sympy as sp

x, r = sp.symbols("x r", real=True)
characteristic_value = sp.simplify(characteristic_polynomial.subs(r, forcing_rate))
resonance_order = root_multiplicity.get(forcing_rate, 0)
trial_exponential = x ** resonance_order * sp.exp(forcing_rate * x) * trial_polynomial
```

## Python 代码片段：模块10 常系数非齐次——三角型
```python
import sympy as sp

x = sp.symbols("x", real=True)
trial_trigonometric = x ** resonance_order * (A_trial * sp.cos(frequency * x)
                                               + B_trial * sp.sin(frequency * x))
trig_residual = sp.expand(linear_operator(trial_trigonometric) - forcing)
```

## Python 代码片段：模块11 欧拉方程
```python
import sympy as sp

x, m = sp.symbols("x m", positive=True, real=True)
euler_characteristic = sp.expand(a * m * (m - 1) + b * m + c)
euler_roots = sp.solve(sp.Eq(euler_characteristic, 0), m)
```

## Python 代码片段：模块12 Laplace 变换
```python
import sympy as sp

s, t = sp.symbols("s t", positive=True)
laplace_candidate = sp.laplace_transform(candidate, t, s, noconds=True)
initial_value_gap = sp.simplify(candidate.subs(t, initial_time) - initial_value)
```

## Python 代码片段：模块13 幂级数法
```python
import sympy as sp

x = sp.symbols("x")
series_candidate = sp.series(candidate, x, expansion_point, order).removeO()
series_residual = sp.series(ode_operator(series_candidate) - forcing, x, expansion_point, order)
```

## Python 代码片段：模块14 常系数线性微分方程组
```python
import sympy as sp

A = sp.Matrix(system_matrix)
matrix_exponential = sp.exp(A * time)
state_candidate = matrix_exponential * initial_state
system_residual = sp.simplify(state_candidate.diff(time) - A * state_candidate)
```

## Python 代码片段：模块15 解的存在唯一性分析
```python
import sympy as sp

continuity_check = sp.limit(rhs_function, x, x0, dir="+")
lipschitz_derivative = sp.simplify(sp.diff(rhs_function, y_symbol))
```

## Python 代码片段：模块16 稳定性分析
```python
import sympy as sp

equilibrium = sp.solve(sp.Eq(rhs_function, 0), y_symbol)
linearization = {point: sp.simplify(sp.diff(rhs_function, y_symbol).subs(y_symbol, point))
                 for point in equilibrium}
```

## Python 代码片段：模块17 奇点分类与相图分析
```python
import sympy as sp

A = sp.Matrix([[a11, a12], [a21, a22]])
trace = sp.trace(A)
determinant = A.det()
discriminant = sp.factor(trace ** 2 - 4 * determinant)
phase_eigenvalues = A.eigenvals()
```

## Python 代码片段：模块18 正交轨线
```python
import sympy as sp

x, y = sp.symbols("x y", real=True)
orthogonal_slope = sp.simplify(-1 / original_slope)
orthogonal_residual = sp.simplify(
    sp.diff(candidate_curve, x) - orthogonal_slope.subs(y, candidate_curve)
)
```

## Python 代码片段：模块19 物理应用题建模
```python
import sympy as sp

mass_balance = sp.Eq(sp.diff(state, time), input_rate - output_rate)
model_residual = sp.simplify(mass_balance.lhs - mass_balance.rhs)
dimension_check = input_unit == output_unit
```

## Python 代码片段：模块20 参数讨论
```python
import sympy as sp

parameter_thresholds = sp.solve(sp.Eq(discriminant, 0), parameter)
admissible_intervals = sp.solve_univariate_inequality(discriminant > 0, parameter)
```

## Python 代码片段：竞赛拓展——参数化与对数微分
```python
import sympy as sp

x = sp.symbols("x", positive=True)
log_derivative_gap = sp.simplify(
    sp.diff(sp.log(candidate), x) - sp.diff(candidate, x) / candidate
)
```
