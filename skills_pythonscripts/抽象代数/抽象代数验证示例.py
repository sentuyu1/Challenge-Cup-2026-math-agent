# 抽象代数：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是用于提示数学智能体的知识点说明，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整程序或枚举器。

## 使用规则
- 先写清集合、运算、单位元和系数域；“看起来像群/环”不能替代封闭性、结合性、单位元和逆元的逐项核对。
- 结构题要区分对象、子对象、同态和同构；每个结论给出所依赖的定理及其适用前提。
- 有限分类题必须列全对象、给总数并说明互不同构性；不要用一个代表代替完整分类。

## 知识点 1：群、子群、陪集与同态
- 子群判别可用非空且对 $ab^{-1}$ 封闭；Lagrange 定理只用于有限群。
- 左右陪集、正规性和商群要分开判断；指数为 $2$ 的子群必正规。
- 同态题同时计算核和像，使用第一同构定理时写出满射/核条件。

## 知识点 2：群作用、Sylow 与有限 Abel 群
- 群作用用轨道--稳定子公式；共轭类和类方程注意中心元素。
- Sylow 子群数满足整除和同余条件，存在性不等于唯一性或正规性。
- 有限 Abel 群按素数幂分解和分拆分类；最终答案列出所有不变因子或初等因子形式。

## 知识点 3：环、理想与商环
- 先明确是否含幺；理想需对加法子群和双侧吸收性分别检查。
- 极大理想对应域商环，素理想对应整环商环；不要混用两者。
- 零因子、可逆元和幂零元的判断必须在给定环内进行。

## 知识点 4：多项式、域扩张与 Galois 理论
- 不可约性根据系数域选择 Eisenstein、模素数约化、根判别或次数论证。
- 扩张次数用塔式定理；分裂域、正规性、可分性和 Galois 群是不同结论。
- 有限域阶为素数幂，元素群结构和 Frobenius 自同构须和域阶一致。

## Python 代码片段：置换阶、核与像的有限核验
```python
from sympy.combinatorics import Permutation

# cycles 必须由题面置换给出；SymPy 的索引约定需与题面转换一致。
sigma = Permutation(cycles)
order_of_sigma = sigma.order()
inverse_sigma = sigma**-1

# 对有限映射 mapping，先由题面列出定义域，再检查核/像而不是只报结论。
image = {mapping[element] for element in domain}
kernel = {element for element in domain if mapping[element] == identity}
```

## Python 代码片段：多项式不可约性与因式分解
```python
import sympy as sp

x = sp.symbols("x")
# poly_expr 与 coefficient_domain 来自题面，例如 sp.QQ 或有限域模数。
poly = sp.Poly(poly_expr, x, domain=coefficient_domain)
factorization = sp.factor_list(poly)
gcd_value = sp.gcd(poly, sp.Poly(other_expr, x, domain=coefficient_domain))
# 因式分解结果必须结合指定系数域解释，不能直接从 QQ 推到 GF(p)。
```

## Python 代码片段：有限群 Sylow 数的必要条件
```python
def sylow_number_candidates(group_order, prime):
    """返回同时满足 n_p | |G|/p^a 且 n_p == 1 mod p 的候选数。"""
    p_power = 1
    while group_order % (p_power * prime) == 0:
        p_power *= prime
    quotient = group_order // p_power
    return [d for d in range(1, quotient + 1) if quotient % d == 0 and d % prime == 1]

# 这只给必要条件；唯一候选才能推出正规 Sylow 子群。
```

## 输出契约
- 明确全部运算与对象；证明题给出闭性/同态/次数等关键链条，计算题逐项复核。
- 题目涉及群、环、域、Galois 结构时不改路由到高等代数；仅矩阵或线性空间计算才应另选高等代数。
- 代码片段仅核验有限对象或代数恒等式；完整同构、正规性和扩张论证仍须写出证明。

## 模块级验证代码（与抽象代数 skill 的 9 个模块对应）

## Python 代码片段：模块1 群的基本概念
```python
from itertools import product

# operation、elements 和 identity 由题面给出；有限实例逐项检查封闭性。
closure = all(operation(a, b) in elements for a, b in product(elements, repeat=2))
identity_check = all(operation(identity, a) == a == operation(a, identity) for a in elements)
```

## Python 代码片段：模块2 子群与商群
```python
# inverse、subgroup、group_operation 由题面运算给出。
subgroup_test = bool(subgroup) and all(
    group_operation(a, inverse(b)) in subgroup
    for a, b in product(subgroup, repeat=2)
)
cosets = {frozenset(group_operation(g, h) for h in subgroup) for g in elements}
index = len(cosets)
```

## Python 代码片段：模块3 群同态与同构定理
```python
from itertools import product

homomorphism_check = all(
    mapping[group_operation(a, b)] == target_operation(mapping[a], mapping[b])
    for a, b in product(domain, repeat=2)
)
kernel = {a for a in domain if mapping[a] == target_identity}
image = {mapping[a] for a in domain}
```

## Python 代码片段：模块4 对称群与群作用
```python
from collections import Counter

orbit = {action(group_element, point) for group_element in group_elements}
stabilizer = {g for g in group_elements if action(g, point) == point}
orbit_stabilizer_gap = len(group_elements) - len(orbit) * len(stabilizer)
class_sizes = Counter(conjugacy_class(element) for element in group_elements)
```

## Python 代码片段：模块5 Sylow 定理
```python
import sympy as sp

def sylow_candidates(group_order, prime):
    p_power = prime ** sp.factorint(group_order).get(prime, 0)
    quotient = group_order // p_power
    return [d for d in sp.divisors(quotient) if d % prime == 1]

possible_sylow_counts = sylow_candidates(group_order, prime)
```

## Python 代码片段：模块6 环论基础
```python
from itertools import product

ideal_absorption = all(
ring_mul(r, a) in ideal and ring_mul(a, r) in ideal
    for r, a in product(ring, ideal)
)
zero_divisor_pairs = [(a, b) for a, b in product(ring, repeat=2)
                      if a != zero and b != zero and ring_mul(a, b) == zero]
```

## Python 代码片段：模块7 多项式与域扩张
```python
import sympy as sp

x = sp.symbols("x")
poly = sp.Poly(polynomial_expression, x, domain=coefficient_domain)
factorization = sp.factor_list(poly)
extension_degree = sp.degree(minimal_polynomial, x)
```

## Python 代码片段：模块8 有限域
```python
import sympy as sp

p = sp.symbols("p", integer=True, positive=True)
field_order = prime ** extension_degree
frobenius_residual = sp.rem(sp.Poly(x ** field_order - x, x, modulus=prime),
                            sp.Poly(modulus_polynomial, x, modulus=prime))
```

## Python 代码片段：模块9 有限 Abel 群分类
```python
from sympy.utilities.iterables import partitions

# 每个 prime_power_component 的分拆代表一个初等因子类型。
partition_types = list(partitions(exponent))
invariant_orders = [prime ** part for part in partition_types for exponent in part]
classification_count = len(partition_types)
```
