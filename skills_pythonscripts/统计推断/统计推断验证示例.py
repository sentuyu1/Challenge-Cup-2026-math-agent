# 统计推断：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是提示词式的统计验证资料，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整数据分析或随机模拟程序。

## 使用规则
- 先记录样本模型、参数化、样本量、独立性、显著性水平和题面定义；不得补造样本、方差或分布。
- OLS、异方差、计量经济学和回归诊断转线性回归；Markov/Poisson 等动态模型转随机过程；单纯概率计算转概率论。
- 最终答复保留统计量、自由度、临界值或 p 值、区间双端点和实际语义结论。

## 知识点 1：估计
- 矩估计和最大似然从样本分布出发；极值点要检查参数空间和端点。
- 无偏性、相合性和有效性是不同性质；Cramer--Rao 下界要求正则性条件和 Fisher 信息。
- MSE 为方差加偏差平方，比较估计量时不能只看无偏性。

## 知识点 2：置信区间
- 正态总体均值根据总体方差已知/未知选择 $z$ 或 $t$ 分布；方差区间用 $\chi^2$ 分布并注意分位点倒置。
- 最终答案必须写成 $[L,U]$，包括自由度和置信水平；不能只给误差界或单端点。

## 知识点 3：假设检验与功效
- 写出 $H_0,H_1$、检验统计量、拒绝域或 p 值、临界值比较和“拒绝/不拒绝 $H_0$”的题意结论。
- 单侧/双侧方向由备择假设决定；第二类错误 $\beta$ 和功效 $1-\beta$ 不可互换。
- $z,t,\chi^2,F$ 检验均须核对分布假设和自由度。

## 知识点 4：拟合、方差分析与描述统计
- 卡方拟合优度要检查期望频数、自由度和合并组规则；ANOVA 写出平方和、自由度、均方和 $F$ 值。
- 似然比检验说明嵌套模型及渐近分布条件。
- 直方图适用于单变量分布，散点图需要两个变量，时间数列需区分趋势、季节、循环与不规则变动。
- 正态分布参数化先按题面区分标准差与方差；选项题按课程口径逐项核验。

## Python 代码片段：似然、矩估计与参数约束
```python
import sympy as sp

theta = sp.symbols("theta", real=True)
# likelihood 或 log_likelihood 必须由题面样本模型构造。
score = sp.diff(log_likelihood, theta)
critical_points = sp.solve(sp.Eq(score, 0), theta)
second_derivative = sp.diff(log_likelihood, theta, 2)
candidate_checks = {value: sp.simplify(second_derivative.subs(theta, value)) for value in critical_points}
# 还需在文字中检查参数空间边界与可行性。
```

## Python 代码片段：置信区间与检验统计量
```python
import sympy as sp

# xbar、sigma_or_s、n、critical_value 和 mu0 均来自题面。
standard_error = sigma_or_s / sp.sqrt(n)
confidence_interval = (sp.simplify(xbar - critical_value * standard_error),
                       sp.simplify(xbar + critical_value * standard_error))
test_statistic = sp.simplify((xbar - mu0) / standard_error)
# 单侧/双侧拒绝域由 H1 决定，不能由该片段自动推断。
```

## Python 代码片段：卡方与 ANOVA 字段核验
```python
import sympy as sp

# observed、expected 和自由度均由题面给出。
chi_square = sp.simplify(sum((obs - exp) ** 2 / exp for obs, exp in zip(observed, expected)))
mean_square_between = sp.simplify(sum_squares_between / degrees_between)
mean_square_within = sp.simplify(sum_squares_within / degrees_within)
f_statistic = sp.simplify(mean_square_between / mean_square_within)
```

## 输出契约
- 统计结论必须完整且可审计，不能只输出一个 p 值或检验统计量。
- 缺失样本或模型参数时，给出符号表达式或指出缺失字段。
- 代码片段只计算由题面指定的统计量；必须另行报告自由度、临界值/p 值、拒绝结论和实际问题解释。

## 模块级验证代码（与统计推断 skill 的 20 个模块对应）

## Python 代码片段：模块1 矩估计
```python
import sympy as sp

theta = sp.symbols("theta", real=True)
moment_equation = sp.Eq(sample_moment, theoretical_moment(theta))
moment_estimate = sp.solve(moment_equation, theta)
```

## Python 代码片段：模块2 离散型极大似然估计
```python
import sympy as sp

theta = sp.symbols("theta", real=True)
log_likelihood = sp.simplify(sum(sp.log(pmf(value, theta)) for value in sample))
discrete_mle = sp.solve(sp.Eq(sp.diff(log_likelihood, theta), 0), theta)
```

## Python 代码片段：模块3 连续型极大似然估计
```python
import sympy as sp

theta = sp.symbols("theta", positive=True)
log_likelihood = sp.simplify(sum(sp.log(density(value, theta)) for value in sample))
score = sp.diff(log_likelihood, theta)
continuous_mle = sp.solve(sp.Eq(score, 0), theta)
```

