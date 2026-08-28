# 线性回归：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是供数学智能体参考的说明型验证提示，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整数据拟合程序。

## 使用规则
- 先明确响应变量、设计矩阵、参数、误差假设、样本量和模型是否含截距；不得自造观测值或协变量。
- 本目录处理 OLS、回归诊断、异方差、计量和模型选择；一般抽样检验/描述统计转统计推断，纯算法最小二乘转数值分析。
- 最终答案保留 $X^TX$、$X^Ty$、SSE、自由度、标准误、统计量、区间或 ANOVA 字段，不能只给一个系数。

## 知识点 1：OLS 与矩阵表达
- 一元回归使用中心化和式；多元回归在 $X$ 满列秩时 $\hat\beta=(X^TX)^{-1}X^Ty$。
- 残差满足正规方程；计算后用 $X^T(y-X\hat\beta)=0$ 或原题数据回验。
- 共线性或秩亏时不能直接写逆矩阵，需要说明可辨识性或广义逆处理。

## 知识点 2：方差、区间与检验
- 区分 $\operatorname{Var}(\hat\beta)$ 的真实方差和传统 OLS 标准误估计。
- 回归系数 $t$ 检验、整体/部分 $F$ 检验给出原假设、统计量、自由度、临界值/p 值和实际结论。
- 均值响应区间与新观测预测区间不同，后者多出误差项；区间必须有上下端点。

## 知识点 3：拟合优度与 ANOVA
- $SST=SSR+SSE$ 的分解需含截距模型；$R^2$、调整 $R^2$ 和 ANOVA 表要与自由度一致。
- 比较模型时说明是否嵌套，部分 $F$ 检验和 AIC/BIC 的目标不同。

## 知识点 4：诊断与扩展
- 异方差不必破坏 OLS 无偏性/一致性，但使传统标准误失真并失去 BLUE 保证；WLS 或稳健标准误依题设选择。
- VIF 诊断多重共线性，Durbin--Watson 诊断一阶自相关，残差图检验线性性、方差齐性和异常点。
- 函数形式未知时优先非参数回归；非线性回归与非线性最小二乘算法应分别说明。

## Python 代码片段：矩阵 OLS、残差与 SSE
```python
import sympy as sp

# X、y 必须由题面观测构造；先确认 X 满列秩。
X = sp.Matrix(design_matrix)
y = sp.Matrix(response_vector)
xtx = X.T * X
xty = X.T * y
beta_hat = xtx.inv() * xty
residuals = y - X * beta_hat
sse = sp.simplify((residuals.T * residuals)[0])
normal_equation_gap = sp.simplify(X.T * residuals)
```

## Python 代码片段：标准误、t/F 统计量与区间
```python
import sympy as sp

# residual_df、critical_value 和待检验系数索引均由题面给出。
sigma2_hat = sp.simplify(sse / residual_df)
covariance_hat = sp.simplify(sigma2_hat * xtx.inv())
standard_error_j = sp.sqrt(covariance_hat[coefficient_index, coefficient_index])
t_statistic = sp.simplify((beta_hat[coefficient_index] - null_value) / standard_error_j)
confidence_interval_j = (
    sp.simplify(beta_hat[coefficient_index] - critical_value * standard_error_j),
    sp.simplify(beta_hat[coefficient_index] + critical_value * standard_error_j),
)
```

## Python 代码片段：$R^2$、ANOVA 与 VIF
```python
import sympy as sp

y_bar = sp.simplify(sum(y) / y.rows)
sst = sp.simplify(sum((value - y_bar) ** 2 for value in y))
ssr = sp.simplify(sst - sse)
r_squared = sp.simplify(ssr / sst)
f_statistic = sp.simplify((ssr / model_df) / (sse / residual_df))
# VIF_j 需要将第 j 个自变量对其余自变量回归后代入 1/(1-R_j^2)。
```

## 输出契约
- 提交系数时连同题目要求的矩阵、残差平方和、自由度、标准误、检验/区间和解释一并给出。
- 不将“异方差使方差必然增大”作为通用结论；方向须由异方差结构决定。
- 代码中的矩阵、自由度和临界值必须与题面一一对应；最终答案还要解释显著性、区间或诊断结论。

## 模块级验证代码（与线性回归 skill 的 20 个模块对应）

## Python 代码片段：模块1 一元线性回归 OLS 估计
```python
import sympy as sp

x = sp.Matrix(x_values)
y = sp.Matrix(y_values)
design = sp.Matrix.hstack(sp.ones(len(x_values), 1), x)
beta_hat = (design.T * design).inv() * design.T * y
```

## Python 代码片段：模块2 回归系数的最小二乘计算
```python
import sympy as sp

residual = response - design * beta_hat
normal_equation_gap = sp.simplify(design.T * residual)
sse = sp.simplify((residual.T * residual)[0])
```

