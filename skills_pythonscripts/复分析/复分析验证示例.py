# 复分析：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是供数学智能体参考的说明文本，包含可摘取的 SymPy 代码片段，不是可直接运行的完整程序。

## 使用规则
- 先标注复平面区域、奇点、路径方向和绕数；所有积分定理都依赖相应的解析性或区域条件。
- 级数、留数和保形映射的结论必须说明收敛环域、孤立奇点类型或映射定义域。
- 实变量 Fourier 变换转数学分析；无复解析条件的整数范数或同余问题转离散数学。

## 知识点 1：复数与解析性
- 用极坐标和 de Moivre 公式处理幂与根，注意辐角多值性。
- $u+iv$ 全纯需满足 Cauchy--Riemann 方程并有适当可微性；调和性是必要条件之一，不是任意函数全纯的充分替代。

## 知识点 2：Cauchy 积分理论
- Cauchy 积分定理和积分公式要求函数在路径及其内部的适当区域解析。
- 高阶导数公式、Morera 定理和最大模原理的使用都要写清区域连通性和边界条件。

## 知识点 3：Laurent 展开与留数
- 先确定展开中心和收敛环域，再选用几何级数、部分分式或 Taylor 展开。
- 孤立奇点区分可去、极点和本性奇点；极点阶数与留数计算方法需一致。
- 留数定理中的积分是 $2\pi i$ 乘以路径内留数和，并计入绕数和方向。

## 知识点 4：保形映射与零点理论
- Möbius 变换由三个点确定，处理圆/直线像时保留退化情形。
- 辐角原理、Rouche 定理和零点计数必须在指定闭曲线及其内部满足无零/严格不等式条件。

## Python 代码片段：Cauchy--Riemann 与调和性
```python
import sympy as sp

x, y = sp.symbols("x y", real=True)
z = x + sp.I * y
# u、v 从题面函数 f(z)=u+iv 中拆出。
cauchy_riemann = (sp.simplify(sp.diff(u, x) - sp.diff(v, y)),
                  sp.simplify(sp.diff(u, y) + sp.diff(v, x)))
laplacian_u = sp.simplify(sp.diff(u, x, 2) + sp.diff(u, y, 2))
```

## Python 代码片段：Laurent 展开与留数
```python
import sympy as sp

z = sp.symbols("z")
# f、z0 和展开阶数由题面提供；展开环域需在文字中另行判断。
laurent = sp.series(f, z, z0, expansion_order)
residue_at_z0 = sp.residue(f, z, z0)
pole_order_check = sp.limit((z - z0) ** pole_order * f, z, z0)
```

## Python 代码片段：围道积分的留数和
```python
import sympy as sp

# singularities_inside 必须先按题面围道和方向人工确认。
residue_sum = sp.simplify(sum(sp.residue(f, z, point) for point in singularities_inside))
contour_integral = sp.simplify(2 * sp.pi * sp.I * winding_number * residue_sum)
```

## 输出契约
- 答案应包含解析域、路径方向、奇点或收敛环域、所用定理和最终值。
- 无法确认路径是否绕过奇点时，不直接套用 Cauchy 或留数定理。
- 代码不会判断奇点是否位于围道内部；先完成区域和定向分析，再使用相应片段。

## 模块级验证代码（与复分析 skill 的 9 个模块对应）

## Python 代码片段：模块1 复数运算与 de Moivre 公式
```python
import sympy as sp

r, theta, n = sp.symbols("r theta n", positive=True, real=True)
z = r * (sp.cos(theta) + sp.I * sp.sin(theta))
power_form = sp.expand_complex(z ** n)
modulus_check = sp.simplify(sp.Abs(z ** n) - r ** n)
```

## Python 代码片段：模块2 解析函数与 Cauchy--Riemann 方程
```python
import sympy as sp

x, y = sp.symbols("x y", real=True)
# u、v 是题面给出的实部和虚部。
cr_gap = (sp.simplify(sp.diff(u, x) - sp.diff(v, y)),
          sp.simplify(sp.diff(u, y) + sp.diff(v, x)))
harmonic_gap = sp.simplify(sp.diff(u, x, 2) + sp.diff(u, y, 2))
```

## Python 代码片段：模块3 Cauchy 积分理论
```python
import sympy as sp

z = sp.symbols("z")
# f、center、radius 由题面给出，且文字中先确认圆盘内无奇点。
cauchy_value = sp.simplify(2 * sp.pi * sp.I * sp.residue(f / (z - center), z, center))
formula_value = sp.simplify(2 * sp.pi * sp.I * f.subs(z, center))
```

## Python 代码片段：模块4 级数展开
```python
import sympy as sp

z, center = sp.symbols("z center")
series_data = sp.series(f, z, center, order)
coefficient = sp.expand(series_data.removeO()).coeff(z - center, coefficient_index)
```

## Python 代码片段：模块5 留数理论
```python
import sympy as sp

z = sp.symbols("z")
residue = sp.simplify(sp.residue(f, z, singular_point))
principal_part = sp.series(f, z, singular_point, pole_order + 1).removeO()
```

## Python 代码片段：模块6 围道积分与实积分计算
```python
import sympy as sp

residue_total = sp.simplify(sum(
    winding.get(point, 0) * sp.residue(f, z, point)
    for point in singularities
))
contour_value = sp.simplify(2 * sp.pi * sp.I * residue_total)
```

## Python 代码片段：模块7 保形映射
```python
import sympy as sp

z = sp.symbols("z")
mobius = (a * z + b) / (c * z + d)
determinant = sp.simplify(a * d - b * c)
derivative = sp.simplify(sp.diff(mobius, z))
```

## Python 代码片段：模块8 零点与极点理论
```python
import sympy as sp

z = sp.symbols("z")
zero_leading = sp.limit(f / (z - zero) ** zero_order, z, zero)
pole_leading = sp.limit((z - pole) ** pole_order * f, z, pole)
```

## Python 代码片段：模块9 经典定理（辐角/Rouche）
```python
import sympy as sp

t = sp.symbols("t", real=True)
boundary_values = [sp.simplify(f.subs(z, gamma(t))) for t in parameter_grid]
minimum_gap = min(abs(complex(value)) for value in boundary_values)
# 该有限采样只辅助核对题面给出的严格边界不等式，不能替代证明。
```

## Python 代码片段：竞赛拓展——虚二次域范数方程
```python
import sympy as sp

x, y, D, target = sp.symbols("x y D target", integer=True)
norm_expression = sp.expand(x ** 2 + D * y ** 2)
norm_residual = sp.factor(norm_expression - target)
```
