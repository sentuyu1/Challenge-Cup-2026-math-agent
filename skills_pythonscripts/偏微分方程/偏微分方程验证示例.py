# 偏微分方程：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是数学智能体的验证说明，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整 PDE 求解或离散化程序。

## 使用规则
- 首先写出未知函数、自变量、区域、方程、初始/边界条件和正则性要求；这些条件是解的一部分。
- 题目核心为有限差分、有限元、截断误差或稳定性时转数值分析；纯抽象算子谱题转泛函分析。
- 求得表达式后检查 PDE 本身和每条初边条件，避免只验证内部方程。

## 知识点 1：一阶方程与特征线
- 线性或拟线性 PDE 用特征方程建立不变量；初始曲线必须是非特征的才通常给出局部唯一解。
- 参数化回代时检查 Jacobian 是否退化、多值解/交叉特征线是否出现。

## 知识点 2：二阶分类与调和函数
- 对 $Au_{xx}+2Bu_{xy}+Cu_{yy}$ 用 $B^2-AC$ 分类，并说明系数和区域。
- Laplace 方程解需检验调和性；调和函数可用最大值原理、均值性质和边界唯一性，但必须满足相应正则性。

## 知识点 3：波动、热与分离变量
- 无界一维波动方程用 d'Alembert 公式并核对初位移/初速度；有界区间根据边界条件选择正弦或余弦特征函数。
- 热方程的特征展开要说明系数由初值投影得到，且检查边界条件和时间衰减。
- Fourier 系列/Green 函数必须标明定义区间、边界类型和收敛意义。

## 知识点 4：能量法与形式伴随
- 能量估计保留积分区域、边界项和符号；能量守恒或衰减取决于边界条件。
- 形式伴随需经分部积分写清导数转移、系数转置/共轭和边界项，不能只改变符号。

## Python 代码片段：候选解的 PDE 与初边条件回代
```python
import sympy as sp

x, y, t = sp.symbols("x y t", real=True)
# candidate、operator、边界函数和区域均由题面给出。
pde_residual = sp.simplify(operator(candidate))
initial_gap = sp.simplify(candidate.subs(t, initial_time) - initial_profile)
left_boundary_gap = sp.simplify(candidate.subs(x, left_endpoint) - left_boundary)
right_boundary_gap = sp.simplify(candidate.subs(x, right_endpoint) - right_boundary)
```

## Python 代码片段：二阶 PDE 的类型判别
```python
import sympy as sp

# 标准形 A*u_xx + 2*B*u_xy + C*u_yy + ... 中的系数从题面读取。
discriminant = sp.simplify(B ** 2 - A * C)
classification_conditions = {
    "elliptic": sp.Lt(discriminant, 0),
    "parabolic": sp.Eq(discriminant, 0),
    "hyperbolic": sp.Gt(discriminant, 0),
}
# 含参数时结合题面参数域判断哪个条件成立。
```

## Python 代码片段：形式伴随的分部积分辅助
```python
import sympy as sp

x = sp.symbols("x", real=True)
u = sp.Function("u")(x)
v = sp.Function("v")(x)
# L_u、candidate_adjoint_v、boundary_term 由分部积分推导，积分端点来自题面。
lhs_pairing = sp.integrate(v * L_u, (x, left_endpoint, right_endpoint))
rhs_pairing = sp.integrate(candidate_adjoint_v * u, (x, left_endpoint, right_endpoint))
green_identity_gap = sp.simplify(lhs_pairing - rhs_pairing - boundary_term)
# gap 为 0 只核验推导；定义域与边界条件仍须单独说明。
```

## 输出契约
- 最终答案同时给出方程满足性、区域、初边条件和必要的正则性/唯一性依据。
- 未给边界或初始资料时，说明只能给通解族或表示式，不能虚构唯一解。
- 代码只辅助回代和符号整理；特征线非退化、边界正则性和唯一性仍须根据题面写出。

## 模块级验证代码（与偏微分方程 skill 的 19 个编号模块对应）

## Python 代码片段：模块1 一阶线性 PDE 特征线
```python
import sympy as sp

x, y, t = sp.symbols("x y t", real=True)
characteristic_gap = sp.simplify(sp.diff(x_characteristic, t) - coefficient_a)
solution_gap = sp.simplify(sp.diff(candidate, t) + coefficient_a * sp.diff(candidate, x) - source)
```

## Python 代码片段：模块2 一阶拟线性 PDE 特征线
```python
import sympy as sp

characteristic_system = (sp.Eq(sp.diff(x_curve, t), a_field),
                         sp.Eq(sp.diff(y_curve, t), b_field),
                         sp.Eq(sp.diff(u_curve, t), source_field))
invariant_gap = sp.simplify(invariant.subs({x: x_curve, y: y_curve}).diff(t))
```

## Python 代码片段：模块3 二阶 PDE 分类判别
```python
import sympy as sp

discriminant = sp.simplify(B ** 2 - A * C)
classification = sp.Piecewise(("elliptic", discriminant < 0),
                              ("parabolic", sp.Eq(discriminant, 0)),
                              ("hyperbolic", discriminant > 0))
```

