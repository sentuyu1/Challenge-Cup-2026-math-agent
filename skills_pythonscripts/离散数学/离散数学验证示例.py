# 离散数学：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是说明型提示资料，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整枚举器或搜索程序。

## 使用规则
- 先明确有限对象、状态、边界和等价关系；计数题必须说明是否有序、是否允许重复以及对称性如何处理。
- 本目录覆盖组合、图论、递推、生成函数、数论整除与组合博弈；纯欧氏几何转非基础及进阶课程，规划/调度转运筹学。
- 小规模枚举只能用于发现规律，最终结论必须给递推、不变量、双计数或构造证明。

## 知识点 1：命题逻辑、集合与布尔代数
- 使用真值表、等价变形、主析取/主合取范式时保持量词和否定范围。
- 集合题通过并、交、补和容斥核对；布尔式化简后可用代入边界值检查等价性。

## 知识点 2：组合计数
- 加法、乘法、排列组合和容斥原理的前提分别是互斥、分步独立、顺序及重复限制。
- 抽屉原理要指出抽屉和对象；递推计数写出初值与边界。
- Burnside/Polya 或对称计数必须说明群作用和不动点数。

## 知识点 3：递推与生成函数
- 线性递推的特征方程要结合初值确定常数；重根和共轭根分别处理。
- 生成函数中系数提取、收敛形式与形式幂级数运算不可混淆。

## 知识点 4：数论
- 扩展 Euclid 给出 $ax+by=\gcd(a,b)$；同余除法先核对逆元或互素条件。
- 中国剩余定理先检查模数互素性或兼容条件；整除、素数、取整和 Diophantine 方程逐项保留整数条件。

## 知识点 5：图论、关系与博弈
- 图论先规定简单图/多重图、有向性和顶点集；握手、Euler/Hamilton、树和着色结论要核对前提。
- 等价关系检查自反、对称、传递；偏序另需反对称。
- 组合博弈区分 P/N 态和终局规则，策略必须覆盖对手所有合法回应。

## 知识点 6：竞赛拓展专题
- 格点正六边形、直线覆盖、面积平分线和全等剖分题：写出坐标/仿射不变量、对称性和不重不漏依据。
- 共线角度、多面体可见性和凸性题：保留射线顺序、外法向和非退化条件，不能由示意图直接断言。
- 分拆共轭、拉丁方与组合设计题：检查大小守恒、行列排列和存在性上界。
- 赛程排程题：每对对象恰出现一次、每轮可行且总成本/停留约束全部满足；有明确优化目标时转运筹学。
- max-plus 闭包、平移不变全序和 rich 集题：先声明运算，再检查闭包、平移相容性和构造的双向条件。
- 判别式丢番图、大数除法与数位整除题：检查判别式为平方、回代原方程、位数/进位以及模 $11$ 交错和等必要条件。

## Python 代码片段：组合数、容斥与有限枚举
```python
from itertools import combinations
from math import comb

# n、k 和对象集合必须来自题面。
binomial_value = comb(n, k)
pair_subsets = list(combinations(objects, subset_size))

# 容斥项由题面事件族给出；只对有限且可枚举情形使用。
inclusion_exclusion_total = sum(
    (-1) ** (len(index_set) + 1) * intersection_size(index_set)
    for size in range(1, len(event_indices) + 1)
    for index_set in combinations(event_indices, size)
)
```

## Python 代码片段：递推、生成函数与系数提取
```python
import sympy as sp

n = sp.symbols("n", integer=True, nonnegative=True)
z = sp.symbols("z")
# recurrence、initial_values 或 generating_function 均由题面给出。
closed_form_candidates = sp.rsolve(recurrence, sp.Function("a")(n))
coefficient_n = sp.expand(generating_function.series(z, 0, target_index + 1).removeO()).coeff(z, target_index)
```

## Python 代码片段：扩展 Euclid 与中国剩余定理
```python
from math import gcd

def extended_gcd(a, b):
    if b == 0:
        return abs(a), 1 if a >= 0 else -1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1

g, u, v = extended_gcd(a, b)
bezout_check = a * u + b * v == g
# 同余求解前先检查 gcd(modulus_1, modulus_2) 与余数兼容性。
```

