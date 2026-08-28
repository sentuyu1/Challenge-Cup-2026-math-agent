# 微分几何：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是面向数学智能体的说明型提示资料，包含可摘取的 SymPy 片段，不是可直接运行的完整曲线/曲面计算程序。

## 使用规则
- 先声明参数化、参数区间、度量和单位法向方向；所有曲率符号都依赖这些选择。
- 三角形、圆、相切、角平分线等初等几何转非基础及进阶课程；圆周上的受限 Laplacian 按数学分析处理。
- 推导后检查正则性、坐标变换不变性和法向翻转带来的符号变化。

## 知识点 1：曲线与 Frenet 标架
- 弧长为 $\int\|r'(t)\|dt$，先排除非正则点或分段处理。
- 平面/空间曲率使用参数化相应公式；Frenet 标架需单位速度或正确换算。
- 挠率只对足够正则且曲率非零的空间曲线直接定义，平面曲线挠率为零。

## 知识点 2：曲面基本形式
- 对 $r(u,v)$，先计算 $E,F,G$ 和正则性 $r_u\times r_v\ne0$。
- 第二基本形式系数 $L,M,N$ 与所选法向相关；换法向会使它们及平均/法曲率变号。
- 法曲率为 $\mathrm{II}(w,w)/\mathrm{I}(w,w)$，主曲率来自形算子或特征方程。

## 知识点 3：内蕴与整体几何
- Gaussian 曲率为主曲率乘积，法向翻转不变；平均曲率会变号。
- 测地线要说明所用联络/Christoffel 符号或变分条件；Gauss--Bonnet 须保留边界、定向和角缺项。
- 圆柱/球面等经典曲面需按题目法向约定报告符号，不能只给绝对值。

## Python 代码片段：曲线弧长、曲率与挠率
```python
import sympy as sp

t = sp.symbols("t", real=True)
r = sp.Matrix(curve_components)  # 题面参数化 r(t)
r1, r2, r3 = r.diff(t), r.diff(t, 2), r.diff(t, 3)
speed = sp.sqrt(sp.simplify(r1.dot(r1)))
arc_length = sp.integrate(speed, (t, parameter_start, parameter_end))
curvature = sp.simplify(r1.cross(r2).norm() / speed ** 3)
torsion = sp.simplify(sp.Matrix.hstack(r1, r2, r3).det() / r1.cross(r2).norm() ** 2)
```

## Python 代码片段：第一、第二基本形式
```python
import sympy as sp

u, v = sp.symbols("u v", real=True)
surface = sp.Matrix(surface_components)  # 题面参数化 r(u,v)
ru, rv = surface.diff(u), surface.diff(v)
normal = sp.simplify(ru.cross(rv) / ru.cross(rv).norm())
E, F, G = ru.dot(ru), ru.dot(rv), rv.dot(rv)
ruu, ruv, rvv = surface.diff(u, 2), surface.diff(u, v), surface.diff(v, 2)
L, M, N = ruu.dot(normal), ruv.dot(normal), rvv.dot(normal)
```

## Python 代码片段：法曲率与主曲率
```python
import sympy as sp

direction = sp.Matrix([du, dv])  # 题面指定的参数方向
first_form = sp.Matrix([[E, F], [F, G]])
second_form = sp.Matrix([[L, M], [M, N]])
normal_curvature = sp.simplify((direction.T * second_form * direction)[0] / (direction.T * first_form * direction)[0])
principal_equation = sp.factor((second_form - sp.symbols("k") * first_form).det())
```

## 输出契约
- 最终答案包含参数化、法向、基本形式/曲率公式、符号约定及所求量。
- 未给法向时说明两种符号可能或明确采用的约定，不无提示地固定符号。
- 代码计算前后都要说明所取法向；法向翻转会改变第二基本形式、平均曲率和法曲率的符号。

## 模块级验证代码（与微分几何 skill 的 20 个编号模块对应）

## Python 代码片段：模块1 曲线弧长
```python
import sympy as sp

t = sp.symbols("t", real=True)
r1 = curve.diff(t)
speed = sp.sqrt(sp.simplify(r1.dot(r1)))
arc_length = sp.integrate(speed, (t, start, end))
```

## Python 代码片段：模块2 平面曲线曲率
```python
import sympy as sp

t = sp.symbols("t", real=True)
velocity, acceleration = curve.diff(t), curve.diff(t, 2)
planar_curvature = sp.simplify(
    (velocity[0] * acceleration[1] - velocity[1] * acceleration[0])
    / sp.sqrt(velocity.dot(velocity)) ** 3
)
```

## Python 代码片段：模块3 Frenet 标架与单位切向量
```python
import sympy as sp

velocity = curve.diff(t)
unit_tangent = sp.simplify(velocity / sp.sqrt(velocity.dot(velocity)))
unit_normal = sp.simplify(unit_tangent.diff(t) / sp.sqrt(unit_tangent.diff(t).dot(unit_tangent.diff(t))))
```

