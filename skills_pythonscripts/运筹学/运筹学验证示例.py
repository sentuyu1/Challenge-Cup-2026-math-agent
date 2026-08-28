# 运筹学：验证提示词与知识点索引
运行环境：conda activate Competition
文件性质：这是数学智能体的验证知识说明，包含可摘取的 Python/SciPy 片段，不是可直接运行的完整优化器或搜索程序。

## 使用规则
- 先明确决策变量、目标方向、全部约束、变量域和单位；可行性、最优性和完整方案必须分别验证。
- 纯组合图论证明或组合博弈转离散数学；统计回归和假设检验转线性回归或统计推断。
- 题面没有成本、容量、需求、服务率等数据时，保留符号模型并说明缺失字段，不自行假设。

## 知识点 1：线性规划、单纯形与对偶
- 图解法检查所有顶点和无界/不可行情形；单纯形法保持同一检验数符号约定。
- 构造对偶时匹配原问题的目标方向、约束方向和变量符号；强对偶可用相等目标值验证最优性。
- 互补松弛需要原、对偶均可行，不能只检查一边。

## 知识点 2：运输、整数与非线性规划
- 运输问题先核对供需平衡、所有行列和和基变量数；初始可行解不是最优解，仍要用位势/闭回路检验。
- 整数规划必须保持整数约束；分支定界给出界、分支和终止理由。
- KKT 条件写出拉格朗日函数、可行性、互补松弛和驻点；充分性还需凸性等条件。

## 知识点 3：动态规划与网络
- 动态规划定义阶段、状态、决策、边界和 Bellman 递推，防止漏掉可行状态。
- 最短路、最大流分别核对路径长度/残量网络和割；最大流最小割用于最优性证明。

## 知识点 4：排队、库存、调度与决策
- 排队模型先明确到达/服务分布和稳定条件；库存模型给出需求、订货/持有成本及边界条件。
- 调度/资源分配题列出每项任务或资源的完整方案与总成本，不能只报最小目标值。
- 运筹博弈与纯组合博弈区分：前者有优化目标、约束或资源配置，后者通常归离散数学。

## Python 代码片段：线性规划求解与可行性回验
```python
import numpy as np
from scipy.optimize import linprog

# c、A_ub、b_ub、A_eq、b_eq 和 bounds 均从题面建模得到。
result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
if not result.success:
    raise ValueError(result.message)
solution = result.x
objective_value = result.fun
inequality_slack = np.asarray(b_ub) - np.asarray(A_ub) @ solution
equality_residual = np.asarray(A_eq) @ solution - np.asarray(b_eq)
```

## Python 代码片段：对偶值与互补松弛
```python
import sympy as sp

# primal_x、dual_y 及矩阵 A,b,c 均由题面或独立求解得到。
primal_value = sp.simplify((c.T * primal_x)[0])
dual_value = sp.simplify((b.T * dual_y)[0])
duality_gap = sp.simplify(primal_value - dual_value)
primal_slack = b - A * primal_x
complementary_products = [sp.simplify(dual_y[i] * primal_slack[i]) for i in range(primal_slack.rows)]
```

## Python 代码片段：运输方案的供需与成本核验
```python
import sympy as sp

allocation = sp.Matrix(allocation_matrix)
cost = sp.Matrix(cost_matrix)
row_totals = [sum(allocation.row(i)) for i in range(allocation.rows)]
column_totals = [sum(allocation.col(j)) for j in range(allocation.cols)]
total_cost = sp.simplify(sum(allocation[i, j] * cost[i, j] for i in range(allocation.rows) for j in range(allocation.cols)))
supply_check = [sp.simplify(row_totals[i] - supply[i]) for i in range(allocation.rows)]
demand_check = [sp.simplify(column_totals[j] - demand[j]) for j in range(allocation.cols)]
```