## Python 代码片段：图的邻接矩阵与度数核验
```python
import sympy as sp

A = sp.Matrix(adjacency_matrix)
degrees = [sum(A.row(i)) for i in range(A.rows)]
handshake_check = sum(degrees) == 2 * edge_count  # 仅适用于无向简单图
reachability_counts = [(A ** steps)[start, end] for steps in range(1, max_steps + 1)]
```

## 输出契约
- 计数给出状态空间、递推/双计数或不重不漏说明；数论给出模条件与整数解限制；博弈给出完整策略或不变量。
- 不用“显然”“程序试过”替代一般性证明。
- 代码仅用于核验题面给出的有限实例、递推初值或不变量；最终答案必须补足不重不漏或一般性证明。

## 模块级验证代码（与离散数学 skill 的 36 个编号专题对应）

## Python 代码片段：模块1 命题逻辑化简
```python
import sympy as sp

proposition = sp.sympify(proposition_expression)
logic_normal_form = sp.to_cnf(proposition, simplify=True)
logic_check = sp.simplify_logic(proposition, form="dnf")
```

## Python 代码片段：模块2 组合计数
```python
from math import comb, factorial

unordered_count = comb(total_items, choose_count)
ordered_count = factorial(total_items) // factorial(total_items - choose_count)
```

## Python 代码片段：模块3 集合运算与恒等式
```python
left_expression = (set_a | set_b) & set_c
right_expression = (set_a & set_c) | (set_b & set_c)
set_identity_gap = left_expression.symmetric_difference(right_expression)
```

## Python 代码片段：模块4 扩展欧几里得算法
```python
import sympy as sp

gcd_value, bezout_s, bezout_t = sp.gcdex(integer_a, integer_b)
bezout_gap = bezout_s * integer_a + bezout_t * integer_b - gcd_value
```

## Python 代码片段：模块5 齐次递推关系
```python
import sympy as sp

n = sp.symbols("n", integer=True, nonnegative=True)
characteristic = sp.Poly(recurrence_polynomial, sp.symbols("r"))
recurrence_solution = sp.rsolve(recurrence_equation, sequence(n), initial_values)
```

## Python 代码片段：模块6 容斥原理
```python
from itertools import combinations

union_count = sum((-1) ** (len(subsets) + 1) * intersection_count(subsets)
                  for size in range(1, len(families) + 1)
                  for subsets in combinations(families, size))
```

## Python 代码片段：模块7 中国剩余定理
```python
import sympy as sp

crt_solution, crt_modulus = sp.ntheory.modular.crt(moduli, residues)
congruence_residuals = [sp.rem(crt_solution - residue, modulus)
                        for modulus, residue in zip(moduli, residues)]
```

## Python 代码片段：模块8 布尔代数与卡诺图化简
```python
import sympy as sp

variables = sp.symbols("x0:%d" % variable_count)
boolean_expression = sp.And(*clauses)
minimal_expression = sp.simplify_logic(boolean_expression, force=True)
```

## Python 代码片段：模块9 图论基础
```python
import sympy as sp

A = sp.Matrix(adjacency_matrix)
degree_sequence = [sum(A.row(i)) for i in range(A.rows)]
handshake_gap = sum(degree_sequence) - 2 * edge_count
```

## Python 代码片段：模块10 生成函数与受限组合
```python
import sympy as sp

x = sp.symbols("x")
generating_function = sp.expand(sp.prod(1 / (1 - x ** part) for part in allowed_parts))
coefficient = generating_function.series(x, 0, target_degree + 1).removeO().coeff(x, target_degree)
```

## Python 代码片段：模块11 等价关系与商集
```python
relation_reflexive = all((value, value) in relation for value in domain)
relation_symmetric = all((b, a) in relation for a, b in relation)
relation_transitive = all((a, c) in relation for a, b in relation for b2, c in relation if b == b2)
equivalence_classes = {frozenset(b for a, b in relation if a == representative)
                       for representative in domain}
```

## Python 代码片段：模块12 组合恒等式
```python
from math import comb

vandermonde_gap = sum(comb(left, k) * comb(right, target - k) for k in range(target + 1)) - comb(left + right, target)
```

## Python 代码片段：模块13 非齐次递推关系
```python
import sympy as sp

n = sp.symbols("n", integer=True, nonnegative=True)
particular_solution = sp.rsolve(nonhomogeneous_recurrence, sequence(n))
recurrence_gap = sp.simplify(particular_solution.subs(n, n + 1)
                             - recurrence_rhs(particular_solution, n))
```