## Python 代码片段：模块4 空间曲线曲率
```python
import sympy as sp

r1, r2 = curve.diff(t), curve.diff(t, 2)
space_curvature = sp.simplify(r1.cross(r2).norm() / r1.norm() ** 3)
```

## Python 代码片段：模块5 挠率
```python
import sympy as sp

r1, r2, r3 = curve.diff(t), curve.diff(t, 2), curve.diff(t, 3)
torsion = sp.simplify(sp.Matrix.hstack(r1, r2, r3).det() / r1.cross(r2).norm() ** 2)
```

## Python 代码片段：模块6 第一基本形式
```python
import sympy as sp

ru, rv = surface.diff(u), surface.diff(v)
first_form = sp.Matrix([[ru.dot(ru), ru.dot(rv)], [ru.dot(rv), rv.dot(rv)]])
regularity = sp.simplify(ru.cross(rv).dot(ru.cross(rv)))
```

## Python 代码片段：模块7 第二基本形式
```python
import sympy as sp

normal = sp.simplify(ru.cross(rv) / ru.cross(rv).norm())
second_form = sp.Matrix([[surface.diff(u, 2).dot(normal), surface.diff(u, v).dot(normal)],
                         [surface.diff(u, v).dot(normal), surface.diff(v, 2).dot(normal)]])
```

## Python 代码片段：模块8 法曲率
```python
import sympy as sp

direction = sp.Matrix([du, dv])
normal_curvature = sp.simplify((direction.T * second_form * direction)[0]
                               / (direction.T * first_form * direction)[0])
```

## Python 代码片段：模块9 高斯曲率
```python
import sympy as sp

gaussian_curvature = sp.simplify(second_form.det() / first_form.det())
principal_product_gap = sp.simplify(gaussian_curvature - principal_curvature_1 * principal_curvature_2)
```

## Python 代码片段：模块10 平均曲率与极小曲面
```python
import sympy as sp

mean_curvature = sp.simplify(sp.trace(first_form.inv() * second_form) / 2)
minimal_surface_gap = sp.simplify(mean_curvature)
```

## Python 代码片段：模块11 曲面面积
```python
import sympy as sp

area_element = sp.sqrt(sp.simplify(first_form.det()))
surface_area = sp.integrate(area_element, (u, u_left, u_right), (v, v_left, v_right))
```

## Python 代码片段：模块12 测地线与测地曲率
```python
import sympy as sp

geodesic_residual = sp.simplify(curve_second_derivative + christoffel_term)
geodesic_curvature = sp.simplify(acceleration.dot(surface_normal))
```

## Python 代码片段：模块13 主曲率
```python
import sympy as sp

k = sp.symbols("k")
principal_polynomial = sp.factor((second_form - k * first_form).det())
principal_curvatures = sp.solve(sp.Eq(principal_polynomial, 0), k)
```

## Python 代码片段：模块14 渐近线与双曲点
```python
import sympy as sp

asymptotic_condition = sp.simplify((direction.T * second_form * direction)[0])
hyperbolic_condition = gaussian_curvature < 0
```

## Python 代码片段：模块15 挠率与平面曲线判定
```python
import sympy as sp

torsion_gap = sp.simplify(torsion)
planarity_test = sp.simplify(sp.Matrix.hstack(curve.diff(t), curve.diff(t, 2),
                                              curve.diff(t, 3)).det())
```

## Python 代码片段：模块16 Frenet--Serret 公式
```python
import sympy as sp

frenet_tangent_gap = sp.simplify(unit_tangent.diff(t) - speed * curvature * unit_normal)
frenet_normal_gap = sp.simplify(unit_normal.diff(t) + speed * curvature * unit_tangent
                                 - speed * torsion * unit_binormal)
```

## Python 代码片段：模块17 可展曲面
```python
import sympy as sp

developable_gap = sp.simplify(gaussian_curvature)
normal_variation = sp.simplify(surface.diff(u).cross(surface.diff(v)).diff(v))
```

## Python 代码片段：模块18 等距对应
```python
import sympy as sp

metric_gap = sp.simplify(first_form_source - first_form_target.subs(parameter_map))
length_gap = sp.simplify(sp.integrate(source_speed, (t, start, end))
                          - sp.integrate(target_speed, (t, start, end)))
```

## Python 代码片段：模块19 Gauss--Bonnet 定理
```python
import sympy as sp

gauss_bonnet_residual = sp.simplify(
    sp.integrate(gaussian_curvature * area_element, (u, u_left, u_right), (v, v_left, v_right))
    + sp.integrate(geodesic_curvature, (t, boundary_start, boundary_end))
    + corner_angle_sum - 2 * sp.pi * euler_characteristic
)
```

## Python 代码片段：模块20 极小曲面判定
```python
import sympy as sp

minimal_equation = sp.simplify(mean_curvature)
area_first_variation = sp.simplify(first_variation)
```
