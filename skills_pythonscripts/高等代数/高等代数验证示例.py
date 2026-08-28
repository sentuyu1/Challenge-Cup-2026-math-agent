# 高等代数：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是提示词式验证资料，包含可摘取的 Python/SymPy 代码片段，不是可直接运行的完整矩阵或符号计算程序。

## 使用规则
- 先确认系数域、维数、矩阵大小、参数范围与重数；计算结果必须回代原多项式、矩阵或线性关系。
- 群、环、域和 Galois 结构题转抽象代数；实变量极限、收敛和微分型函数方程转数学分析。
- 题目若给出多个问项，分别保留矩阵、基、坐标、特征值、重数等完整字段。

## 知识点 1：多项式
- 使用带余除法、Euclid 算法、因式分解和根的重数；不可约性必须相对于指定系数域判断。
- Vieta 公式、对称多项式和判别式使用前确认首项系数与根的个数/重数。
- 极小多项式整除特征多项式，并由其根和重根限制 Jordan 结构。

## 知识点 2：行列式与矩阵
- 行变换改变行列式时同步处理符号和倍数；矩阵可逆等价于行列式非零、满秩等条件需在方阵场景使用。
- 求逆、秩、零空间和解空间时，将结果代回 $AX=b$ 或 $Av=0$。
- 参数矩阵要分离秩发生变化的特殊参数值。

## 知识点 3：线性空间与二次型
- 基、维数、线性无关和张成关系必须在同一空间/同一系数域内讨论。
- 坐标变换写明基变换矩阵方向；Gram--Schmidt 需保留正交化顺序和零向量情形。
- 二次型按合同变换化标准形，正定性可用顺序主子式或特征值但要满足对应条件。

## 知识点 4：特征值、对角化与 Jordan 形
- 特征值由 $\det(\lambda I-A)=0$ 得到，几何重数不超过代数重数。
- 可对角化要求每个特征值的特征子空间维数之和为 $n$；Jordan 形要给相似变换或块结构依据。
- max-plus/热带代数题明确采用的加法、乘法和特征方程，不能沿用通常线性代数运算。

## Python 代码片段：多项式、根与因式分解
```python
import sympy as sp

x = sp.symbols("x")
# polynomial_expr 和 coefficient_domain 均由题面决定。
poly = sp.Poly(polynomial_expr, x, domain=coefficient_domain)
factorization = sp.factor_list(poly)
roots_with_multiplicity = sp.roots(poly.as_expr(), x)
remainder = sp.rem(poly, sp.Poly(divisor_expr, x, domain=coefficient_domain))
```

## Python 代码片段：矩阵秩、零空间与线性方程
```python
import sympy as sp

A = sp.Matrix(matrix_entries)
b = sp.Matrix(rhs_entries)
rank_a = A.rank()
rank_augmented = A.row_join(b).rank()
null_basis = A.nullspace()
solution_set = sp.linsolve((A, b))
# 若 rank_a != rank_augmented，则无解；参数分类需在文字中保留。
```

## Python 代码片段：特征值、对角化与 Jordan 形
```python
import sympy as sp

A = sp.Matrix(matrix_entries)
characteristic_polynomial = A.charpoly().as_expr()
eigen_data = A.eigenvects()
diagonalizable = sum(len(vectors) for _, _, vectors in eigen_data) == A.rows
P, J = A.jordan_form()  # 返回相似变换矩阵 P 和 Jordan 形 J
jordan_check = sp.simplify(P.inv() * A * P - J)
```

## Python 代码片段：二次型的合同变换核验
```python
import sympy as sp

Q = sp.Matrix(quadratic_form_matrix)
congruence_check = sp.simplify(change_of_basis.T * Q * change_of_basis - diagonal_form)
leading_principal_minors = [Q[:k, :k].det() for k in range(1, Q.rows + 1)]
# Sylvester 判据只适用于实对称矩阵的正定性判断。
```

## 输出契约
- 最终答案包含完整多项式、矩阵/基/标准形及参数分类，并给出回代或不变量核验。
- 不把数值近似根当作精确重根结论，除非题面明确要求近似。
- 代码结果必须与指定系数域、参数范围和相似/合同变换方向一并解释，不能只粘贴 SymPy 输出。

## 模块级验证代码（与高等代数 skill 的 8 个主模块对应）

## Python 代码片段：模块一 多项式理论
```python
import sympy as sp

x = sp.symbols("x")
poly = sp.Poly(polynomial_expression, x, domain=coefficient_domain)
quotient, remainder = sp.div(poly, divisor, domain=coefficient_domain)
discriminant = sp.discriminant(poly.as_expr(), x)
```

## Python 代码片段：模块二 行列式
```python
import sympy as sp

A = sp.Matrix(matrix_entries)
determinant = sp.factor(A.det())
cofactor_check = sp.simplify(sum(A[0, j] * A.cofactor(0, j) for j in range(A.cols)) - determinant)
```

## Python 代码片段：模块三 矩阵
```python
import sympy as sp

A = sp.Matrix(matrix_entries)
inverse = A.inv() if A.det() != 0 else None
inverse_residual = sp.zeros(A.rows) if inverse is None else sp.simplify(A * inverse - sp.eye(A.rows))
```

## Python 代码片段：模块四 线性方程组
```python
import sympy as sp

A = sp.Matrix(matrix_entries)
b = sp.Matrix(rhs_entries)
rank_gap = A.row_join(b).rank() - A.rank()
solution_set = sp.linsolve((A, b))
```

## Python 代码片段：模块五 二次型
```python
import sympy as sp

Q = sp.Matrix(quadratic_form_matrix)
leading_minors = [Q[:k, :k].det() for k in range(1, Q.rows + 1)]
quadratic_value = (vector.T * Q * vector)[0]
```

## Python 代码片段：模块六 线性空间与线性变换
```python
import sympy as sp

basis_matrix = sp.Matrix(basis_columns)
dimension = basis_matrix.rank()
coordinate_residual = sp.simplify(basis_matrix * coordinates - vector)
```

## Python 代码片段：模块七 欧氏空间
```python
import sympy as sp

gram = sp.Matrix([[u.dot(v) for v in vectors] for u in vectors])
orthogonality = [sp.simplify(u.dot(v)) for u, v in orthogonal_pairs]
```

## Python 代码片段：模块八 特征值与对角化
```python
import sympy as sp

A = sp.Matrix(matrix_entries)
eigen_data = A.eigenvects()
geometric_dimensions = {value: len(vectors) for value, _, vectors in eigen_data}
diagonalizable = sum(geometric_dimensions.values()) == A.rows
```