## Python 代码片段：模块14 数论整除性证明
```python
import sympy as sp

divisibility_remainder = sp.rem(numerator, divisor, domain=sp.ZZ)
gcd_factor = sp.factor(sp.gcd(numerator, divisor))
```

## Python 代码片段：模块15 Catalan 数
```python
from math import comb

catalan = comb(2 * n, n) // (n + 1)
catalan_recurrence_gap = catalan_next - sum(catalan_values[i] * catalan_values[n - 1 - i]
                                           for i in range(n))
```

## Python 代码片段：模块16 偏序集与格
```python
lower_bounds = {item for item in poset if all(item <= value for value in subset)}
upper_bounds = {item for item in poset if all(value <= item for value in subset)}
meet_candidates = lower_bounds & maximal_elements(lower_bounds)
join_candidates = upper_bounds & minimal_elements(upper_bounds)
```

## Python 代码片段：模块17 鸽巢原理
```python
from collections import Counter

occupancies = Counter(objects_to_boxes)
pigeonhole_witness = max(occupancies.values())
```

## Python 代码片段：模块18 通用解题方法论
```python
required_invariants = (state_space, invariant, boundary_condition, target_statement)
missing_invariants = [name for name, value in zip(invariant_names, required_invariants) if value is None]
```

## Python 代码片段：模块19 竞赛博弈
```python
def mex(values):
    candidate = 0
    while candidate in values:
        candidate += 1
    return candidate

grundy = {state: mex({grundy[next_state] for next_state in moves(state)}) for state in states}
```

## Python 代码片段：模块20 双色点集直线分离
```python
import sympy as sp

def orientation(a, b, c):
    return sp.Matrix([[a[0], a[1], 1], [b[0], b[1], 1], [c[0], c[1], 1]]).det()

separation_signs = [sp.sign(orientation(point_a, point_b, point)) for point in points]
```

## Python 代码片段：模块21 Lempel--Ziv 字典编码
```python
dictionary = {}
phrases = []
cursor = 0
while cursor < len(sequence):
    phrase = longest_known_prefix(sequence[cursor:], dictionary)
    phrases.append(phrase)
    dictionary[phrase] = len(dictionary) + 1
    cursor += len(phrase)
```

## Python 代码片段：模块22 组合几何格点计数
```python
import sympy as sp

boundary_points = [(i, j) for i in range(width + 1) for j in range(height + 1)]
primitive_edges = [sp.gcd(abs(dx), abs(dy)) == 1 for dx, dy in edge_vectors]
```

## Python 代码片段：模块23 平面点集直线覆盖极值
```python
from collections import Counter

line_counts = Counter(line_identifier(pair) for pair in point_pairs)
max_collinear = max(line_counts.values(), default=0)
```

## Python 代码片段：模块24 凸多边形面积平分线
```python
import sympy as sp

oriented_area = sp.Matrix([[point[0], point[1], 1] for point in polygon]).det() / 2
area_balance_gap = sp.simplify(left_subpolygon_area - right_subpolygon_area)
```

## Python 代码片段：模块25 全等三角剖分与外切多边形
```python
import sympy as sp

side_length_gaps = [sp.simplify(length_a - length_b) for length_a, length_b in corresponding_sides]
triangle_area = sp.simplify(base * height / 2)
```

## Python 代码片段：模块26 共线构型角度倍数关系
```python
import sympy as sp

angle_residual = sp.simplify(angle_expression - multiple * base_angle)
root_count = len(sp.solve(sp.Eq(angle_residual, 0), angle_variable))
```

## Python 代码片段：模块27 凸多面体面可见性
```python
import sympy as sp

face_normal = edge_1.cross(edge_2)
visibility_sign = sp.sign(face_normal.dot(view_direction))
separating_gap = sp.simplify(face_normal.dot(point - face_origin))
```

## Python 代码片段：模块28 多项式恒等式与频数向量互逆
```python
import sympy as sp

x = sp.symbols("x")
frequency_polynomial = sp.expand(sum(count * x ** degree for degree, count in frequencies.items()))
coefficient_vector = [frequency_polynomial.coeff(x, degree) for degree in degrees]
```

## Python 代码片段：模块29 拉丁方与组合设计
```python
row_valid = all(len(set(row)) == order for row in latin_square)
column_valid = all(len({latin_square[i][j] for i in range(order)}) == order
                   for j in range(order))
```

