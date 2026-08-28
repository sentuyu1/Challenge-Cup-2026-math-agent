# 数值分析：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是给数学智能体的验证知识提示，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整数值计算程序。

## 使用规则
- 近似问题必须保留题面给定的节点、步长、初值、范数、停止准则和精度要求；不得自造数据或网格。
- 最终值除近似数外，按题意报告公式、误差阶、残差/条件数或稳定区间，并尽量以独立高精度计算核验。
- PDE 解析理论转偏微分方程；回归推断转线性回归或统计推断。

## 知识点 1：误差与条件数
- 区分绝对误差、相对误差、截断误差和舍入误差；有效数字与相对误差的关系要说明前提。
- 条件数依赖所选范数，病态性是问题性质，稳定性是算法性质，二者不可混同。

## 知识点 2：插值、数值微分与积分
- Lagrange/Newton 插值要列节点和插值余项；重复节点对应 Hermite 情形。
- 中点、梯形、Simpson、Romberg 公式要给步长、节点、权重和复化求和式。
- 差分公式的阶数来自 Taylor 展开；数值微分同时报告近似值、精确/参考值和误差。

## 知识点 3：非线性方程与迭代
- 二分法依赖变号区间；Newton 法写出迭代式、初值和导数非零条件。
- 固定点迭代用 $|\varphi'|<1$ 等收敛条件；停止准则应与题设容差一致。

## 知识点 4：线性系统与常微分方程数值法
- Gauss 消元、LU/QR 分解需检查主元、奇异性和残差；迭代法说明收敛判据。
- Euler、改进 Euler、Runge--Kutta 必须列明步长、每一步更新和全局/局部截断误差阶。
- 稳定性区间不能从少量数值试验推断，应由放大因子或理论条件给出。

## 知识点 5：PDE 离散化
- 有限差分、有限元、有限体积题分别说明网格、边界离散、截断误差和稳定性/一致性；不要把解析 PDE 解法混进数值结论。

## Python 代码片段：插值多项式与余项核验
```python
import sympy as sp

x = sp.symbols("x")
# nodes 与 values 必须逐项来自题面。
interpolant = sp.interpolate(list(zip(nodes, values)), x)
node_gaps = [sp.simplify(interpolant.subs(x, node) - value) for node, value in zip(nodes, values)]
# 若题面给出高阶导数界，才可据此代入插值余项公式。
```

## Python 代码片段：复化求积与高精度交叉检查
```python
import sympy as sp

x = sp.symbols("x", real=True)
# integrand、a、b、subintervals 由题面给出。
step = sp.simplify((b - a) / subintervals)
grid = [a + index * step for index in range(subintervals + 1)]
trapezoid = step * (integrand.subs(x, grid[0]) / 2 + sum(integrand.subs(x, point) for point in grid[1:-1]) + integrand.subs(x, grid[-1]) / 2)
reference_value = sp.N(sp.integrate(integrand, (x, a, b)), precision)
absolute_error = sp.Abs(sp.N(trapezoid, precision) - reference_value)
```

## Python 代码片段：Newton 迭代与残差
```python
import sympy as sp

x = sp.symbols("x", real=True)
# equation、initial_guess、iterations 和 tolerance 必须来自题面。
iterate = initial_guess
for _ in range(iterations):
    derivative = sp.diff(equation, x).subs(x, iterate)
    if derivative == 0:
        raise ZeroDivisionError("Newton 迭代遇到零导数")
    iterate = sp.N(iterate - equation.subs(x, iterate) / derivative, precision)
residual = sp.N(equation.subs(x, iterate), precision)
```

## Python 代码片段：线性系统残差与条件数
```python
import numpy as np

# matrix_a 与 vector_b 由题面给出；范数类型应与题意一致。
A = np.array(matrix_a, dtype=float)
b = np.array(vector_b, dtype=float)
solution = np.linalg.solve(A, b)
residual_norm = np.linalg.norm(A @ solution - b, ord=norm_order)
condition_number = np.linalg.cond(A, p=norm_order)
```

