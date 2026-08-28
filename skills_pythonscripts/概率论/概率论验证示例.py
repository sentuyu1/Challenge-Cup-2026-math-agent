# 概率论：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是面向数学智能体的知识说明，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整模拟或统计程序。

## 使用规则
- 先界定样本空间、事件、随机变量、参数和独立性；概率、密度和条件事件都必须来自题面。
- 静态随机变量与分布计算归本目录；Markov、Poisson 过程、Brownian 等时间演化模型转随机过程，估计/检验转统计推断。
- 计算结果用归一化、边缘化、期望定义或独立方法交叉核对，不以无种子模拟替代推导。

## 知识点 1：古典概型与条件概率
- 等可能模型先明确基本事件是否等可能；组合计数注意顺序、重复和互斥性。
- $P(A\mid B)=P(A\cap B)/P(B)$ 要求 $P(B)>0$；Bayes 公式须列出完备事件组和全概率分母。

## 知识点 2：一维随机变量
- 离散型分布检查 $\sum p_i=1$，连续型密度检查非负性和积分为 $1$。
- 分布函数满足单调、右连续及两端极限；由分布函数求密度要说明可微区间。
- 变换题区分单调变换、分段反函数和多原像求和。

## 知识点 3：多维分布与条件量
- 联合密度/质量先归一化，再求边缘和条件分布。
- 独立性要求联合分布可分解为边缘分布乘积，零协方差通常不推出独立。
- 条件期望、全期望和全方差公式应保留条件对象。

## 知识点 4：数字特征与极限定理
- $E[X]$、$\operatorname{Var}(X)$、协方差和相关系数要先确认矩存在；方差不能为负。
- MGF/特征函数变换注意定义域；和的分布可用独立性和卷积。
- 大数定律与中心极限定理需核对独立同分布、方差有限和标准化方式。

## Python 代码片段：离散分布的归一化、期望与方差
```python
import sympy as sp

# support 与 pmf 必须逐项来自题面，不能自行截断或补全尾部。
normalization = sp.simplify(sum(pmf[value] for value in support))
expectation = sp.simplify(sum(value * pmf[value] for value in support))
variance = sp.simplify(sum((value - expectation) ** 2 * pmf[value] for value in support))
if normalization != 1:
    raise ValueError("概率质量函数未归一化")
```

## Python 代码片段：连续密度、分布函数与尾部概率
```python
import sympy as sp

x, t = sp.symbols("x t", real=True)
# density、lower、upper 与 threshold 均由题面给出。
normalization = sp.integrate(density, (x, lower, upper))
cdf_at_t = sp.integrate(density, (x, lower, t))
tail_probability = sp.integrate(density, (x, threshold, upper))
mean = sp.integrate(x * density, (x, lower, upper))
```

## Python 代码片段：联合分布的边缘化与独立性
```python
import sympy as sp

x, y = sp.symbols("x y", real=True)
# joint_density 及积分区域来自题面。
marginal_x = sp.integrate(joint_density, (y, y_lower, y_upper))
marginal_y = sp.integrate(joint_density, (x, x_lower, x_upper))
independence_gap = sp.simplify(joint_density - marginal_x * marginal_y)
covariance = sp.integrate(
    (x - mean_x) * (y - mean_y) * joint_density,
    (x, x_lower, x_upper), (y, y_lower, y_upper),
)
```

## 输出契约
- 最终答案明确事件方向、分布参数、积分/求和范围和概率值；尾部概率不可把 $>$ 与 $<$ 混淆。
- 条件不足时说明无法判定独立性或无法使用极限定理，不构造额外样本。
- 代码片段只在分布与积分区域完整时使用；条件概率、独立性和极限定理前提仍需用文字明确说明。

## 模块级验证代码（与概率论 skill 的 8 个模块对应）

## Python 代码片段：模块1 古典概型与组合计数
```python
from math import comb

sample_count = comb(total_objects, sample_size)
favourable_count = sum(comb(group_size, selected) for group_size, selected in cases)
classical_probability = favourable_count / sample_count
```

## Python 代码片段：模块2 随机变量与分布
```python
import sympy as sp

x = sp.symbols("x", real=True)
pmf_sum = sp.summation(pmf, (x, support_left, support_right))
pdf_integral = sp.integrate(density, (x, lower, upper))
cdf = sp.integrate(density, (x, lower, threshold))
```

## Python 代码片段：模块3 多维随机变量
```python
import sympy as sp

x, y = sp.symbols("x y", real=True)
marginal_x = sp.integrate(joint_density, (y, y_left, y_right))
marginal_y = sp.integrate(joint_density, (x, x_left, x_right))
conditional_density = sp.simplify(joint_density / marginal_x)
```

## Python 代码片段：模块4 数字特征
```python
import sympy as sp

mean = sp.simplify(sp.integrate(x * density, (x, lower, upper)))
second_moment = sp.simplify(sp.integrate(x ** 2 * density, (x, lower, upper)))
variance = sp.simplify(second_moment - mean ** 2)
```

## Python 代码片段：模块5 极限定理
```python
import sympy as sp

standard_error = sigma / sp.sqrt(n)
clt_standardized = sp.simplify((sample_mean - population_mean) / standard_error)
law_of_large_numbers_gap = sp.simplify(sample_mean - population_mean)
```

## Python 代码片段：模块6 概率不等式与性质
```python
import sympy as sp

markov_bound = sp.simplify(expectation / threshold)
chebyshev_bound = sp.simplify(variance / deviation ** 2)
covariance = sp.simplify(expectation_xy - expectation_x * expectation_y)
```

## Python 代码片段：模块7 Bayes 公式与全概率
```python
import sympy as sp

total_probability = sp.simplify(sum(prior[i] * likelihood[i] for i in hypotheses))
posterior = {
    i: sp.simplify(prior[i] * likelihood[i] / total_probability)
    for i in hypotheses
}
posterior_sum = sp.simplify(sum(posterior.values()))
```

## Python 代码片段：模块8 独立随机变量和的分布（卷积）
```python
import sympy as sp

k, j = sp.symbols("k j", integer=True)
convolution = sp.summation(pmf_x.subs(x, j) * pmf_y.subs(y, k - j),
                           (j, support_x_left, support_x_right))
convolution_normalized = sp.simplify(sp.summation(convolution, (k, sum_left, sum_right)))
```

## Python 代码片段：竞赛拓展——二项分布正态近似
```python
import sympy as sp

continuity_corrected_z = sp.simplify((cutoff + sp.Rational(1, 2) - n * p) /
                                     sp.sqrt(n * p * (1 - p)))
```

## Python 代码片段：竞赛拓展——PGF 与分式线性不动点
```python
import sympy as sp

s = sp.symbols("s", real=True)
pgf = p / (1 - (1 - p) * s)
fixed_points = sp.solve(sp.Eq(pgf, s), s)
mean_from_pgf = sp.simplify(sp.diff(pgf, s).subs(s, 1))
```
