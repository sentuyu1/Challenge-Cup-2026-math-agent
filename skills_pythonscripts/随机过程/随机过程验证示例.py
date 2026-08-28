# 随机过程：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是数学智能体的说明型提示资料，包含可摘取的 Python/SymPy 片段，不是可直接运行的完整随机模拟或数值程序。

## 使用规则
- 首先确定状态空间、时间指标、初始分布、转移/强度和停时；题面从 $t=1$ 还是 $t=0$ 计时必须保留。
- 静态随机变量分布转概率论；描述统计、趋势、季节调整等观测时间序列转统计推断。
- 过程结论用转移方程、独立增量、马尔可夫性或鞅条件核验，不用少量模拟轨迹代替证明。

## 知识点 1：离散时间 Markov 链
- 转移矩阵每行非负且和为 $1$；$n$ 步转移使用 $P^n$。
- 平稳分布满足 $\pi P=\pi$ 和 $\sum\pi_i=1$；极限分布还需要不可约、非周期、正再生等条件。
- 吸收概率和期望吸收时间从瞬态/吸收块分解或首步分析得到；周期性由可返回步数的最大公因数定义。

## 知识点 2：Poisson、生灭与排队过程
- Poisson 过程用独立平稳增量，$N(t)\sim\operatorname{Poisson}(\lambda t)$；等待时间为指数/Gamma 分布。
- 复合 Poisson 过程的期望和方差要同时包含跳跃大小的二阶矩。
- 生灭过程、M/M/1 队列先检查到达/服务率与稳定条件 $\rho<1$。

## 知识点 3：随机游走、Brownian 与更新
- 随机游走的首达、赌徒破产和停时要核对边界与可积性。
- Brownian 运动具连续路径、独立正态增量及协方差 $\min(s,t)$；反射原理有明确适用事件。
- 更新定理要说明更新间隔独立同分布和期望有限。

## 知识点 4：鞅与停时
- 先验证适应性、可积性及 $E(M_{n+1}\mid\mathcal F_n)=M_n$。
- 可选停时定理不是无条件成立，必须检查有界停时或一致可积等条件。

## Python 代码片段：Markov 链的平稳分布与转移核验
```python
import sympy as sp

P = sp.Matrix(transition_matrix)  # 行随机矩阵必须由题面给出
pi_symbols = sp.symbols(f"p0:{P.rows}")
pi = sp.Matrix(1, P.rows, pi_symbols)
equations = list((pi * P - pi)) + [sum(pi_symbols) - 1]
stationary_solutions = sp.solve(equations, pi_symbols, dict=True)
row_sum_checks = [sp.simplify(sum(P.row(index)) - 1) for index in range(P.rows)]
```

## Python 代码片段：Poisson 过程与等待时间
```python
import sympy as sp

k, rate, time = sp.symbols("k rate time", integer=True, nonnegative=True)
# rate、time、事件个数均由题面给出，且 rate > 0。
poisson_mass = sp.exp(-rate * time) * (rate * time) ** k / sp.factorial(k)
waiting_cdf = 1 - sp.exp(-rate * time)
increment_mean = rate * time
increment_variance = rate * time
```

## Python 代码片段：吸收链与首步方程
```python
import sympy as sp

# Q 为瞬态到瞬态子矩阵，R 为瞬态到吸收态子矩阵；块分解由题面状态顺序确定。
Q = sp.Matrix(transient_block)
R = sp.Matrix(absorbing_block)
fundamental_matrix = (sp.eye(Q.rows) - Q).inv()
absorption_probabilities = fundamental_matrix * R
expected_steps = fundamental_matrix * sp.ones(Q.rows, 1)
```

## 输出契约
- 答案明确时间起点、状态/吸收条件、参数、所用性质和目标概率/期望。
- 题面没有初始分布或边界时，保留为参数或说明无法给唯一数值。
- 代码只辅助检查转移矩阵、首步方程或分布公式；不可约性、周期性和停时定理前提仍需在文字中证明。

## 模块级验证代码（与随机过程 skill 的 10 个模块对应）

## Python 代码片段：模块1 离散时间 Markov 链基础
```python
import sympy as sp

P = sp.Matrix(transition_matrix)
row_sums = [sp.simplify(sum(P.row(i)) - 1) for i in range(P.rows)]
n_step_kernel = P ** step_count
```

## Python 代码片段：模块2 Markov 链吸收概率
```python
import sympy as sp

Q = sp.Matrix(transient_block)
R = sp.Matrix(absorbing_block)
fundamental = (sp.eye(Q.rows) - Q).inv()
absorption = fundamental * R
```

## Python 代码片段：模块3 Poisson 过程
```python
import sympy as sp

k, rate, time = sp.symbols("k rate time", integer=True, nonnegative=True)
count_probability = sp.exp(-rate * time) * (rate * time) ** k / sp.factorial(k)
increment_check = sp.simplify(sp.diff(count_probability, time))
```

## Python 代码片段：模块4 复合 Poisson 过程
```python
import sympy as sp

compound_mean = sp.simplify(rate * time * jump_mean)
compound_variance = sp.simplify(rate * time * (jump_variance + jump_mean ** 2))
```

## Python 代码片段：模块5 生灭过程与排队论
```python
import sympy as sp

rho = sp.simplify(arrival_rate / service_rate)
stationary_queue = sp.simplify((1 - rho) * rho ** queue_length)
stable = sp.Lt(rho, 1)
```

## Python 代码片段：模块6 Brownian 运动
```python
import sympy as sp

s, t = sp.symbols("s t", nonnegative=True)
covariance = sp.Min(s, t)
increment_variance = sp.simplify(covariance.subs({s: t + delta, t: t + delta})
                                  - 2 * covariance + covariance.subs({s: t, t: t}))
```

## Python 代码片段：模块7 随机游走
```python
import sympy as sp

position_mean = sp.simplify(step_count * (2 * up_probability - 1))
position_variance = sp.simplify(4 * step_count * up_probability * (1 - up_probability))
```

## Python 代码片段：模块8 更新过程
```python
import sympy as sp

renewal_mean = sp.simplify(time / interarrival_mean)
renewal_residual = sp.simplify(renewal_count * interarrival_mean - time)
```

## Python 代码片段：模块9 指数分布与次序统计量
```python
import sympy as sp

x = sp.symbols("x", nonnegative=True)
minimum_cdf = 1 - sp.exp(-sample_size * rate * x)
order_stat_density = sp.simplify(order_factor * cdf_base ** (order_index - 1)
                                  * (1 - cdf_base) ** (sample_size - order_index) * density_base)
```

## Python 代码片段：模块10 鞅与停时
```python
import sympy as sp

conditional_drift = sp.simplify(conditional_expectation_next - current_value)
optional_stopping_gap = sp.simplify(expected_stopped_value - expected_initial_value)
```

## Python 代码片段：竞赛拓展——完全图随机游动覆盖时间
```python
import sympy as sp

cover_time_bound = sp.simplify((vertices - 1) * sp.log(vertices))
coupon_gap = sp.simplify(expected_cover_time - cover_time_bound)
```