## Python 代码片段：模块3 误差方差的无偏估计
```python
import sympy as sp

residual_df = sample_size - design.cols
sigma2_hat = sp.simplify(sse / residual_df)
```

## Python 代码片段：模块4 回归系数标准误与 t 检验
```python
import sympy as sp

covariance_beta = sigma2_hat * (design.T * design).inv()
standard_errors = [sp.sqrt(covariance_beta[i, i]) for i in range(design.cols)]
t_statistics = [(beta_hat[i] - null_value[i]) / standard_errors[i]
                for i in range(design.cols)]
```

## Python 代码片段：模块5 回归系数 t 检验推导
```python
import sympy as sp

t_statistic_residual = sp.simplify(t_statistics[index] -
                                   (beta_hat[index] - null_value[index]) / standard_errors[index])
```

## Python 代码片段：模块6 回归系数置信区间
```python
import sympy as sp

confidence_interval = (
    sp.simplify(beta_hat[index] - critical_value * standard_errors[index]),
    sp.simplify(beta_hat[index] + critical_value * standard_errors[index]),
)
```

## Python 代码片段：模块7 多元回归矩阵形式
```python
import sympy as sp

design = sp.Matrix(design_entries)
normal_matrix = design.T * design
projection_matrix = design * normal_matrix.inv() * design.T
```

## Python 代码片段：模块8 多元回归 OLS 矩阵运算
```python
import sympy as sp

beta_hat = (design.T * design).inv() * design.T * response
fitted = design * beta_hat
residual = response - fitted
```

## Python 代码片段：模块9 判定系数 R²
```python
import sympy as sp

mean_response = sp.simplify(sum(response) / response.rows)
sst = sp.simplify(sum((value - mean_response) ** 2 for value in response))
ssr = sp.simplify(sst - sse)
r_squared = sp.simplify(ssr / sst)
```

## Python 代码片段：模块10 F 检验
```python
import sympy as sp

f_statistic = sp.simplify((ssr / model_df) / (sse / residual_df))
f_residual = sp.simplify(f_statistic - reported_f)
```

## Python 代码片段：模块11 预测区间
```python
import sympy as sp

prediction_variance = sp.simplify(sigma2_hat * (1 + new_row.T * (design.T * design).inv() * new_row)[0])
prediction_interval = (prediction - critical_value * sp.sqrt(prediction_variance),
                       prediction + critical_value * sp.sqrt(prediction_variance))
```

## Python 代码片段：模块12 均值响应置信区间
```python
import sympy as sp

mean_response_variance = sp.simplify(sigma2_hat * (new_row.T * (design.T * design).inv() * new_row)[0])
mean_interval = (fitted_new - critical_value * sp.sqrt(mean_response_variance),
                 fitted_new + critical_value * sp.sqrt(mean_response_variance))
```

## Python 代码片段：模块13 多重共线性诊断（VIF）
```python
import sympy as sp

vif = sp.simplify(1 / (1 - auxiliary_r_squared))
gram_determinant = sp.factor(design.T * design).det()
```

## Python 代码片段：模块14 加权最小二乘
```python
import sympy as sp

W = sp.diag(*weights)
weighted_beta = (design.T * W * design).inv() * design.T * W * response
weighted_residual = sp.simplify(response - design * weighted_beta)
```

## Python 代码片段：模块15 Gauss--Markov 定理
```python
import sympy as sp

covariance_ols = sp.simplify(sigma2 * (design.T * design).inv())
covariance_gap = sp.simplify(covariance_alternative - covariance_ols)
```

## Python 代码片段：模块16 残差图分析与模型诊断
```python
import sympy as sp

residual_mean = sp.simplify(sum(residual) / residual.rows)
residual_sum = sp.simplify(sum(residual))
leverage_diagonal = [projection_matrix[i, i] for i in range(projection_matrix.rows)]
```

## Python 代码片段：模块17 偏 F 检验与变量选择
```python
import sympy as sp

partial_f = sp.simplify(((sse_reduced - sse_full) / added_parameters)
                        / (sse_full / residual_df_full))
```

## Python 代码片段：模块18 方差分析表与回归显著性
```python
import sympy as sp

ms_model = sp.simplify(ssr / model_df)
ms_error = sp.simplify(sse / residual_df)
anova_check = sp.simplify(ms_model / ms_error - f_statistic)
```

## Python 代码片段：模块19 自相关诊断（Durbin--Watson）
```python
import sympy as sp

durbin_watson = sp.simplify(sum((residual[i] - residual[i - 1]) ** 2
                                for i in range(1, residual.rows)) / sse)
```

## Python 代码片段：模块20 模型选择准则（AIC/BIC）
```python
import sympy as sp

aic = sp.simplify(sample_size * sp.log(sse / sample_size) + 2 * parameter_count)
bic = sp.simplify(sample_size * sp.log(sse / sample_size) + parameter_count * sp.log(sample_size))
```
