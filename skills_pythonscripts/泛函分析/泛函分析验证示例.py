# 泛函分析：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是供数学智能体调用的提示资料，包含可摘取的 Python/SymPy 代码片段，不是可直接运行的完整程序。

## 使用规则
- 每个向量、函数和算子都要先确认属于题面指定的范数空间；形式解不在该空间内时不能作为结论。
- 区分范数、内积、弱收敛、强收敛、紧性和谱分类，不能用有限维直觉直接推广到无穷维。
- 微分算子的形式伴随若核心涉及边界项或 PDE 结构，应提示转偏微分方程处理。

## 知识点 1：Banach、Hilbert 与完备性
- 完备性通过 Cauchy 列的极限仍在空间中判断；范数等价只能在满足相应条件时使用。
- Hilbert 空间可用正交分解和投影定理；一般 Banach 空间没有正交投影工具。

## 知识点 2：有界算子、伴随与投影
- 有界线性算子范数为 $\sup_{\|x\|\le1}\|Tx\|$；核、像与定义域均要说明。
- Hilbert 空间伴随由 $\langle Tx,y\rangle=\langle x,T^*y\rangle$ 定义；积分/微分算子还要核对边界项。
- 正交投影满足 $P^2=P=P^*$；仅幂等并不自动正交。

## 知识点 3：紧算子与谱
- 紧算子把有界集送到相对紧集；无穷维情形必须避免“有界即紧”的错误。
- 谱分类时依次检查 $\lambda I-T$ 的单射性、值域稠密性和逆的有界性。
- 紧算子非零谱点为特征值；$0$ 的谱型必须结合是否为特征值和逆是否有界判断。

## 知识点 4：核心定理
- 压缩映射原理要求完备空间和压缩常数小于 $1$。
- Riesz 表示、Hahn--Banach、开映射/闭图像、一致有界性和 Arzela--Ascoli 都要逐条写出前提。
- 弱收敛与强收敛要分别用测试泛函和范数收敛验证，不能互相替换。

## Python 代码片段：有限维算子范数、伴随与投影
```python
import sympy as sp

# A 是题面给出的有限维矩阵；有限维计算不能替代无穷维空间证明。
A = sp.Matrix(operator_matrix)
adjoint = A.conjugate().T
gram = adjoint * A
singular_squares = gram.eigenvals()  # 2-范数平方的候选特征值
projection_check = sp.simplify(P * P - P) == sp.zeros(*P.shape) and P == P.conjugate().T
```

## Python 代码片段：压缩映射与不动点残差
```python
import sympy as sp

x = sp.symbols("x", real=True)
# phi、interval 和初值来自题面；先由导数上界确认压缩条件。
derivative = sp.diff(phi, x)
fixed_point_residual = sp.simplify(phi.subs(x, candidate) - candidate)
derivative_bound_expression = sp.Abs(derivative)
```

## Python 代码片段：谱点的有限维辅助核验
```python
import sympy as sp

lam = sp.symbols("lam")
characteristic = (lam * sp.eye(A.rows) - A).det()
eigenvalues = sp.solve(sp.Eq(characteristic, 0), lam)
kernel_dimensions = {value: len((value * sp.eye(A.rows) - A).nullspace()) for value in eigenvalues}
# 无穷维连续谱/剩余谱不能由此代码判定，仍需分析值域稠密性和逆的有界性。
```

## 输出契约
- 答案中保留空间、范数/内积、定义域和值域、所用定理前提及谱的三分类依据。
- 无法由题面确认紧性、稠密性或有界逆时，明确写为未能判定，不能补造边界条件。
- 明确指出每段代码只覆盖有限维或符号可计算部分，避免把数值输出误作泛函分析的一般证明。

## 模块级验证代码（与泛函分析 skill 的 20 个模块对应）

## Python 代码片段：模块1 度量空间完备性判定
```python
import sympy as sp

distance_gap = sp.simplify(metric(x_n, x_m))
cauchy_bound = sp.simplify(distance_gap.subs({n: lower_index, m: upper_index}))
```

## Python 代码片段：模块2 压缩映射原理求不动点
```python
import sympy as sp

x = sp.symbols("x", real=True)
fixed_points = sp.solve(sp.Eq(mapping(x), x), x)
contraction_gap = sp.simplify(sp.diff(mapping(x), x))
```

## Python 代码片段：模块3 范数等价性验证
```python
import sympy as sp

vector = sp.Matrix(vector_entries)
norm_one = sum(abs(value) for value in vector)
norm_two = sp.sqrt(vector.dot(vector))
norm_infinity = max(abs(value) for value in vector)
equivalence_gaps = (sp.simplify(norm_two - norm_one), sp.simplify(norm_infinity - norm_two))
```

## Python 代码片段：模块4 内积空间与正交分解
```python
import sympy as sp

gram = sp.Matrix([[inner_product(u, v) for v in basis] for u in basis])
coordinates = gram.LUsolve(sp.Matrix([inner_product(vector, u) for u in basis]))
orthogonality_residual = [sp.simplify(inner_product(remainder, u)) for u in basis]
```

## Python 代码片段：模块5 有界线性算子范数（有限维）
```python
import sympy as sp

operator_matrix = sp.Matrix(operator_entries)
gram_matrix = operator_matrix.T * operator_matrix
singular_values = [sp.sqrt(value) for value in gram_matrix.eigenvals().keys()]
operator_norm = sp.Max(*singular_values)
```