## Python 代码片段：模块30 排程优化与赛程安排
```python
from collections import Counter

resource_load = Counter(task_resource for task_resource in assignment)
capacity_feasible = all(resource_load[r] <= capacity[r] for r in capacity)
total_schedule_cost = sum(task_cost[task] for task in assignment)
```

## Python 代码片段：模块31 max-plus 半环与闭包
```python
import numpy as np

max_plus_product = np.max(weight_matrix[:, :, None] + weight_matrix[None, :, :], axis=1)
max_plus_closure = np.maximum.reduce([np.linalg.matrix_power(max_plus_product, k)
                                      for k in range(1, path_bound + 1)])
```

## Python 代码片段：模块32 平移不变全序与秩函数
```python
rank_gap = rank_function(value + translation) - rank_function(value)
parity_check = rank_gap % 2
```

## Python 代码片段：模块33 多项式整数根封闭集
```python
import sympy as sp

x = sp.symbols("x")
integer_roots = [root for root in sp.polys.polytools.ground_roots(polynomial)
                 if root.is_Integer]
closure_residuals = [sp.factor(polynomial.subs(x, root)) for root in integer_roots]
```

## Python 代码片段：模块34 丢番图方程与判别式参数化
```python
import sympy as sp

discriminant = sp.factor(sp.discriminant(dio_polynomial, variable))
integer_parameter_candidates = [value for value in parameter_values
                                if sp.Integer(discriminant.subs(parameter, value)).is_square]
```

## Python 代码片段：模块35 大数除法的数字结构
```python
quotient, remainder = divmod(dividend, divisor)
division_identity_gap = dividend - (quotient * divisor + remainder)
```

## Python 代码片段：模块36 十进制数字操作与整除
```python
digits = [int(char) for char in str(integer_value)]
digit_sum = sum(digits)
base_ten_residual = integer_value % divisor
```

## Python 代码片段：模块37 小规模打表、周期外推与记忆化博弈搜索
```python
from functools import lru_cache

# rule_moves(state) 与 is_terminal(state) 按题面原始规则实现，禁止先验简化。
@lru_cache(maxsize=None)
def game_value(state, maximizing):
    if is_terminal(state):
        return terminal_score(state)
    children = [game_value(next_state, not maximizing)
                for next_state in rule_moves(state)]
    return max(children) if maximizing else min(children)

table = [exact_bruteforce(n) for n in range(1, 13)]
diffs = [table[i + 1] - table[i] for i in range(len(table) - 1)]
period_candidates = [m for m in range(1, 6)
                     if all(diffs[i] == diffs[i + m] for i in range(len(diffs) - m))]
# 归纳公式后必须用打表范围外的中等规模精确值复验，再外推题面规模。
formula_matches = all(closed_form(n) == table[n - 1] for n in range(1, 13))
```

## Python 代码片段：模块38 极值构造的上下界闭环与竞争构造对照
```python
from itertools import permutations

# 两个结构不同的构造必须独立实现；只验证单一构造的算术是循环论证。
value_greedy = objective(build_greedy_construction(n))
value_divide = objective(build_divide_and_conquer_construction(n))
best_constructive = min(value_greedy, value_divide)

# 小规模全空间精确最优，用于校准构造是否达到最优。
exact_small = min(objective(candidate) for candidate in enumerate_all_candidates(small_n))
construction_small = min(objective(build_greedy_construction(small_n)),
                         objective(build_divide_and_conquer_construction(small_n)))
calibration_gap = construction_small - exact_small
```

## Python 代码片段：模块39 全解枚举与例外解支
```python
# 截断版本上回溯枚举全部解支；对合方程 a = F(F(a)) 须同时收集不动点与 2-循环。
solutions = []

def backtrack(prefix):
    if violates_constraints(prefix):
        return
    if len(prefix) == truncation_length:
        solutions.append(tuple(prefix))
        return
    for value in candidate_values(prefix):
        backtrack(prefix + [value])

backtrack([])
fixed_points = [a for a in solutions if apply_map(a) == a]
two_cycles = [(a, apply_map(a)) for a in solutions
              if apply_map(a) != a and apply_map(apply_map(a)) == a]
solution_branches = {classify_branch(sol) for sol in solutions}
```