## 输出契约
- 最终答案保留所有指定中间节点、公式名、求和/迭代式、误差与结论。
- 当题目未给足数值参数时，给出符号算法或说明缺失字段，不随意选取步长。
- 代码片段必须同时保留节点、步长、停止条件、精度和误差表达式，不能只打印近似结果。

## 模块级验证代码（与数值分析 skill 的 11 个主模块对应）

## Python 代码片段：模块1 误差分析
```python
import sympy as sp

absolute_error = sp.simplify(approximation - exact_value)
relative_error = sp.simplify(absolute_error / exact_value)
order_estimate = sp.log(abs(error_h / error_h2)) / sp.log(abs(h / h2))
```

## Python 代码片段：模块2 插值法
```python
import sympy as sp

x = sp.symbols("x")
interpolant = sp.interpolate(list(zip(nodes, values)), x)
interpolation_residual = [sp.simplify(interpolant.subs(x, node) - value)
                          for node, value in zip(nodes, values)]
```

## Python 代码片段：模块3 数值积分
```python
import numpy as np

trap_value = np.trapz(function_values, nodes)
simpson_value = scipy_integrate.simpson(function_values, x=nodes)
quadrature_error = simpson_value - reference_value
```

## Python 代码片段：模块4 方程求根
```python
import sympy as sp

root = sp.nsolve(equation, initial_guess)
root_residual = sp.simplify(equation.subs(variable, root))
```

## Python 代码片段：模块5 线性方程组直接法
```python
import numpy as np

solution = np.linalg.solve(matrix_a, vector_b)
direct_residual = np.asarray(matrix_a) @ solution - np.asarray(vector_b)
```

## Python 代码片段：模块6 线性方程组迭代法
```python
import numpy as np

iterate = initial_vector.copy()
for _ in range(max_iterations):
    next_iterate = iteration_matrix @ iterate + iteration_offset
    if np.linalg.norm(next_iterate - iterate, ord=np.inf) <= tolerance:
        break
    iterate = next_iterate
```

## Python 代码片段：模块7 最小二乘拟合
```python
import numpy as np

design = np.asarray(design_matrix, dtype=float)
response = np.asarray(response_vector, dtype=float)
beta_hat, *_ = np.linalg.lstsq(design, response, rcond=None)
sse = np.sum((response - design @ beta_hat) ** 2)
```

## Python 代码片段：模块8 数值微分
```python
import sympy as sp

x, h = sp.symbols("x h", real=True)
central_difference = sp.simplify((function.subs(x, x0 + h) - function.subs(x, x0 - h)) / (2 * h))
truncation_order = sp.series(central_difference - sp.diff(function, x).subs(x, x0), h, 0, 4)
```

## Python 代码片段：模块9 矩阵范数与条件数
```python
import numpy as np

matrix_norm = np.linalg.norm(matrix_a, ord=norm_order)
inverse_norm = np.linalg.norm(np.linalg.inv(matrix_a), ord=norm_order)
condition_number = matrix_norm * inverse_norm
```

## Python 代码片段：模块10 数值稳定性
```python
import numpy as np

forward_error = np.linalg.norm(computed - exact, ord=np.inf)
backward_error = np.linalg.norm(np.asarray(matrix_a) @ computed - vector_b, ord=np.inf)
stability_ratio = forward_error / max(backward_error, np.finfo(float).eps)
```

## Python 代码片段：模块11 常微分方程数值解
```python
import numpy as np

next_state = state + step * rhs(time, state)
euler_residual = next_state - state - step * rhs(time, state)
```

## Python 代码片段：竞赛拓展——PDE 数值离散化
```python
import numpy as np

laplacian_stencil = (grid[2:, 1:-1] - 2 * grid[1:-1, 1:-1] + grid[:-2, 1:-1]) / dx ** 2
discrete_residual = laplacian_stencil - source_grid[1:-1, 1:-1]
```