## 输出契约
- 最终答案包含模型、可行解、全部约束核验、最优性依据和目标值；运输/分配题列出全部基变量或分配项。
- 不能因找到一个可行方案就宣布最优。
- 求解器输出必须经过原约束、对偶界或互补松弛回验；最终答案列出完整方案而不只报目标值。

## 模块级验证代码（与运筹学 skill 的 11 个模块对应）

## Python 代码片段：模块一 线性规划
```python
import numpy as np

primal_slack = np.asarray(b_ub) - np.asarray(A_ub) @ solution
feasible = np.all(primal_slack >= -tolerance) and np.allclose(np.asarray(A_eq) @ solution, b_eq)
```

## Python 代码片段：模块二 运输问题
```python
import numpy as np

row_residual = np.asarray(allocation).sum(axis=1) - np.asarray(supply)
column_residual = np.asarray(allocation).sum(axis=0) - np.asarray(demand)
transport_cost = np.sum(np.asarray(allocation) * np.asarray(cost_matrix))
```

## Python 代码片段：模块三 整数规划
```python
import numpy as np

integrality_gap = np.asarray(integer_solution) - np.rint(integer_solution)
integer_feasible = np.all(np.abs(integrality_gap) <= tolerance)
```

## Python 代码片段：模块四 非线性规划与 KKT
```python
import sympy as sp

lagrangian = objective + sum(multiplier[i] * constraint[i] for i in range(len(constraint)))
stationarity = [sp.diff(lagrangian, variable) for variable in variables]
complementarity = [sp.simplify(multiplier[i] * constraint[i]) for i in range(len(constraint))]
```

## Python 代码片段：模块五 动态规划
```python
import sympy as sp

bellman_gap = sp.simplify(value_function[state] -
                          min(stage_cost(state, action) + value_function[next_state(state, action)]
                              for action in actions[state]))
```

## Python 代码片段：模块六 图论与网络优化
```python
import networkx as nx

shortest_length = nx.shortest_path_length(network, source, target, weight="weight")
flow_value, flow = nx.maximum_flow(network, source, target)
cut_value, partition = nx.minimum_cut(network, source, target)
maxflow_mincut_gap = flow_value - cut_value
```

## Python 代码片段：模块七 排队论
```python
import sympy as sp

rho = sp.simplify(arrival_rate / service_rate)
stability_condition = sp.Lt(rho, 1)
mean_number = sp.simplify(rho / (1 - rho))
```

## Python 代码片段：模块八 存储论
```python
import sympy as sp

total_inventory_cost = sp.simplify(order_cost * demand / order_quantity
                                   + holding_cost * order_quantity / 2)
economic_order_quantity = sp.solve(sp.Eq(sp.diff(total_inventory_cost, order_quantity), 0),
                                   order_quantity)
```

## Python 代码片段：模块九 博弈论
```python
import sympy as sp

payoff_matrix = sp.Matrix(payoff_entries)
row_best_responses = [max(row) for row in payoff_matrix.tolist()]
column_best_responses = [max(payoff_matrix[:, j]) for j in range(payoff_matrix.cols)]
```

## Python 代码片段：模块十 决策论
```python
import sympy as sp

expected_utilities = [sp.simplify(sum(probability[s] * utility[action][s] for s in states))
                      for action in actions]
best_action = actions[expected_utilities.index(max(expected_utilities))]
```

## Python 代码片段：模块十一 单循环赛程最优调度
```python
import itertools

matches = list(itertools.combinations(teams, 2))
round_count = max(len(teams) - 1, 1)
schedule_count = len(matches)
schedule_feasible = schedule_count == len(teams) * (len(teams) - 1) // 2
```

## Python 代码片段：竞赛拓展——分割选择博弈
```python
from itertools import combinations

partition_values = [sum(partition[i] for i in subset) for subset in combinations(range(len(partition)), split_size)]
balanced_gap = min(abs(total - 2 * value) for value in partition_values)
```
