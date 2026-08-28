# 非基础及进阶课程：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是竞赛数学的说明型提示资料，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整搜索程序或答案库。

## 使用规则
- 只用于欧氏/凸/射影竞赛几何，以及没有更专门课程目录的构造、反例、数论函数方程和连续策略题。
- 构造题同时验证可行性与最优性：给出构造、下界或上界，以及所有非退化、凸性、相切和顺序条件。
- 题目若明确是矩阵、群环域、PDE、数值离散、曲率/测地线，应转对应专科手册。

## 知识点 1：竞赛几何
- 面对三角形、圆、角平分线、外心/内心/垂心、根轴或极点极线，优先寻找共圆、相似、幂、反演和射影不变量。
- 坐标化前先说明坐标选择不丢失一般性；解析结论要回译为几何条件。
- 凸多边形和面积题应检查顶点顺序、对角线交点和面积是否为有向面积。

## 知识点 2：组合构造与极值
- 覆盖、路径、棋盘和铺砖题先给状态空间和不变量，再分别给可行构造与不可行下界。
- 计数时处理对称性、重复计数和边界状态；不能把小规模试验当作一般证明。

## 知识点 3：数论与函数方程
- 整除函数或多项式函数方程从代入特殊值、因式分解、同余和增长性开始；每次除法都保留零值情形。
- 用 Vieta、判别式或不变量时明确参数范围和实根/整数根条件。

## 知识点 4：策略与博弈
- 连续策略题先定义状态、行动集合、胜负条件与阈值；分别构造双方策略来证明临界值两侧结论。
- 离散 P/N 态或纯组合博弈转离散数学；此处只处理综合竞赛型策略构造。

## Python 代码片段：坐标几何与面积不变量
```python
import sympy as sp

def oriented_area(point_a, point_b, point_c):
    matrix = sp.Matrix([
        [point_a[0], point_a[1], 1],
        [point_b[0], point_b[1], 1],
        [point_c[0], point_c[1], 1],
    ])
    return sp.simplify(matrix.det() / 2)

# 点坐标必须由题面构造；比较面积前核对顶点顺序和凸性。
```

## Python 代码片段：整数构造的整除与回代
```python
import sympy as sp

# candidate 和 predicate 由推导得到；仅枚举题面给出的有限范围。
def validate_candidate(candidate, predicate):
    return bool(predicate(candidate))

factor_check = sp.factor(candidate_expression - target_expression)
divisibility_check = sp.rem(numerator, denominator, domain=sp.ZZ) == 0
```

## Python 代码片段：有限状态策略的反例搜索
```python
from itertools import product

# 只在题目状态空间确实有限且边界已知时使用；不能代替一般策略证明。
counterexample = next(
    (state for state in product(*state_components) if not invariant(state)),
    None,
)
if counterexample is not None:
    raise ValueError(f"候选策略在状态 {counterexample} 失效")
```

## 输出契约
- 结论必须给出构造或策略、双侧界/反例、以及题目要求的全部参数或分类。
- 不得把示意图、数值试验或未证明的对称性当作最终证明。
- 代码负责核对构造与反例，文字部分仍须给出一般性上/下界或策略证明。

## 模块级验证代码（与非基础及进阶课程 skill 的 10 个主模块对应）

## Python 代码片段：模块1 竞赛数论与整除函数
```python
import sympy as sp

gcd_check = sp.gcd(integer_a, integer_b)
divisibility_residual = sp.rem(candidate_expression, divisor_expression, domain=sp.ZZ)
```

## Python 代码片段：模块2 竞赛组合与未知障碍路径
```python
from itertools import product

states = list(product(range(rows), range(columns)))
reachable = {state for state in states if state not in blocked_states}
path_count = sum(path_counter(state) for state in reachable)
```

## Python 代码片段：模块3 竞赛函数方程的结构审计
```python
import sympy as sp

x, y = sp.symbols("x y")
substitution_gap = sp.factor(function_equation.subs({x: special_x, y: special_y}))
candidate_gap = sp.factor(candidate_function(x) - target_function(x))
```

## Python 代码片段：模块4 连续策略博弈
```python
import sympy as sp

threshold_gap = sp.simplify(strategy_value - critical_value)
lower_bound_gap = sp.simplify(opponent_payoff - lower_bound)
upper_bound_gap = sp.simplify(upper_bound - player_payoff)
```

## Python 代码片段：模块5 验证知识提示与回归索引
```python
required_fields = (problem_statement, candidate_answer, claimed_bound)
missing_fields = [name for name, value in zip(field_names, required_fields) if value is None]
```

## Python 代码片段：模块6 复分析兼容提示
```python
import sympy as sp

z = sp.symbols("z")
compatibility_residue = sp.residue(complex_expression, z, singular_point)
```

## Python 代码片段：模块7 测度积分兼容提示
```python
import sympy as sp

absolute_integral = sp.integrate(sp.Abs(integrand), (x, lower, upper))
integrability_check = sp.limit(absolute_integral, upper, sp.oo)
```

## Python 代码片段：模块8 综合几何构造
```python
import sympy as sp

area = sp.Matrix([[point[0], point[1], 1] for point in triangle]).det() / 2
distance_constraints = [sp.simplify(distance(a, b) - required_length)
                        for a, b, required_length in constraints]
```

## Python 代码片段：模块9 综合代数技巧
```python
import sympy as sp

x = sp.symbols("x")
polynomial_residual = sp.factor(polynomial.subs(x, candidate_root))
discriminant = sp.discriminant(polynomial, x)
```

## Python 代码片段：模块10 平面几何核心定理
```python
import sympy as sp

oriented_area = sp.Matrix([[p[0], p[1], 1] for p in points]).det() / 2
circle_power_gap = sp.factor(distance(point, center) ** 2 - radius ** 2)
```