## Python 代码片段：模块4 无偏性判别
```python
import sympy as sp

estimator_expectation = sp.simplify(expectation_of_estimator)
unbiased_gap = sp.simplify(estimator_expectation - parameter)
```

## Python 代码片段：模块5 相合性与无偏修正
```python
import sympy as sp

consistency_gap = sp.limit(estimator_n - parameter, n, sp.oo)
finite_sample_bias = sp.simplify(expectation_estimator - parameter)
unbiased_correction = sp.simplify(estimator - finite_sample_bias)
```

## Python 代码片段：模块6 正态均值置信区间（sigma 已知）
```python
import sympy as sp

standard_error = sigma / sp.sqrt(n)
known_sigma_interval = (sp.simplify(xbar - z_quantile * standard_error),
                        sp.simplify(xbar + z_quantile * standard_error))
```

## Python 代码片段：模块7 正态均值置信区间（sigma 未知）
```python
import sympy as sp

standard_error_t = sample_standard_deviation / sp.sqrt(n)
unknown_sigma_interval = (sp.simplify(xbar - t_quantile * standard_error_t),
                          sp.simplify(xbar + t_quantile * standard_error_t))
```

## Python 代码片段：模块8 正态总体方差置信区间
```python
import sympy as sp

chi_square_statistic = sp.simplify((n - 1) * sample_variance / sigma2)
variance_interval = (sp.simplify((n - 1) * sample_variance / chi2_upper),
                     sp.simplify((n - 1) * sample_variance / chi2_lower))
```

## Python 代码片段：模块9 双总体均值差区间估计
```python
import sympy as sp

difference_se = sp.sqrt(sigma1 ** 2 / n1 + sigma2 ** 2 / n2)
mean_difference_interval = (sp.simplify(xbar1 - xbar2 - critical * difference_se),
                             sp.simplify(xbar1 - xbar2 + critical * difference_se))
```

## Python 代码片段：模块10 单总体均值 Z 检验
```python
import sympy as sp

z_statistic = sp.simplify((xbar - mu0) / (sigma / sp.sqrt(n)))
z_rejection_gap = sp.simplify(abs(z_statistic) - z_critical)
```

## Python 代码片段：模块11 单总体均值 t 检验
```python
import sympy as sp

t_statistic = sp.simplify((xbar - mu0) / (sample_standard_deviation / sp.sqrt(n)))
t_rejection_gap = sp.simplify(abs(t_statistic) - t_critical)
```

## Python 代码片段：模块12 单总体方差 chi-square 检验
```python
import sympy as sp

chi_statistic = sp.simplify((n - 1) * sample_variance / sigma02)
chi_rejection_gap = sp.simplify(chi_statistic - chi_critical)
```

## Python 代码片段：模块13 双总体方差 F 检验
```python
import sympy as sp

f_statistic = sp.simplify(sample_variance_1 / sample_variance_2)
f_reciprocal_gap = sp.simplify(f_statistic * sample_variance_2 / sample_variance_1 - 1)
```

## Python 代码片段：模块14 双总体均值差假设检验
```python
import sympy as sp

pooled_variance = sp.simplify(((n1 - 1) * variance1 + (n2 - 1) * variance2) /
                              (n1 + n2 - 2))
pooled_t = sp.simplify((xbar1 - xbar2 - null_difference) /
                       sp.sqrt(pooled_variance * (1 / n1 + 1 / n2)))
```

## Python 代码片段：模块15 Cramer--Rao 下界与有效估计
```python
import sympy as sp

fisher_information = sp.simplify(-sp.diff(log_likelihood, theta, 2))
cr_lower_bound = sp.simplify(1 / fisher_information)
efficiency_gap = sp.simplify(estimator_variance - cr_lower_bound)
```

## Python 代码片段：模块16 MSE 与偏倚-方差权衡
```python
import sympy as sp

mse = sp.simplify(estimator_variance + bias ** 2)
comparison_gap = sp.simplify(mse_a - mse_b)
```

## Python 代码片段：模块17 两类错误与检验功效
```python
import sympy as sp

power = sp.simplify(1 - beta_error)
error_sum_check = sp.simplify(alpha_error + beta_error)
```

## Python 代码片段：模块18 chi-square 拟合优度检验
```python
import sympy as sp

chi_square = sp.simplify(sum((observed_i - expected_i) ** 2 / expected_i
                             for observed_i, expected_i in zip(observed, expected)))
degrees_of_freedom = category_count - 1 - estimated_parameter_count
```

## Python 代码片段：模块19 单因素方差分析
```python
import sympy as sp

mean_square_between = sp.simplify(sum_squares_between / degrees_between)
mean_square_within = sp.simplify(sum_squares_within / degrees_within)
anova_f = sp.simplify(mean_square_between / mean_square_within)
```

## Python 代码片段：模块20 似然比检验
```python
import sympy as sp

likelihood_ratio = sp.simplify(2 * (log_likelihood_full - log_likelihood_null))
asymptotic_gap = sp.simplify(likelihood_ratio - chi_square_critical)
```
