# 拓扑学：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是面向数学智能体的知识说明，包含可摘取的 Python 片段，不是可直接运行的完整集合枚举或图算法程序。

## 使用规则
- 每个结论先写明空间、拓扑、子空间/商空间结构和分离或紧致假设；不能把欧氏空间定理无条件移植到一般空间。
- 只涉及实数 Cauchy 列、极限或微积分时转数学分析；曲率、测地线和基本形式转微分几何。
- 有限空间例子可辅助反例，但一般性结论必须由拓扑定义、覆盖或映射性质证明。

## 知识点 1：拓扑、公理与基本集合运算
- 拓扑包含空集和全集，对任意并及有限交封闭；基和子基生成拓扑时说明生成过程。
- 内部、闭包、边界、导集和稠密性均依赖环境空间；补集和子空间拓扑要显式标出。

## 知识点 2：连续性与构造拓扑
- 连续映射可用开集原像、闭集原像或邻域定义验证；同胚需额外验证双射和逆连续。
- 子空间、积、商和 Sorgenfrey 拓扑使用对应定义，不把集合层面的双射误认成同胚。

## 知识点 3：紧致、连通与分离性
- 紧致性以任意开覆盖有限子覆盖定义；度量空间中的列紧等价需满足相应条件。
- 连通性用不存在非平凡分离判断；路径连通通常更强。
- Hausdorff、正则、正规等分离公理层级不可倒置。

## 知识点 4：基本群与覆盖空间
- 基本群依赖基点；一点并 $\bigvee_{i=1}^n S^1$ 的基本群为自由群 $F_n$。
- 描述普遍覆盖时要回答具体图结构：$F_n$ 的 Cayley 图是无限 $2n$-正则树。

## Python 代码片段：有限集合上的拓扑公理
```python
from itertools import combinations

def is_topology(points, topology):
    topology = {frozenset(item) for item in topology}
    if frozenset() not in topology or frozenset(points) not in topology:
        return False
    for family_size in range(len(topology) + 1):
        for family in combinations(topology, family_size):
            if frozenset().union(*family) not in topology:
                return False
    for left in topology:
        for right in topology:
            if left & right not in topology:
                return False
    return True

# 只适用于题面给出有限空间和显式拓扑族的情形。
```

## Python 代码片段：内部、闭包与连续性
```python
def interior(subset, topology):
    subset = frozenset(subset)
    return frozenset().union(*(open_set for open_set in topology if open_set <= subset))

def closure(subset, points, topology):
    complement = frozenset(points) - frozenset(subset)
    return frozenset(points) - interior(complement, topology)

def is_continuous(mapping, domain_topology, codomain_topology):
    return all(
        frozenset(point for point, image in mapping.items() if image in open_set) in domain_topology
        for open_set in codomain_topology
    )
```

## Python 代码片段：覆盖与连通性的有限反例搜索
```python
from itertools import combinations

def has_finite_subcover(open_cover, points):
    target = frozenset(points)
    for size in range(1, len(open_cover) + 1):
        if any(frozenset().union(*subcover) == target for subcover in combinations(open_cover, size)):
            return True
    return False

# 该片段只能核验有限开覆盖，不能用来证明一般空间紧致性。
```

## 输出契约
- 最终答案保留空间与拓扑、使用的定义/定理、必要反例或开覆盖/路径构造。
- 多问题必须同时回答不变量和题目要求的几何/图结构描述。
- 代码仅用于有限模型和反例；商拓扑、一般紧致性、基本群与覆盖空间结论必须依赖定义或定理证明。

## 模块级验证代码（与拓扑学 skill 的 7 个主知识点对应）

## Python 代码片段：模块1 拓扑公理与拓扑族
```python
from itertools import combinations

def topology_axioms(points, family):
    family = {frozenset(item) for item in family}
    union_all = frozenset().union(*family) if family else frozenset()
    finite_intersections = all(
        frozenset(a & b) in family for a, b in combinations(family, 2)
    )
    return (frozenset() in family and union_all == frozenset(points)
            and finite_intersections)
```

## Python 代码片段：模块2 内部、闭包、边界与导集
```python
def interior(subset, topology):
    return frozenset().union(*[open_set for open_set in topology if open_set <= subset])

closure = frozenset().union(*[closed for closed in closed_sets if closed >= subset])
boundary = closure - interior(subset, topology)
derived_set = frozenset(point for point in points
                         if any((open_set - {point}) & subset for open_set in topology
                                if point in open_set))
```

## Python 代码片段：模块3 连续映射及其刻画
```python
preimages = {frozenset(mapping_inverse(open_set)) for open_set in target_topology}
continuous = all(preimage in source_topology for preimage in preimages)
bijective = len(set(mapping.values())) == len(source_points) == len(target_points)
inverse_continuous = all(
    frozenset(inverse_mapping(open_set)) in target_topology
    for open_set in source_topology
)
```

## Python 代码片段：模块4 子空间、乘积、Sorgenfrey 与商拓扑
```python
subspace_topology = {frozenset(open_set & subspace) for open_set in ambient_topology}
product_basis = {frozenset(product_set(a, b)) for a in topology_x for b in topology_y}
quotient_saturated = all(
    union_of_fibres(open_set) == open_set for open_set in quotient_candidate
)
```

## Python 代码片段：模块5 紧致性、连通性与分离公理
```python
finite_subcover_exists = any(
    frozenset().union(*cover_subset) == frozenset(compact_subset)
    for cover_subset in finite_subcovers
)
separation_witness = next(
    ((u, v) for u, v in open_pairs if point_a in u and point_b in v and not (u & v)),
    None,
)
```

## Python 代码片段：模块6 基本群、覆盖空间与同调
```python
word_reduction = reduce_free_word(loop_word)
fundamental_group_rank = max(0, number_of_edges - number_of_vertices + number_of_components)
boundary_matrix = incidence_matrix  # 由题面单纯复形的定向边界给出
homology_kernel_dimension = len(boundary_matrix.nullspace())
```

## Python 代码片段：模块7 可分性与可数性公理
```python
countable_basis = len(basis) <= countable_bound
dense = all(any(open_set & dense_subset for open_set in topology if point in open_set)
            for point in points)
second_countable = countable_basis and all(open_set in generated_topology for open_set in topology)
```