## Python 代码片段：模块4 调和函数与拉普拉斯方程
```python
import sympy as sp

laplacian = sp.simplify(sp.diff(candidate, x, 2) + sp.diff(candidate, y, 2))
mean_value_gap = sp.simplify(boundary_average - candidate.subs({x: center_x, y: center_y}))
```

## Python 代码片段：模块5 波动方程行波法与分离变量
```python
import sympy as sp

x, t = sp.symbols("x t", real=True)
wave_residual = sp.simplify(sp.diff(candidate, t, 2) - speed ** 2 * sp.diff(candidate, x, 2))
initial_displacement_gap = sp.simplify(candidate.subs(t, 0) - initial_profile)
```

## Python 代码片段：模块6 热传导方程分离变量
```python
import sympy as sp

heat_residual = sp.simplify(sp.diff(candidate, t) - diffusivity * sp.diff(candidate, x, 2))
left_gap = sp.simplify(candidate.subs(x, left_endpoint))
right_gap = sp.simplify(candidate.subs(x, right_endpoint))
```

## Python 代码片段：模块7 傅里叶变换法
```python
import sympy as sp

x, omega = sp.symbols("x omega", real=True)
transform = sp.integrate(initial_profile * sp.exp(-sp.I * omega * x), (x, -sp.oo, sp.oo))
transform_residual = sp.simplify(sp.I * omega * transform - transformed_derivative)
```

## Python 代码片段：模块8 拉普拉斯方程圆域与极坐标
```python
import sympy as sp

r, theta = sp.symbols("r theta", positive=True, real=True)
polar_laplacian = sp.simplify(sp.diff(candidate, r, 2) + sp.diff(candidate, r) / r
                              + sp.diff(candidate, theta, 2) / r ** 2)
```

## Python 代码片段：模块9 非齐次边界与稳态分析
```python
import sympy as sp

steady_residual = sp.simplify(sp.diff(steady_solution, x, 2) + forcing)
boundary_gaps = (sp.simplify(steady_solution.subs(x, left)),
                 sp.simplify(steady_solution.subs(x, right)))
```

## Python 代码片段：模块10 半无界问题反射法
```python
import sympy as sp

reflected = initial_profile(-x)
odd_extension_gap = sp.simplify(extended_profile.subs(x, -x) + extended_profile)
boundary_value = sp.simplify(candidate.subs(x, boundary))
```

## Python 代码片段：模块11 非齐次方程特征展开法
```python
import sympy as sp

mode_coefficient = sp.integrate(forcing * eigenfunction, (x, left, right))
mode_equation_gap = sp.simplify(sp.diff(mode_amplitude, t) + eigenvalue * mode_amplitude
                                - mode_coefficient)
```

## Python 代码片段：模块12 能量方法与唯一性
```python
import sympy as sp

energy = sp.integrate(sp.diff(candidate, t) ** 2 + speed ** 2 * sp.diff(candidate, x) ** 2,
                      (x, left, right))
energy_derivative = sp.simplify(sp.diff(energy, t))
```

## Python 代码片段：模块13 极值原理
```python
import sympy as sp

interior_laplacian = sp.simplify(sp.diff(candidate, x, 2) + sp.diff(candidate, y, 2))
boundary_values = [candidate.subs(point) for point in boundary_points]
maximum_bound = max(boundary_values)
```

## Python 代码片段：模块14 格林函数与对称性
```python
import sympy as sp

green_residual = sp.simplify(operator(green_function) - delta_source)
symmetry_gap = sp.simplify(green_function(x, xi) - green_function(xi, x))
```

## Python 代码片段：模块15 依赖域与传播特征
```python
import sympy as sp

cone_gap = sp.simplify((x - source_x) ** 2 - speed ** 2 * (t - source_t) ** 2)
domain_check = sp.simplify(cone_gap.subs({x: observation_x, t: observation_t}))
```

## Python 代码片段：模块16 稳定性估计
```python
import sympy as sp

norm_initial = sp.integrate(initial_profile ** 2, (x, left, right))
norm_solution = sp.integrate(candidate ** 2, (x, left, right))
stability_gap = sp.simplify(norm_solution - stability_constant * norm_initial)
```

## Python 代码片段：模块17 通用解题方法论
```python
required_fields = (unknown_function, domain, equation, initial_data, boundary_data)
missing_fields = [name for name, value in zip(field_names, required_fields) if value is None]
```

## Python 代码片段：模块18 习题解题思路索引表
```python
from collections import Counter

topic_counts = Counter(topic_labels)
index_consistency = all(index in known_indices for index in requested_indices)
```

## Python 代码片段：模块19 竞赛拓展——散度型算子形式伴随
```python
import sympy as sp

formal_pairing = sp.integrate(test_function * divergence_operator(candidate), (x, left, right))
adjoint_pairing = sp.integrate(formal_adjoint(test_function) * candidate, (x, left, right))
green_gap = sp.simplify(formal_pairing - adjoint_pairing - boundary_term)
```