## Python 代码片段：模块6 积分算子范数
```python
import sympy as sp

x, t = sp.symbols("x t", real=True)
kernel_norm = sp.integrate(sp.integrate(abs(kernel(x, t)), (t, left_t, right_t)),
                           (x, left_x, right_x))
```

## Python 代码片段：模块7 伴随算子计算
```python
import sympy as sp

operator_matrix = sp.Matrix(operator_entries)
adjoint_matrix = operator_matrix.conjugate().T
adjoint_identity_gap = sp.simplify(adjoint_matrix - operator_matrix.conjugate().T)
```

## Python 代码片段：模块8 正交投影计算
```python
import sympy as sp

basis_matrix = sp.Matrix(basis_columns)
projection = basis_matrix * (basis_matrix.T * basis_matrix).inv() * basis_matrix.T * vector
projection_residual = sp.simplify(basis_matrix.T * (vector - projection))
```

## Python 代码片段：模块9 自伴算子判断
```python
import sympy as sp

A = sp.Matrix(operator_entries)
self_adjoint_gap = sp.simplify(A - A.conjugate().T)
self_adjoint = self_adjoint_gap == sp.zeros(A.rows)
```

## Python 代码片段：模块9.1 微分算子的形式伴随
```python
import sympy as sp

x = sp.symbols("x", real=True)
pairing_gap = sp.simplify(
    sp.integrate(v * differential_operator(u), (x, left, right))
    - sp.integrate(formal_adjoint(v) * u, (x, left, right))
    - boundary_term
)
```

## Python 代码片段：模块10 紧算子判定
```python
import sympy as sp

finite_rank = sp.Matrix(operator_entries).rank()
finite_dimensional_compact = finite_rank <= ambient_dimension
truncation_gap = sp.simplify(operator_matrix - finite_rank_approximation)
```

## Python 代码片段：模块11 谱半径计算
```python
import sympy as sp

A = sp.Matrix(operator_entries)
eigenvalues = A.eigenvals()
spectral_radius = sp.Max(*[sp.Abs(value) for value in eigenvalues])
```

## Python 代码片段：模块12 Riesz 表示定理应用
```python
import sympy as sp

representer = gram_matrix.inv() * functional_values
representation_gap = sp.simplify(functional_values - gram_matrix * representer)
```

## Python 代码片段：模块13 Fredholm 二择一定理
```python
import sympy as sp

A = sp.Matrix(operator_entries)
nullity = len(A.nullspace())
range_codimension = A.rows - A.rank()
fredholm_index = nullity - range_codimension
```

## Python 代码片段：模块14 闭算子与闭图像定理
```python
import sympy as sp

graph_vector = sp.Matrix.vstack(input_vector, operator_matrix * input_vector)
graph_residual = sp.simplify(graph_vector - sp.Matrix.vstack(input_vector, output_vector))
```

## Python 代码片段：模块15 Banach 与 Hilbert 空间判别
```python
import sympy as sp

hermitian_gap = sp.simplify(inner_product(u, v) - sp.conjugate(inner_product(v, u)))
parallelogram_gap = sp.simplify(norm(u + v) ** 2 + norm(u - v) ** 2
                                - 2 * norm(u) ** 2 - 2 * norm(v) ** 2)
```

## Python 代码片段：模块16 一致有界性原理
```python
import sympy as sp

operator_values = [sp.simplify(operator_n(vector)) for operator_n in operator_family]
pointwise_bound = sp.Max(*[sp.Abs(value) for value in operator_values])
```

## Python 代码片段：模块17 弱收敛与强收敛
```python
import sympy as sp

weak_gaps = [sp.limit(functional(sequence_n), n, sp.oo) - functional(limit_vector)
             for functional in test_functionals]
strong_gap = sp.limit(norm(sequence_n - limit_vector), n, sp.oo)
```

## Python 代码片段：模块18 紧集判定（Arzela--Ascoli）
```python
import sympy as sp

uniform_bound = sp.sup(abs(function_family(n, x)), (n, n_left, n_right), (x, left, right))
equicontinuity_modulus = sp.sup(abs(function_family(n, x + h) - function_family(n, x)),
                                (n, n_left, n_right), (x, left, right))
```

## Python 代码片段：模块19 Hahn--Banach 延拓
```python
import sympy as sp

extension_value = sp.symbols("extension_value", real=True)
domination_gap = sp.simplify(abs(extension_value) - seminorm(new_vector))
linear_extension_gap = sp.simplify(extension(functional_vector + new_vector)
                                   - extension(functional_vector) - extension_value)
```

## Python 代码片段：模块20 谱集分类
```python
import sympy as sp

A = sp.Matrix(operator_entries)
resolvent_determinant = sp.factor((lambda_symbol * sp.eye(A.rows) - A).det())
candidate_spectrum = sp.solve(sp.Eq(resolvent_determinant, 0), lambda_symbol)
```

## Python 代码片段：竞赛拓展——傅里叶变换与柯西列
```python
import sympy as sp

x, omega = sp.symbols("x omega", real=True)
transform = sp.integrate(function * sp.exp(-sp.I * omega * x), (x, -sp.oo, sp.oo))
cauchy_gap = sp.limit(metric(sequence_n, sequence_m), n, sp.oo)
```
