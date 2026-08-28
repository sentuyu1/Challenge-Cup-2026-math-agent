---
name: stochastic-processes-verification
description: Use when verifying stochastic processes problems — Markov chains, Poisson processes, Brownian motion, birth-death processes, renewal processes, martingales, and queueing theory
---

# 随机过程解题与验证技能手册

## 领域边界与路由约定

- 适用范围：Markov 链、Poisson 过程、Brownian 运动、生灭/更新过程、鞅、停时和覆盖时间。
- 不接管：静态分布与概率计算转概率论；时间序列观测数据、趋势和季节调整转统计推断。
- 验证契约：明确离散步数与时间编号（若题面从 $t=1$ 计时要保留额外 $+1$），并检查停时/状态空间条件。

## 时间序列兼容口径

经典时间序列分解包含长期趋势 $T$、季节变动 $S$、循环变动 $C$ 和不规则项 $I$；“随机变动”通常是对不规则项的同义描述，不应重复计数。弱平稳要求均值、方差恒定且协方差只依赖滞后；白噪声还要求不同期不相关。季节调整常用移动平均比率法和 X-11/X-13。
- **时间数列指标类型（判分口径）**：「两个总量指标时间数列相比照得到的时间数列**一定**是相对数时间数列」是**错误**命题——反例：工资总额（总量）÷职工人数（总量）=平均工资，得到的是**平均数时间数列**而非相对数时间数列；带「一定」的绝对化表述即判错。判断类最终答案 \boxed{错误}。

## 概述

本技能手册覆盖本科随机过程课程的核心知识体系，包括离散时间Markov链（转移矩阵、平稳分布、周期性、极限分布、吸收概率）、Poisson过程（基本概率、非齐次、独立叠加、等待时间分布）、复合Poisson过程（期望与方差）、生灭过程与M/M/1排队论、Brownian运动（协方差、鞅性质、首达时、反射原理）、随机游走、更新过程（初等更新定理）、指数分布与次序统计量、以及鞅与停时（Doob有界停时定理）等经典内容。全手册以20道精选习题为骨架，系统梳理每个知识模块的核心概念、常用定理、解题步骤和常见陷阱，并配套验证知识提示，适用于随机过程课程的学习、复习与自动解题验证。

---

## 知识点体系

### 模块1：离散时间Markov链基础

#### 核心概念

- **Markov链**：$\{X_n, n = 0,1,2,\ldots\}$ 是状态空间 $S$ 上的离散时间Markov链（DTMC），若对任意 $n$ 和任意状态 $i_0, \ldots, i_{n-1}, i, j \in S$，有 $P(X_{n+1}=j \mid X_n=i, X_{n-1}=i_{n-1},\ldots,X_0=i_0) = P(X_{n+1}=j \mid X_n=i)$。
- **时齐转移概率**：$p_{ij} = P(X_{n+1}=j \mid X_n=i)$，与 $n$ 无关。
- **转移概率矩阵**：$P = [p_{ij}]_{i,j \in S}$，每一行之和为 $1$。
- **$n$ 步转移概率**：$p_{ij}^{(n)} = P(X_n = j \mid X_0 = i) = [P^n]_{ij}$（Chapman-Kolmogorov方程保证）。
- **平稳分布**：非负行向量 $\pi = (\pi_i)_{i \in S}$ 满足 $\pi = \pi P$ 且 $\sum_i \pi_i = 1$。
- **Chapman-Kolmogorov方程**（C-K方程）：
  $$p_{ij}^{(m+n)} = \sum_{k} p_{ik}^{(m)} p_{kj}^{(n)}$$
  矩阵形式：$P^{(m+n)} = P^{(m)} P^{(n)}$。

#### 常用公式

1. **平稳分布方程**：
   $$\pi_j = \sum_{i} \pi_i p_{ij} \quad (\forall j),\qquad \sum_{j} \pi_j = 1$$
   矩阵形式：$\pi P = \pi$，$\pi \mathbf{1} = 1$。

2. **二状态转移矩阵平稳分布**：
   对 $P = \begin{pmatrix} 1-a & a \\ b & 1-b \end{pmatrix}$（$a,b \in (0,1]$），平稳分布为 $\pi = \left(\frac{b}{a+b}, \frac{a}{a+b}\right)$。

3. **周期（period）**：状态 $i$ 的周期 $d(i) = \gcd\{n \geq 1 : p_{ii}^{(n)} > 0\}$。若所有状态具有相同周期 $d$，称该链具有周期 $d$。

4. **极限分布存在条件**：不可约、非周期（遍历）、正常返的Markov链有唯一的极限分布 $\lim_{n\to\infty} p_{ij}^{(n)} = \pi_j$（与 $i$ 无关），且极限分布即为平稳分布。

#### 解题步骤

**求平稳分布：**
1. 写出方程 $\pi P = \pi$，即对每个 $j$ 有 $\pi_j = \sum_i \pi_i p_{ij}$。
2. 添加归一化条件 $\sum_i \pi_i = 1$，消去一个冗余方程。
3. 解线性方程组（对有限状态可直接求解，对生灭过程可用细致平衡）。

**判断极限分布是否存在：**
1. 检查不可约性（所有状态相互可达）。
2. 检查周期性（任一状态有自环即非周期）。
3. 若不可约且非周期，极限分布存在且等于平稳分布。
4. 若有周期 $d > 1$，则 $P^n$ 不收敛，极限分布不存在。

#### 对应习题

- **idx 0**: 二状态Markov链求平稳分布 — 解 $\pi P = \pi$，$\pi = (3/7, 4/7)$
- **idx 9**: 三状态矩阵周期判定与平稳分布 — 确定循环置换矩阵周期 $d=3$
- **idx 13**: 极限分布存在性与计算 — 验证不可约非周期，求极限分布 $(1/3,1/3,1/3)$
- **idx 15**: 证明Chapman-Kolmogorov方程 — 全概率公式 + Markov性 + 时齐性

---

### 模块2：Markov链吸收概率

#### 核心概念

- **吸收态**：状态 $i$ 满足 $p_{ii} = 1$（一旦进入永不离开）。
- **吸收Markov链**：状态空间可分为瞬态集合 $T$ 和吸收态集合 $A$。
- **吸收概率**：$a_i = P(\text{最终被某吸收态集合吸收} \mid X_0 = i)$。
- **基本矩阵（fundamental matrix）**：$N = (I - Q)^{-1}$，其中 $Q$ 为仅保留瞬态间的转移子矩阵。$N_{ij}$ 表示从状态 $i$ 出发访问状态 $j$ 的期望次数。

#### 常用公式

1. **吸收概率方程组**（从瞬态 $i$ 被吸收态集合 $A$ 吸收的概率）：
   $$a_i = \sum_{j \in A} p_{ij} + \sum_{k \in T} p_{ik} a_k \quad (i \in T)$$
   边界条件：$a_i = 1$（$i \in A$ 目标吸收态），$a_i = 0$（$i \in A$ 非目标吸收态）。

2. **矩阵形式**：令 $\mathbf{a} = (a_i)_{i \in T}$，则 $\mathbf{a} = \mathbf{r} + Q\mathbf{a}$，即 $\mathbf{a} = (I - Q)^{-1}\mathbf{r} = N\mathbf{r}$，其中 $\mathbf{r}_i = \sum_{j \in A_{\text{target}}} p_{ij}$。

#### 解题步骤

**求从瞬态出发被指定吸收态吸收的概率：**
1. 重新排列状态，将吸收态放在前面。
2. 对每个瞬态 $i$，列出吸收概率方程：$a_i = \sum_{j \in A} p_{ij} \cdot (\text{边界值}) + \sum_{k \in T} p_{ik} a_k$。
3. 设定边界条件（目标吸收态概率为 $1$，其余吸收态为 $0$）。
4. 解线性方程组得到各 $a_i$。

#### 对应习题

- **idx 3**: 四状态Markov链吸收概率 — 建立方程组求解，从状态2被状态3吸收的概率为 $2/5$

---

### 模块3：Poisson过程

#### 核心概念

- **Poisson过程（齐次）**：计数过程 $\{N(t), t \geq 0\}$ 满足：(1) $N(0) = 0$；(2) 独立增量；(3) 在任意长度为 $s$ 的区间内的事件数服从参数为 $\lambda s$ 的Poisson分布，即 $P(N(t+s) - N(t) = k) = e^{-\lambda s} \frac{(\lambda s)^k}{k!}$。
- **到达间隔时间**：$T_i$ 为第 $i-1$ 到第 $i$ 个事件的间隔，$T_i \sim \text{Exp}(\lambda)$ i.i.d.。
- **等待时间（第 $n$ 个事件的时间）**：$W_n = T_1 + T_2 + \cdots + T_n \sim \text{Gamma}(n, \lambda)$。
- **非齐次Poisson过程**：强度函数 $\lambda(t)$（时间依赖），均值函数 $\Lambda(t) = \int_0^t \lambda(s)\,ds$。$N(t) \sim \text{Poisson}(\Lambda(t))$。
- **Poisson过程叠加**：两个独立Poisson过程 $N_1(t) \sim \text{PP}(\lambda_1)$，$N_2(t) \sim \text{PP}(\lambda_2)$，则 $N_1(t) + N_2(t) \sim \text{PP}(\lambda_1 + \lambda_2)$。

#### 常用公式

1. **Poisson PMF**：
   $$P(N(t) = k) = e^{-\lambda t} \frac{(\lambda t)^k}{k!}, \quad k = 0, 1, 2, \ldots$$

2. **Poisson过程期望与方差**：
   $$E[N(t)] = \lambda t, \quad \operatorname{Var}(N(t)) = \lambda t$$

3. **非齐次Poisson的分布**：
   $$N(t) \sim \text{Poisson}\left(\Lambda(t)\right), \quad \Lambda(t) = \int_0^t \lambda(s)\,ds$$

4. **非齐次Poisson的增量分布**：
   $$N(t) - N(s) \sim \text{Poisson}\left(\Lambda(t) - \Lambda(s)\right), \quad \Lambda(t) - \Lambda(s) = \int_s^t \lambda(u)\,du$$

5. **等待时间 $W_n$ 的分布**：
   $$f_{W_n}(t) = \frac{\lambda^n t^{\,n-1} e^{-\lambda t}}{(n-1)!}, \quad t > 0$$

6. **独立Poisson过程的叠加**：
   $$N_1(t) + N_2(t) \sim \text{PP}(\lambda_1 + \lambda_2)$$

#### 解题步骤

**计算齐次Poisson概率：**
1. 确定参数 $\lambda$ 和时间区间长度 $t$。
2. 确定所需的 $k$ 值。
3. 代入公式 $P(N(t) = k) = e^{-\lambda t} (\lambda t)^k / k!$。

**处理非齐次Poisson过程：**
1. 计算均值函数 $\Lambda(t) = \int_0^t \lambda(s)\,ds$。
2. 利用 $N(t) \sim \text{Poisson}(\Lambda(t))$ 将问题转化为标准Poisson概率。

**求等待时间分布：**
1. 利用 $W_n = T_1 + \cdots + T_n$，其中 $T_i \sim \text{Exp}(\lambda)$ i.i.d.。
2. 使用特征函数或矩母函数法：$n$ 个独立 $\text{Exp}(\lambda)$ 之和的特征函数为 $(\frac{\lambda}{\lambda - it})^n$，识别为 $\text{Gamma}(n, \lambda)$。

#### 对应习题

- **idx 2**: Poisson过程基本概率 — $P(N(1)=3) = \frac{4}{3}e^{-2}$，$P(N(2) \geq 1) = 1-e^{-4}$
- **idx 10**: 非齐次Poisson过程 — $\lambda(t) = 2t$，$E[N(3)] = 9$，$P(N(2)-N(1)=0) = e^{-3}$
- **idx 11**: 独立Poisson过程叠加 — $N_1+N_2 \sim \text{Poisson}(5)$
- **idx 17**: 证明Poisson过程等待时间分布 — $W_n \sim \text{Gamma}(n,\lambda)$

---

### 模块4：复合Poisson过程

#### 核心概念

- **复合Poisson过程**：$S(t) = \sum_{k=1}^{N(t)} X_k$，其中 $\{N(t)\}$ 是参数 $\lambda$ 的Poisson过程，$\{X_k\}$ 是 i.i.d. 随机变量（独立于 $N(t)$），$X_k$ 表示第 $k$ 个事件的"报酬/金额"。
- **应用场景**：保险理赔总额、商店总销售额、股票价格的跳跃部分等。

#### 常用公式

1. **期望**：
   $$E[S(t)] = E[N(t)] \cdot E[X] = \lambda t \cdot E[X]$$

2. **方差**：
   $$\operatorname{Var}(S(t)) = E[N(t)] \cdot E[X^2] = \lambda t \cdot E[X^2]$$

3. **二阶矩分解**：
   $$\operatorname{Var}(S(t)) = \lambda t \cdot (\operatorname{Var}(X) + (E[X])^2)$$

#### 解题步骤

1. 识别Poisson过程参数 $\lambda$ 和单次报酬分布 $X$。
2. 计算 $E[X]$ 和 $E[X^2] = \operatorname{Var}(X) + (E[X])^2$。
3. 代入公式 $E[S(t)] = \lambda t \cdot E[X]$。
4. 代入公式 $\operatorname{Var}(S(t)) = \lambda t \cdot E[X^2]$。
5. 注意：$\operatorname{Cov}(S(s), S(t)) = \lambda \min(s,t) \cdot E[X^2]$（若需协方差）。

#### 对应习题

- **idx 6**: 复合Poisson期望与方差 — $E[S(4)]=400$，$\operatorname{Var}(S(4))=8320$

---

### 模块5：生灭过程与排队论

#### 核心概念

- **连续时间Markov链（CTMC）**：状态间的转移服从指数分布，由转移速率矩阵 $Q$（生成元矩阵）描述。
- **生灭过程**：CTMC的特殊形式，状态变化只能是相邻状态（$i \to i+1$ 或 $i \to i-1$）。定义出生率 $\lambda_i$（从 $i$ 到 $i+1$ 的速率）和死亡率 $\mu_i$（从 $i$ 到 $i-1$ 的速率，$\mu_0 = 0$）。
- **平稳分布**：$\pi Q = 0$，$\sum \pi_i = 1$。
- **细致平衡（detailed balance）**：$\pi_i \lambda_i = \pi_{i+1} \mu_{i+1}$（对于生灭过程必然成立）。
- **M/M/1排队系统**：顾客到达为 $\text{PP}(\lambda)$，服务时间 $\sim \text{Exp}(\mu)$，单个服务器。交通强度 $\rho = \lambda / \mu$。
- **M/M/1的平稳队长分布**：若 $\rho < 1$，$\pi_n = (1-\rho)\rho^n$（$n = 0, 1, 2, \ldots$）。

#### 常用公式

1. **生灭过程平稳分布**（由细致平衡）：
   $$\pi_n = \pi_0 \prod_{k=0}^{n-1} \frac{\lambda_k}{\mu_{k+1}}, \quad \pi_0 = \left(1 + \sum_{n=1}^{\infty} \prod_{k=0}^{n-1} \frac{\lambda_k}{\mu_{k+1}}\right)^{-1}$$

2. **M/M/1关键量**：
   - 平稳队长：$\pi_n = (1-\rho)\rho^n$，$\rho = \lambda / \mu < 1$
   - 平均队长：$L = E[N] = \frac{\rho}{1-\rho}$
   - 平均等待时间（Little定律）：$W = L / \lambda = \frac{1}{\mu - \lambda}$

3. **有限状态生灭过程的平稳分布**：直接利用细致平衡递推 $\pi_{i+1} = \frac{\lambda_i}{\mu_{i+1}} \pi_i$，最后归一化。

#### 解题步骤

**求生灭过程平稳分布：**
1. 列出所有出生率 $\lambda_i$ 和死亡率 $\mu_i$。
2. 利用细致平衡：$\pi_i \lambda_i = \pi_{i+1} \mu_{i+1}$，即 $\pi_{i+1} = (\lambda_i / \mu_{i+1}) \pi_i$。
3. 逐个递推得到所有 $\pi_i$ 用 $\pi_0$ 表示的表达式。
4. 利用归一化条件 $\sum \pi_i = 1$ 求出 $\pi_0$，进而求出全部 $\pi_i$。

**M/M/1排队系统分析：**
1. 判定 $\rho = \lambda / \mu < 1$ 为平稳条件。
2. 由细致平衡 $\lambda \pi_n = \mu \pi_{n+1}$ 得 $\pi_{n} = \rho^n \pi_0$。
3. 归一化：$\pi_0 \sum_{n=0}^{\infty} \rho^n = \pi_0 / (1-\rho) = 1$，故 $\pi_0 = 1 - \rho$。

#### 对应习题

- **idx 4**: 三状态生灭过程平稳分布 — 细致平衡递推，$\pi = (8/23, 12/23, 3/23)$
- **idx 16**: 证明M/M/1排队平稳分布 $\pi_n = (1-\rho)\rho^n$ — 细致平衡 + 归一化

---

### 模块6：Brownian运动

#### 核心概念

- **标准Brownian运动（Wiener过程）**：$\{B(t), t \geq 0\}$ 满足：(1) $B(0) = 0$；(2) 独立增量；(3) 对 $0 \leq s < t$，$B(t) - B(s) \sim N(0, t-s)$；(4) 样本路径连续（a.s.）。
- **协方差函数**：$\operatorname{Cov}(B(s), B(t)) = \min(s, t)$（对所有 $s, t \geq 0$）。
- **鞅性质**：$B(t)$ 关于其自然滤子 $\{\mathcal{F}_t\}$ 是鞅，即 $E[B(t) \mid \mathcal{F}_s] = B(s)$（$s < t$）。
- **首达时（hitting time）**：$T_a = \inf\{t \geq 0 : B(t) = a\}$（$a > 0$）。
- **双边界首达时**：$T = \min(T_a, T_{-b})$，其中 $a, b > 0$。
- **反射原理**：首达 $a$ 后将路径关于直线 $y=a$ 反射，反射后的路径仍是标准Brownian运动。

#### 常用公式

1. **协方差**：
   $$\operatorname{Cov}(B(s), B(t)) = \min(s, t)$$

2. **方差**：
   $$\operatorname{Var}(B(t)) = t$$

3. **增量独立性**：$B(t) - B(s) \perp B(u)$ 对所有 $u \leq s < t$。

4. **首达时概率**（单边界）：
   $$P(T_a \leq t) = 2P(B(t) \geq a) = 2\left(1 - \Phi\left(\frac{a}{\sqrt{t}}\right)\right)$$

5. **首达时密度**：
   $$f_{T_a}(t) = \frac{a}{\sqrt{2\pi t^3}} e^{-a^2/(2t)}, \quad t > 0$$

6. **双边界问题**：
   $$P(T_a < T_{-b}) = \frac{b}{a+b}$$
   $$E[\min(T_a, T_{-b})] = ab$$

#### 解题步骤

**计算Brownian运动的协方差：**
1. 将含 $B(t)$ 的线性组合写出来。
2. 利用 $\operatorname{Cov}(B(s), B(t)) = \min(s, t)$ 展开。
3. 利用增量独立性简化组合的方差。

**首达时问题：**
1. 对称情况（$a = b$）：$P(T_a < T_{-a}) = 1/2$，$E[T] = a^2$。
2. 非对称情况：$P(T_a < T_{-b}) = b/(a+b)$，$E[\min(T_a, T_{-b})] = ab$。

**证明鞅性质：**
1. 将 $B(t)$ 分解为 $B(t) = (B(t)-B(s)) + B(s)$。
2. 取条件期望：$E[B(t) \mid \mathcal{F}_s] = E[B(t)-B(s) \mid \mathcal{F}_s] + B(s)$。
3. 由独立增量性质，$B(t)-B(s)$ 独立于 $\mathcal{F}_s$ 且期望为 $0$，故 $E[B(t) \mid \mathcal{F}_s] = B(s)$。

#### 对应习题

- **idx 7**: Brownian运动协方差与方差 — $\operatorname{Cov}(B(1)+B(2), B(3)) = 3$，$\operatorname{Var}(B(2)-B(1)) = 1$
- **idx 12**: Brownian运动双边界首达时 — $P(T_1 < T_{-1}) = 1/2$，$E[T] = 1$
- **idx 14**: 证明Brownian运动是鞅 — 独立增量 + 零期望增量
- **idx 19**: 证明反射原理 — 反射路径同分布 + 概率分解

---

### 模块7：随机游走

#### 核心概念

- **简单对称随机游走**：$S_0 = 0$，$S_n = \sum_{k=1}^n X_k$，其中 $X_k$ 独立同分布，$P(X_k = 1) = P(X_k = -1) = 1/2$。
- **位置与步数的关系**：若在 $n$ 步中向上走了 $k$ 步（向下 $n-k$ 步），则 $S_n = k - (n-k) = 2k - n$。
- **位置概率**：向上步数 $K \sim \text{Binomial}(n, 1/2)$，故：
  $$P(S_n = m) = \binom{n}{\frac{n+m}{2}} \left(\frac{1}{2}\right)^n$$
  当且仅当 $n+m$ 为偶数且 $|m| \leq n$ 时非零。

#### 常用公式

1. **二项分布概率**：
   $$P(S_n = m) = C\left(n, \frac{n+m}{2}\right) \cdot \left(\frac{1}{2}\right)^n$$

2. **期望与方差**：
   $$E[S_n] = 0, \quad \operatorname{Var}(S_n) = n$$

#### 解题步骤

1. 由所需 $S_n = m$ 反解向上步数 $k = (n+m)/2$。
2. 验证 $k$ 为整数且在 $[0, n]$ 范围内。
3. 计算二项概率 $\binom{n}{k} \cdot (1/2)^n$。

#### 对应习题

- **idx 1**: 简单对称随机游走位置概率 — $P(S_6=0) = 5/16$，$P(S_6=2) = 15/64$

---

### 模块8：更新过程

#### 核心概念

- **更新过程**：考虑一个无限序列的独立同分布非负随机变量 $\{X_1, X_2, \ldots\}$（到达间隔时间），定义 $S_0 = 0$，$S_n = \sum_{i=1}^n X_i$。令 $N(t) = \max\{n : S_n \leq t\}$ 为到时刻 $t$ 为止的更新次数。
- **更新函数**：$m(t) = E[N(t)]$，表示到时刻 $t$ 的期望更新次数。
- **初等更新定理**：
  $$\lim_{t \to \infty} \frac{m(t)}{t} = \frac{1}{\mu}$$
  其中 $\mu = E[X_1]$ 为平均到达间隔时间。
- **长期平均更新率**：$1 / \mu$。

#### 常用公式

1. **初等更新定理**：
   $$\lim_{t \to \infty} \frac{E[N(t)]}{t} = \frac{1}{E[X_1]} = \frac{1}{\mu}$$

2. **长期平均更新率**：
   $$\text{长期更新率} = \frac{1}{\mu}$$

3. **大 $t$ 近似**：
   $$E[N(t)] \approx \frac{t}{\mu} \quad (\text{当 } t \text{ 足够大时})$$

#### 解题步骤

1. 识别到达间隔时间 $X_i$ 的分布，计算其均值 $\mu = E[X_1]$。
2. 长期平均更新率 $= 1/\mu$。
3. 用初等更新定理近似给定时间 $t$ 内的期望更新次数：$E[N(t)] \approx t/\mu$。

#### 对应习题

- **idx 8**: 灯泡更换更新过程 — 平均更换率 $=1$ 次/年（寿命 $U(0,2)$，均值为 $1$ 年）

---

### 模块9：指数分布与次序统计量

#### 核心概念

- **指数分布**：$T \sim \text{Exp}(\lambda)$，密度 $f(t) = \lambda e^{-\lambda t}$（$t > 0$），$E[T] = 1/\lambda$，$\operatorname{Var}(T) = 1/\lambda^2$。
- **无记忆性**：$P(T > s+t \mid T > s) = P(T > t) = e^{-\lambda t}$。
- **独立指数分布的最小值**：若 $X_i \sim \text{Exp}(\lambda_i)$ 独立，则：
  $$T = \min(X_1, \ldots, X_n) \sim \text{Exp}\left(\sum_{i=1}^n \lambda_i\right)$$

#### 常用公式

1. **指数分布最小值**：
   $$T = \min(X_1, \ldots, X_n) \sim \text{Exp}(\lambda_1 + \cdots + \lambda_n)$$
   $$E[T] = \frac{1}{\sum_{i=1}^n \lambda_i}, \quad P(T > t) = e^{-(\sum \lambda_i) t}$$

2. **同参数指数分布（$\lambda_i = \lambda$）的最小值**：
   $$\min(X_1, \ldots, X_n) \sim \text{Exp}(n\lambda)$$

#### 解题步骤

1. 确认各随机变量独立且均服从指数分布。
2. 利用最小值分布公式 $T = \min(X_i) \sim \text{Exp}(\sum \lambda_i)$。
3. 计算期望 $E[T] = 1/(\sum \lambda_i)$ 和生存函数 $P(T > t) = e^{-(\sum \lambda_i) t}$。

#### 对应习题

- **idx 5**: 独立指数分布最小值 — $E[T] = 1/3$ 年，$P(T > 1) = e^{-3}$

---

### 模块10：鞅与停时

#### 核心概念

- **鞅（martingale）**：$\{M_n, n \geq 0\}$ 若满足 $E[|M_n|] < \infty$ 且 $E[M_{n+1} \mid \mathcal{F}_n] = M_n$ a.s.，则称其为关于滤子 $\{\mathcal{F}_n\}$ 的鞅。
- **停时（stopping time）**：取值于非负整数的随机变量 $T$，满足对任意 $n$，$\{T = n\} \in \mathcal{F}_n$。
- **Doob有界停时定理（可选停止定理）**：设 $\{M_n\}$ 是鞅，$T$ 是有界停时（存在常数 $K$ 使得 $T \leq K$ a.s.），则 $E[M_T] = E[M_0]$。
- **鞅的停时过程**：$M_{T \wedge n}$ 仍是鞅。

#### 常用公式

1. **停时过程的鞅表示**：
   $$M_{T \wedge n} = M_0 + \sum_{k=1}^{n} (M_k - M_{k-1}) \cdot \mathbf{1}_{\{T \geq k\}}$$

2. **关键引理**：$\mathbf{1}_{\{T \geq k\}} = 1 - \mathbf{1}_{\{T \leq k-1\}} \in \mathcal{F}_{k-1}$（由停时定义保证）。

3. **鞅差条件期望为零**：$E[(M_k - M_{k-1}) \cdot \mathbf{1}_{\{T \geq k\}} \mid \mathcal{F}_{k-1}] = \mathbf{1}_{\{T \geq k\}} \cdot E[M_k - M_{k-1} \mid \mathcal{F}_{k-1}] = 0$。

#### 解题步骤

**证明Doob有界停时定理：**
1. 写出 $M_{T \wedge n}$ 的鞅差表示。
2. 验证 $\mathbf{1}_{\{T \geq k\}}$ 关于 $\mathcal{F}_{k-1}$ 可测。
3. 利用鞅差性质证明 $M_{T \wedge n}$ 是鞅，从而 $E[M_{T \wedge n}] = E[M_0]$。
4. 利用停时 $T$ 的有界性（$T \leq K$），取 $n = K$ 得 $E[M_{T \wedge K}] = E[M_T] = E[M_0]$。

**证明Brownian运动是鞅：**
1. 分解 $B(t) = (B(t) - B(s)) + B(s)$。
2. 取条件期望 $E[B(t) \mid \mathcal{F}_s]$。
3. 利用独立增量性质：$B(t)-B(s) \perp \mathcal{F}_s$，且 $E[B(t)-B(s)] = 0$。
4. 得 $E[B(t) \mid \mathcal{F}_s] = B(s)$。

#### 对应习题

- **idx 14**: 证明Brownian运动是鞅 — 独立增量 + 条件期望
- **idx 18**: 证明Doob有界停时定理 — 鞅差表示 + 有界停时
- **idx 19**: 证明Brownian运动反射原理 — 反射不变性 + 概率分解

---

## 模块速查：通用解题方法论

### 1. 题型识别

拿到题目后首先判断：

| 题型特征 | 对应模块 |
|---------|---------|
| "转移概率矩阵" / "平稳分布" / "$\pi P = \pi$" | 模块1：离散时间Markov链基础 |
| "$p_{ij}^{(n)}$" / "C-K方程" / "Chapman-Kolmogorov" | 模块1：C-K方程 |
| "周期" / "极限分布" / "$P^n$ 是否收敛" | 模块1：周期性与极限 |
| "吸收态" / "被吸收的概率" / "吸收Markov链" | 模块2：Markov链吸收概率 |
| "Poisson过程" / "$N(t)$" / "$e^{-\lambda t}$" | 模块3：Poisson过程 |
| "非齐次Poisson" / "$\lambda(t)$" / "强度函数" | 模块3：非齐次Poisson |
| "$N_1+N_2$" / "叠加" / "独立Poisson过程之和" | 模块3：Poisson叠加 |
| "等待时间" / "$W_n$" / "Erlang" / "Gamma分布" | 模块3：等待时间分布 |
| "复合Poisson" / "$S(t)$" / "总销售额" / "复合" | 模块4：复合Poisson过程 |
| "生灭过程" / "出生率死亡率" / "细致平衡" | 模块5：生灭过程 |
| "M/M/1" / "排队" / "$\rho$" / "交通强度" | 模块5：M/M/1排队论 |
| "Brownian运动" / "$B(t)$" / "Wiener过程" | 模块6：Brownian运动 |
| "协方差" / "$\min(s,t)$" / "增量独立" | 模块6：Brownian协方差 |
| "首达时" / "$T_a$" / "hitting time" / "反射原理" | 模块6：首达时与反射原理 |
| "鞅" / "$E[M_T]$" / "martingale" | 模块6 + 模块10：鞅 |
| "随机游走" / "$S_n$" / "步数" / "二项分布" | 模块7：随机游走 |
| "更新过程" / "更新率" / "初等更新定理" | 模块8：更新过程 |
| "指数分布" / "$\min$" / "次序统计量" / "无记忆性" | 模块9：指数分布 |
| "Doob" / "停时" / "有界停时" / "可选停止" | 模块10：鞅与停时 |

### 2. 方法选择

| 问题类型 | 首选方法 | 备选方法 |
|---------|---------|---------|
| 求平稳分布 | 解 $\pi P = \pi$ 方程组 | 细致平衡（生灭过程） |
| 求吸收概率 | 建立吸收方程组 + 线性求解 | 基本矩阵 $N = (I-Q)^{-1}$ |
| 求Poisson概率 | 直接代入PMF公式 | N/A |
| 求非齐次Poisson | 先求 $\Lambda(t)$，再转化为标准Poisson | N/A |
| 求复合Poisson期望/方差 | Wald公式：$E[S]=E[N]E[X]$ | 条件期望 |
| 求Brownian协方差 | $\operatorname{Cov}(B(s),B(t)) = \min(s,t)$ | 增量独立性展开 |
| 求Brownian首达时 | 反射原理公式 / 鞅停时法 | 密度函数积分 |
| 求随机游走概率 | 转化为二项分布 | 递推/生成函数 |
| 求更新率 | $1/\mu$（初等更新定理） | 更新方程 |
| 求独立指数最小值 | 最小值分布 $T \sim \text{Exp}(\sum \lambda_i)$ | 生存函数相乘 |
| 判定周期 | 求状态 $i$ 回路的步数集合的gcd | 自环判定（若 $p_{ii} > 0$ 则 $d=1$） |
| 判定极限分布存在 | 不可约 + 非周期 + 有限状态 | 遍历性定理 |
| 证明鞅性质 | 直接条件期望展开 | 鞅变换/函数鞅 |
| 证明反射原理 | 反射路径同分布 + 概率分解 | Markov性强Markov性 |

### 3. 结果验证

- **平稳分布验证**：$\pi P = \pi$ 且 $\sum \pi_i = 1$。将解代回方程验证。
- **Poisson概率验证**：$\sum_{k=0}^{\infty} P(N(t)=k) = 1$（总概率为1）。
- **协方差验证**：正定性检查——对任意 $t_1, \ldots, t_n$，协方差矩阵应半正定。
- **吸收概率验证**：从吸收态出发的边界条件必须满足；所有瞬态出发的概率值应在 $[0,1]$ 内。
- **生灭过程平稳分布验证**：验证细致平衡方程 $\pi_i \lambda_i = \pi_{i+1} \mu_{i+1}$ 成立。
- **首达时概率验证**：$\lim_{t \to \infty} P(T_a \leq t) = 1$（迟早会到达）。
- **复合Poisson方差验证**：方差必须非负；$E[X^2] \geq (E[X])^2$ 自然满足。
- **sympy 独立验证**：对计算题结果用 sympy 独立验算（矩阵运算、符号积分、概率计算）。

---

## 模块速查：sympy验证技巧

### 转移矩阵与平稳分布

```python
from sympy import Matrix, symbols, solve, Rational

# 例：idx 0 - 二状态Markov链平稳分布
P = Matrix([
    [Rational(1, 3), Rational(2, 3)],
    [Rational(1, 2), Rational(1, 2)]
])

pi1, pi2 = symbols('pi1 pi2')
eqs = [
    pi1 * P[0, 0] + pi2 * P[1, 0] - pi1,  # pi1 = pi1*p11 + pi2*p21
    pi1 * P[0, 1] + pi2 * P[1, 1] - pi2,  # pi2 = pi1*p12 + pi2*p22
    pi1 + pi2 - 1                          # 归一化
]
sol = solve(eqs, (pi1, pi2))
# 得到 pi1=3/7, pi2=4/7

# 例：idx 9 - 周期矩阵的平稳分布
P3 = Matrix([
    [0, 1, 0],
    [0, 0, 1],
    [1, 0, 0]
])
# 验证 P^3 = I（周期为3）
P3_pow3 = P3**3  # 应为单位矩阵

# 求平稳分布
pi = symbols('pi0:3')
eqs3 = [sum(pi[j] * P3[j, i] for j in range(3)) - pi[i] for i in range(3)]
eqs3.append(sum(pi) - 1)
sol3 = solve(eqs3, pi)
```

### 吸收概率方程组

```python
from sympy import Matrix, symbols, solve, Rational

# 例：idx 3 - 吸收Markov链
# 状态：1(absorbing,非目标),2(transient),3(absorbing,目标),4(transient)
P_absorb = Matrix([
    [1,     0,     0,     0],          # 状态1
    [Rational(1,3), 0, Rational(1,3), Rational(1,3)],  # 状态2
    [0,     0,     1,     0],          # 状态3
    [Rational(1,4), Rational(1,4), 0, Rational(1,2)]   # 状态4
])

a2, a4 = symbols('a2 a4')
# a1 = 0, a3 = 1
eqs = [
    a2 - (Rational(1,3)*0 + Rational(1,3)*1 + Rational(1,3)*a4),
    a4 - (Rational(1,4)*0 + Rational(1,4)*a2 + Rational(1,2)*a4)
]
sol_absorb = solve(eqs, (a2, a4))
# a2 = 2/5, a4 = 1/5
```

### Poisson过程概率

```python
from sympy import exp, factorial, symbols, integrate

lam, t, k = symbols('lam t k', positive=True, integer=True)

# 例：idx 2 - Poisson PMF
lam_val = 2
t_val = 1
k_val = 3
p = exp(-lam_val * t_val) * (lam_val * t_val)**k_val / factorial(k_val)
# = 4*exp(-2)/3

# 例：idx 10 - 非齐次Poisson过程
lam_t = 2 * t  # lambda(t) = 2t
Lambda_3 = integrate(lam_t, (t, 0, 3))  # ∫_0^3 2t dt = 9
# E[N(3)] = 9

Lambda_interval = integrate(lam_t, (t, 1, 2))  # ∫_1^2 2t dt = 3
P_no_fault = exp(-Lambda_interval)  # e^{-3}

# 例：idx 11 - Poisson过程叠加
# N1~PP(2), N2~PP(3) -> N1+N2~PP(5)
P_zero = exp(-5)  # P(N1(1)+N2(1)=0) = e^{-5}
```

### 复合Poisson过程

```python
from sympy import symbols

# 例：idx 6
lam = 5  # 参数
t_val = 4
E_X = 20  # 单次期望
Var_X = 16  # 单次方差
E_X2 = Var_X + E_X**2  # 416

E_N = lam * t_val  # 20
E_S = E_N * E_X  # 400
Var_S = E_N * E_X2  # 8320
```

### Brownian运动协方差

```python
# 例：idx 7
# Cov(B(1)+B(2), B(3)) = Cov(B(1),B(3)) + Cov(B(2),B(3))
# = min(1,3) + min(2,3) = 1 + 2 = 3

# Var(B(2)-B(1)) = Var(B(2)) + Var(B(1)) - 2Cov(B(1),B(2))
# = 2 + 1 - 2*min(1,2) = 3 - 2 = 1
# 或直接：B(2)-B(1) ~ N(0, 1)，方差为1

def cov_B(s, t):
    """Brownian运动协方差"""
    return min(s, t)

result_cov = cov_B(1, 3) + cov_B(2, 3)  # 1 + 2 = 3
result_var = 2 + 1 - 2 * cov_B(1, 2)  # 3 - 2 = 1
```

### 指数分布与次序统计量

```python
from sympy import exp, symbols

# 例：idx 5
lam_list = [1, 1, 1]  # 三台机器均Exp(1)
lam_min = sum(lam_list)  # 3
# T = min(X1,X2,X3) ~ Exp(3)
E_T = 1 / lam_min  # 1/3
P_T_gt_1 = exp(-lam_min * 1)  # e^{-3}
```

---

## 模块速查：习题索引

| idx | 题型 | 难度 | 主题 | 关键公式/定理 | 核心方法 | 验证方法 |
|-----|------|------|------|-------------|---------|---------|
| 0 | 计算 | 简单 | 离散Markov链平稳分布 | $\pi P = \pi$，$\sum \pi_i = 1$ | 解线性方程组 | sympy `solve` 方程组 |
| 1 | 计算 | 简单 | 简单随机游走 | $P(S_n=m) = \binom{n}{(n+m)/2} 2^{-n}$ | 二项分布公式 | sympy `binomial` 计算 |
| 2 | 计算 | 简单 | Poisson过程概率 | $P(N(t)=k) = e^{-\lambda t}\frac{(\lambda t)^k}{k!}$ | 直接代入PMF公式 | sympy `exp` + `factorial` |
| 3 | 计算 | 中等 | Markov链吸收概率 | $a_i = \sum_{j\in A} p_{ij} + \sum_{k\in T} p_{ik} a_k$ | 建立并解线性方程组 | sympy `solve` |
| 4 | 计算 | 中等 | 生灭过程平稳分布 | $\pi_i\lambda_i = \pi_{i+1}\mu_{i+1}$（细致平衡） | 细致平衡递推 + 归一化 | 手动递推验证 |
| 5 | 计算 | 中等 | 指数分布与次序统计量 | $\min(\text{Exp}(\lambda_i)) \sim \text{Exp}(\sum \lambda_i)$ | 最小值分布公式 | sympy `exp` 计算 |  
| 6 | 计算 | 中等 | 复合Poisson过程 | $E[S(t)] = \lambda t E[X]$，$\operatorname{Var}(S(t)) = \lambda t E[X^2]$ | Wald期望/方差公式 | 手动代入验证 |
| 7 | 计算 | 中等 | Brownian运动协方差 | $\operatorname{Cov}(B(s),B(t)) = \min(s,t)$ | 协方差函数展开 | 独立增量 + min公式 |
| 8 | 计算 | 中等 | 更新过程 | $\lim_{t\to\infty} E[N(t)]/t = 1/\mu$ | 计算平均间隔 $\mu$ + 初等更新定理 | 期望公式计算 |
| 9 | 计算 | 中等 | Markov链周期性判定 | $d(i) = \gcd\{n \geq 1 : p_{ii}^{(n)} > 0\}$ | 解平稳分布 + 周期判定 | sympy 矩阵幂 |
| 10 | 计算 | 中等 | 非齐次Poisson过程 | $\Lambda(t) = \int_0^t \lambda(s)ds$，$N(t)\sim\text{Poisson}(\Lambda(t))$ | 积分求 $\Lambda(t)$ + Poisson概率 | sympy `integrate` |
| 11 | 计算 | 中等 | 独立Poisson过程叠加 | $N_1+N_2 \sim \text{PP}(\lambda_1+\lambda_2)$ | 参数相加 + Poisson概率 | sympy `exp` |
| 12 | 计算 | 困难 | Brownian运动首达时 | $P(T_a < T_{-b}) = \frac{b}{a+b}$，$E[\min(T_a, T_{-b})] = ab$ | 对称Brownian首达时公式 | 鞅停时法 / 公式直接代入 |
| 13 | 计算 | 困难 | Markov链极限分布 | 不可约非周期 $\Rightarrow$ 极限分布 $=$ 平稳分布 | 验证不可约+非周期 + 解$\pi P = \pi$ | sympy 矩阵特征值 |
| 14 | 证明 | 简单 | Brownian运动鞅性质 | $E[B(t)\mid\mathcal{F}_s] = B(s)$（独立增量） | 增量分解 + 条件期望 | 逻辑验证 |
| 15 | 证明 | 中等 | Chapman-Kolmogorov方程 | $p_{ij}^{(m+n)} = \sum_k p_{ik}^{(m)} p_{kj}^{(n)}$ | 全概率公式 + Markov性 + 时齐性 | 逻辑推导 |
| 16 | 证明 | 中等 | M/M/1排队平稳分布 | $\pi_n = (1-\rho)\rho^n$，$\rho = \lambda/\mu < 1$ | 细致平衡递推 + 几何级数归一化 | 逻辑推导 |
| 17 | 证明 | 中等 | Poisson过程等待时间 | $W_n \sim \text{Gamma}(n,\lambda)$，$f(t) = \frac{\lambda^n t^{n-1}e^{-\lambda t}}{(n-1)!}$ | $W_n = \sum T_i$ + 特征函数法 | 特征函数唯一性 |
| 18 | 证明 | 困难 | Doob有界停时定理 | $E[M_T] = E[M_0]$（$T$有界停时） | 鞅差表示 + 有界停时 | 逻辑推导 |
| 19 | 证明 | 困难 | Brownian运动反射原理 | $P(T_a \leq t) = 2P(B(t) \geq a) = 2(1-\Phi(a/\sqrt{t}))$ | 反射路径同分布 + 概率分解 | 对称性论证 |

---

## 模块速查：常见错误与陷阱

### 离散时间Markov链
1. **平稳分布方程中漏写归一化条件**：解 $\pi P = \pi$ 时，$n$ 个方程中只有 $n-1$ 个独立，必须添加 $\sum \pi_i = 1$ 才能得到唯一解。
2. **将非平稳分布误认为平稳分布**：必须验证 $\pi = \pi P$ 是否在所有分量上成立。仅通过一两项的比值不能断定。
3. **混淆周期性和非周期性**：状态有自环（$p_{ii} > 0$）仅保证该状态非周期，但若链不可约，则所有状态同周期。周期 $d > 1$ 意味着极限分布不存在（$P^n$ 不收敛）。
4. **极限分布与平稳分布的概念混淆**：平稳分布总是存在于有限不可约链中；极限分布只有在遍历链（不可约非周期）中才存在，并等于平稳分布。
5. **C-K方程中指标顺序错误**：$p_{ij}^{(m+n)} = \sum_k p_{ik}^{(m)} p_{kj}^{(n)}$，注意第一个因子的第一个下标是 $i$、第二个因子的第二个下标是 $j$。不要写成 $\sum_k p_{ki}^{(m)} p_{jk}^{(n)}$。

### 吸收概率
6. **边界条件设定错误**：吸收态的边界值必须正确——目标吸收态概率为 $1$，非目标吸收态概率为 $0$。混淆边界会导致整个方程组的结果错误。
7. **方程组中遗漏归一化条件**：吸收概率方程组本身是封闭的，不需要额外添加归一化。从瞬态出发，进入所有吸收态的概率之和为 $1$，可作为验证。
8. **转移矩阵行方向混淆**：$P$ 的行表示"从哪个状态出发"，列表示"到达哪个状态"。列方程时注意使用正确方向。

### Poisson过程
9. **混淆速率和均值**：Poisson过程的参数 $\lambda$ 是速率（rate），而 $N(t)$ 的分布参数是 $\lambda t$。直接代入 $\lambda$ 而不是 $\lambda t$ 是常见错误。
10. **非齐次Poisson中直接使用 $\lambda(t)$ 作为分布参数**：必须先用 $\Lambda(t) = \int_0^t \lambda(s)\,ds$ 转化。$N(t) \sim \text{Poisson}(\Lambda(t))$，而非 $\text{Poisson}(\lambda(t) \cdot t)$。
11. **Poisson过程叠加中混淆独立性和参数**：两个独立Poisson过程之和确实仍是Poisson过程，但要求真正的独立性。未验证独立性就叠加是错误的。
12. **混淆Poisson过程的 $N(t)$ 与 $W_n$**：$P(N(t) \geq n) = P(W_n \leq t)$ 是做变换的关键关系，但注意不等号方向。

### 复合Poisson过程
13. **方差公式中遗忘 $E[X^2]$ 而非 $\operatorname{Var}(X)$**：$\operatorname{Var}(S(t)) = \lambda t \cdot E[X^2]$，其中 $E[X^2] = \operatorname{Var}(X) + (E[X])^2$。直接代入 $\operatorname{Var}(X)$ 会显著低估。
14. **混淆 $S(t)$ 与 $N(t)$ 的期望**：复合Poisson的期望是 $E[S(t)] = E[N(t)] \cdot E[X] = \lambda t \cdot E[X]$。只计算了$N(t)$的期望而忘记乘以$E[X]$。

### Brownian运动
15. **协方差公式 $\min(s,t)$ 使用错误**：$\operatorname{Cov}(B(s), B(t)) = \min(s, t)$，不是 $\max(s, t)$ 也不是 $s \cdot t$。
16. **忘记增量独立性仅对不相交区间成立**：$B(3) - B(2)$ 与 $B(2) - B(1)$ 独立，但 $B(3) - B(1)$ 与 $B(2)$ 不独立。
17. **首达时公式的符号错误**：$P(T_a \leq t) = 2P(B(t) \geq a) = 2(1 - \Phi(a/\sqrt{t}))$。虽然 $P(B(t) \geq a) = P(B(t) \leq -a)$（对称性），但公式中使用的是 $P(B(t) \geq a)$ 不是 $P(B(t) \geq -a)$。
18. **双边界期望首达时遗忘乘积形式**：$E[\min(T_a, T_{-b})] = ab$，不是 $a+b$，不是 $(a+b)/2$。注意 $a$ 和 $b$ 都是正数。

### 生灭过程与排队论
19. **细致平衡公式下标不匹配**：正确形式是 $\pi_i \lambda_i = \pi_{i+1} \mu_{i+1}$。常见错误是写成 $\pi_i \lambda_i = \pi_{i+1} \mu_i$ 或 $\pi_{i+1} \lambda_{i+1} = \pi_i \mu_i$。
20. **M/M/1排队中遗忘平稳条件 $\rho < 1$**：当 $\rho \geq 1$ 时几何级数发散，不存在平稳分布。在应用 $\pi_n = (1-\rho)\rho^n$ 之前必须验证 $\rho < 1$。
21. **生灭过程递推方向搞反**：从 $\pi_0$ 出发依次递推 $\pi_1, \pi_2, \ldots$。注意 $\pi_{i+1} = (\lambda_i / \mu_{i+1}) \pi_i$，分子是 $\lambda_i$（当前状态的出生率），分母是 $\mu_{i+1}$（目标状态的死亡率）。

### 随机游走
22. **混淆步数与位置的关系**：$S_n = 2k - n$，其中 $k$ 是向上步数。反过来 $k = (n + S_n)/2$。确认 $n+S_n$ 为偶数是概率非零的前提。

### 更新过程
23. **将初等更新定理作为精确等式使用**：初等更新定理给出的是极限性质 $\lim_{t\to\infty} m(t)/t = 1/\mu$，对有限 $t$ 仅是大致近似，不是精确等式。
24. **遗忘均匀分布的均值公式**：$U(a,b)$ 的均值为 $(a+b)/2$，不是 $b/2$，不是 $b-a$。

### 鞅与停时
25. **Doob停止定理中停时必须有界**：定理要求 $T \leq K$ a.s.，若停时无界则结论不一定成立（需额外条件如一致可积性或 $E[T] < \infty$ 等）。

---

## 模块速查：关键公式速查表

### Markov链基础

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **平稳分布方程** | $\pi = \pi P$, $\sum_i \pi_i = 1$ | 有限状态Markov链 |
| **Chapman-Kolmogorov方程** | $p_{ij}^{(m+n)} = \sum_k p_{ik}^{(m)} p_{kj}^{(n)}$ | 任意Markov链 |
| **二状态平稳分布** | $\pi = \left(\frac{p_{21}}{p_{12}+p_{21}}, \frac{p_{12}}{p_{12}+p_{21}}\right)$ | $P = \begin{pmatrix}1-p_{12}&p_{12}\\p_{21}&1-p_{21}\end{pmatrix}$ |
| **极限分布存在条件** | 不可约 + 非周期 + 正常返 $\Rightarrow$ $\lim P^n$ 存在 | 有限状态不可约非周期即遍历 |
| **周期定义** | $d(i) = \gcd\{n \geq 1 : p_{ii}^{(n)} > 0\}$ | 任意Markov链 |
| **吸收概率方程组** | $a_i = \sum_{j\in A} p_{ij} + \sum_{k\in T} p_{ik}a_k$ | 吸收Markov链 |

### Poisson过程

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **Poisson PMF** | $P(N(t)=k) = e^{-\lambda t}\frac{(\lambda t)^k}{k!}$ | $k = 0,1,2,\ldots$ |
| **Poisson期望/方差** | $E[N(t)] = \lambda t$, $\operatorname{Var}(N(t)) = \lambda t$ | 齐次Poisson过程 |
| **非齐次均值函数** | $\Lambda(t) = \int_0^t \lambda(s)\,ds$ | 非齐次Poisson过程 |
| **Poisson叠加** | $N_1(t)+N_2(t) \sim \text{PP}(\lambda_1+\lambda_2)$ | $N_1 \perp N_2$ |
| **等待时间分布** | $W_n \sim \text{Gamma}(n,\lambda)$，$f(t) = \frac{\lambda^n t^{n-1}e^{-\lambda t}}{(n-1)!}$ | $t > 0$ |
| **到达间隔时间** | $T_i \sim \text{Exp}(\lambda)$ i.i.d. | 齐次Poisson过程 |

### 复合Poisson过程

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **期望** | $E[S(t)] = \lambda t \cdot E[X]$ | $N, X_i$ 独立 |
| **方差** | $\operatorname{Var}(S(t)) = \lambda t \cdot E[X^2]$ | $N, X_i$ 独立 |
| **二阶矩** | $E[X^2] = \operatorname{Var}(X) + (E[X])^2$ | 任意 $X$ |

### Brownian运动

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **协方差** | $\operatorname{Cov}(B(s), B(t)) = \min(s, t)$ | $s, t \geq 0$ |
| **方差** | $\operatorname{Var}(B(t)) = t$ | $t \geq 0$ |
| **增量分布** | $B(t) - B(s) \sim N(0, t-s)$ | $0 \leq s < t$ |
| **鞅性质** | $E[B(t) \mid \mathcal{F}_s] = B(s)$ | $s < t$ |
| **首达时概率（反射原理）** | $P(T_a \leq t) = 2(1 - \Phi(a/\sqrt{t}))$ | $a > 0, t > 0$ |
| **双边界首达概率** | $P(T_a < T_{-b}) = \frac{b}{a+b}$ | $a, b > 0$ |
| **双边界期望首达时** | $E[\min(T_a, T_{-b})] = ab$ | $a, b > 0$ |

### 生灭过程与排队论

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **细致平衡** | $\pi_i \lambda_i = \pi_{i+1} \mu_{i+1}$ | 生灭过程/可逆Markov链 |
| **生灭平稳分布递推** | $\pi_{n} = \pi_0 \prod_{k=0}^{n-1} \frac{\lambda_k}{\mu_{k+1}}$ | 生灭过程 |
| **M/M/1平稳分布** | $\pi_n = (1-\rho)\rho^n$, $\rho = \lambda/\mu$ | $\rho < 1$, $n = 0,1,2,\ldots$ |
| **M/M/1平均队长** | $L = \frac{\rho}{1-\rho}$ | $\rho < 1$ |

### 随机游走

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **位置分布** | $P(S_n = m) = \binom{n}{\frac{n+m}{2}} \cdot 2^{-n}$ | $n+m$ 偶数，$\|m\| \leq n$ |
| **期望与方差** | $E[S_n] = 0$, $\operatorname{Var}(S_n) = n$ | 对称随机游走 |

### 更新过程

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **初等更新定理** | $\lim_{t\to\infty} \frac{E[N(t)]}{t} = \frac{1}{\mu}$ | $\mu = E[X_1] < \infty$ |
| **长期更新率** | $\text{更新率} = 1 / \mu$ | 任意更新过程 |

### 指数分布与次序统计量

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **指数分布独立性最小值** | $\min(\text{Exp}(\lambda_i)) \sim \text{Exp}(\sum \lambda_i)$ | $X_i$ 独立 |
| **生存函数** | $P(\min X_i > t) = e^{-(\sum \lambda_i) t}$ | $t > 0$ |
| **同参数型最小值期望** | $E[\min X_i] = 1/(n\lambda)$ | $X_i \sim \text{Exp}(\lambda)$ i.i.d. |

### 鞅与停时

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **鞅定义** | $E[M_{n+1} \mid \mathcal{F}_n] = M_n$ a.s. | $\{M_n\}$ 关于 $\{\mathcal{F}_n\}$ 可适 |
| **Doob有界停时定理** | $E[M_T] = E[M_0]$ | $T$ 有界停时，$\{M_n\}$ 鞅 |
| **停时过程的鞅表示** | $M_{T\wedge n} = M_0 + \sum_{k=1}^n (M_k - M_{k-1}) \mathbf{1}_{\{T \geq k\}}$ | 任意鞅与停时 |

---

## 模块速查：计算题标准解法速查

### 类型A：Markov链平稳分布
**步骤**：写出 $\pi P = \pi$ $\to$ 添加 $\sum \pi_i = 1$ $\to$ 解线性方程组

例：二状态 $P = \begin{pmatrix}1/3 & 2/3\\ 1/2 & 1/2\end{pmatrix}$：$\pi_1 = \frac{1}{3}\pi_1 + \frac{1}{2}\pi_2$，解得 $\pi = (3/7, 4/7)$。

### 类型B：随机游走位置概率
**步骤**：$S_n = m$ $\to$ 向上步数 $k = (n+m)/2$ $\to$ $P = \binom{n}{k} \cdot 2^{-n}$

例：$n=6$，$m=0 \Rightarrow k=3$，$P = \binom{6}{3} \cdot 2^{-6} = 20/64 = 5/16$。

### 类型C：Poisson过程概率
**步骤**：确定 $\lambda$ 和时间 $t$ $\to$ 代入 $P(N(t)=k) = e^{-\lambda t}(\lambda t)^k/k!$

例：$\lambda=2$，$t=1$，$k=3$：$P = e^{-2} \cdot 8/6 = (4/3)e^{-2}$。

### 类型D：吸收概率
**步骤**：列出瞬态的吸收概率方程 $\to$ 设定边界条件 $\to$ 解方程组

例：四状态链，状态1和3为吸收态。$a_2 = (1/3)a_1 + (1/3)a_3 + (1/3)a_4 = (1/3) + (1/3)a_4$，解得 $a_2 = 2/5$。

### 类型E：生灭过程平稳分布
**步骤**：列出 $\lambda_i, \mu_i$ $\to$ 细致平衡递推 $\pi_{i+1} = (\lambda_i/\mu_{i+1})\pi_i$ $\to$ 归一化

例：$\lambda_0=3, \mu_1=2, \lambda_1=1, \mu_2=4$：$\pi_1 = (3/2)\pi_0$, $\pi_2 = (3/8)\pi_0$，$\pi_0 = 8/23$。

### 类型F：复合Poisson过程期望/方差
**步骤**：确认 $\lambda$ 和时间 $t$ $\to$ 计算 $E[X]$ 和 $E[X^2]$ $\to$ $E[S] = \lambda t E[X]$，$\operatorname{Var}(S) = \lambda t E[X^2]$

例：$\lambda=5$，$t=4$，$E[X]=20$，$\operatorname{Var}(X)=16$：$E[S]=400$，$\operatorname{Var}(S)=8320$。

### 类型G：Brownian运动协方差
**步骤**：写出含 $B(t)$ 的线性组合 $\to$ 利用 $\operatorname{Cov}(B(s),B(t)) = \min(s,t)$ 展开

例：$\operatorname{Cov}(B(1)+B(2), B(3)) = \operatorname{Cov}(B(1),B(3)) + \operatorname{Cov}(B(2),B(3)) = \min(1,3) + \min(2,3) = 1+2 = 3$。

### 类型H：Brownian运动首达时
**步骤**：识别 $a, b > 0$ $\to$ $P(T_a < T_{-b}) = b/(a+b)$ $\to$ $E[\min(T_a, T_{-b})] = ab$

例：$a=b=1$：$P(T_1 < T_{-1}) = 1/2$，$E[T] = 1 \cdot 1 = 1$。

### 类型I：更新过程
**步骤**：确定 $X_i$ 的分布和均值 $\mu$ $\to$ 长期更新率 $= 1/\mu$ $\to$ 期望次数 $\approx t/\mu$

例：$X_i \sim U(0,2)$，$\mu = 1$，长期更新率 $=1$ 次/年。

### 类型J：非齐次Poisson过程
**步骤**：计算 $\Lambda(t) = \int_0^t \lambda(s)\,ds$ $\to$ 用于期望和概率计算

例：$\lambda(t) = 2t$，$\Lambda(3) = 9$，$\Lambda(2)-\Lambda(1) = 3$。

### 类型K：Markov链极限分布
**步骤**：验证不可约 $\to$ 验证非周期 $\to$ 求平稳分布即为极限分布

例：$P$ 含自环及回路 $1\to2\to3\to1$，不可约非周期，极限分布 $=$ 平稳分布 $=(1/3,1/3,1/3)$。

---

## 模块速查：证明题标准策略速查

### 策略1：全概率公式 + Markov性 + 时齐性
**适用**：Chapman-Kolmogorov方程（idx 15）

模式：在中间时刻 $m$ 对状态做全概率展开 $\to$ 利用Markov性消去历史条件 $\to$ 利用时齐性转化时间跨度 $\to$ 得到乘积形式。

### 策略2：增量分解 + 条件期望
**适用**：Brownian运动鞅性质（idx 14）

模式：$B(t) = (B(t)-B(s)) + B(s)$ $\to$ 取条件期望 $\to$ 独立增量使得 $E[B(t)-B(s) \mid \mathcal{F}_s] = 0$ $\to$ 得证。

### 策略3：细致平衡 + 递推 + 几何级数归一化
**适用**：M/M/1排队平稳分布（idx 16）

模式：列出生灭率 $\to$ 写出细致平衡 $\lambda \pi_n = \mu \pi_{n+1}$ $\to$ 递推 $\pi_n = \rho^n \pi_0$ $\to$ 归一化 $\sum \pi_n = 1 \Rightarrow \pi_0 = 1-\rho$。

### 策略4：特征函数法 / 矩母函数法
**适用**：Poisson过程等待时间分布（idx 17）

模式：$W_n = \sum T_i$（$T_i \sim \text{Exp}(\lambda)$ i.i.d.）$\to$ 求特征函数 $\phi_{W_n}(t) = (\lambda/(\lambda-it))^n$ $\to$ 识别为 $\text{Gamma}(n,\lambda)$ 的特征函数 $\to$ 由唯一性得证。

### 策略5：鞅差表示 + 停时可测性 + 有界性
**适用**：Doob有界停时定理（idx 18）

模式：$M_{T\wedge n} = M_0 + \sum_{k=1}^n (M_k-M_{k-1})\mathbf{1}_{\{T \geq k\}}$ $\to$ 验证 $\mathbf{1}_{\{T \geq k\}} \in \mathcal{F}_{k-1}$ $\to$ 鞅差条件期望为零 $\to$ $E[M_{T\wedge n}] = E[M_0]$ $\to$ 取 $n=K$（有界停时）。

### 策略6：反射路径 + 概率分解 + 对称性
**适用**：Brownian运动反射原理（idx 19）

模式：$P(T_a \leq t) = P(T_a \leq t, B(t) > a) + P(T_a \leq t, B(t) < a)$ $\to$ 第一项 $= P(B(t) > a)$ $\to$ 第二项通过反射路径 $\tilde{B}(s) = 2a - B(s)$ 转化为 $P(B(t) > a)$ $\to$ 总概率 $= 2P(B(t) > a)$。

---

### 竞赛拓展：完全图随机游动的覆盖时间

#### 核心概念

考虑完全图 $K_n$（$n$ 个顶点，每对不同顶点间均有一条边相连）上的简单对称随机游走：每步从当前顶点等概率地跳到其余 $n-1$ 个顶点中的任意一个。

**覆盖时间（cover time）** $C$ 定义为从任意起点出发，首次访问完所有 $n$ 个顶点所需要的最少步数。覆盖时间是随机游走理论中的核心量度，直接推广了经典的优惠券收集问题（coupon collector problem）：在优惠券收集问题中，每次"抽取"是独立同分布的；而在完全图随机游走中，每次"抽取"的分布依赖于当前位置，但由于完全图的对称性，两者的期望结构极为相似。

#### 常用公式

1. **覆盖时间的分解**：
   $$C = \sum_{k=1}^{n-1} G_k$$
   其中 $G_k$ 表示从已访问 $k$ 个不同顶点的时刻起，到首次访问第 $k+1$ 个新顶点所需的等待步数。由于完全图的对称性，这 $n-1$ 个等待时间是**相互独立**的。

2. **等待时间 $G_k$ 的分布**：在当前已访问 $k$ 个顶点的状态下，下一步跳到新顶点的概率为
   $$p_k = \frac{n-k}{n-1}$$
   因此 $G_k \sim \text{Geometric}(p_k)$（取值为 $1, 2, 3, \ldots$），其期望与方差为：
   $$E[G_k] = \frac{1}{p_k} = \frac{n-1}{n-k}, \quad \operatorname{Var}(G_k) = \frac{1-p_k}{p_k^2} = \frac{(n-1)(k-1)}{(n-k)^2}$$

3. **期望覆盖时间**：
   $$E[C] = \sum_{k=1}^{n-1} E[G_k] = \sum_{k=1}^{n-1} \frac{n-1}{n-k} = (n-1) \sum_{j=1}^{n-1} \frac{1}{j} = (n-1) H_{n-1}$$
   其中 $H_{n-1} = 1 + \frac{1}{2} + \cdots + \frac{1}{n-1}$ 为第 $n-1$ 个调和数（harmonic number）。

   > **起点约定（务必核对题面）**：上式计的是从初始位置（已访问 1 个顶点）出发后的**转移步数**。若题面将初始时刻记为 $t = 1$（即「第 1 步」而非「第 0 步」），则总时间为
   > $$E[T] = 1 + (n-1) H_{n-1}$$
   > 也就是说，题面时间编号从 1 起时，答案比公式多 1。判题前务必确认题面的时间起点约定：转移步数 vs. 时刻编号。

4. **渐近公式**：利用 $H_{n-1} = \ln n + \gamma + O(1/n)$（$\gamma \approx 0.5772$ 为 Euler-Mascheroni 常数），
   $$E[C] \sim n \ln n \quad (n \to \infty)$$

5. **覆盖时间的方差**（由独立性）：
   $$\operatorname{Var}(C) = \sum_{k=1}^{n-1} \operatorname{Var}(G_k) = (n-1)^2 \sum_{j=1}^{n-1} \frac{1}{j^2} - (n-1) H_{n-1}$$

6. **与经典优惠券收集问题的对比**：
   | 项目 | 优惠券收集 | 完全图覆盖 |
   |------|----------|-----------|
   | 每次"发现新顶点"概率 | $\frac{n-k}{n}$ | $\frac{n-k}{n-1}$ |
   | 期望完成时间 | $n H_n$ | $(n-1) H_{n-1}$ |
   | 高概率界 | $n \ln n + O(n)$ | $n \ln n + O(n)$ |

#### 解题步骤

1. 利用对称性将覆盖时间分解为 $n-1$ 个相互独立的几何分布随机变量之和。
2. 写出第 $k$ 步新顶点发现概率：$p_k = \frac{n-k}{n-1}$。
3. 由几何分布期望公式 $E[G_k] = 1/p_k$ 求和得期望覆盖时间。
4. 利用调和数的渐进展开进行渐近估计。
5. 若需求覆盖时间的概率界，可使用 Chernoff 界结合几何分布独立性的技巧。

#### 常见陷阱

- **混淆覆盖时间与回访时间**：覆盖时间关注的是访问所有顶点的时长，而回访时间（return time）是对特定顶点的两次连续访问之间的步数。两者的量级不同（前者 $O(n \ln n)$，后者 $O(n)$）。
- **忘记 $G_k$ 是几何分布**：在离散时间随机游走中，等待时间是离散的几何分布，而非连续时间的指数分布。两者的期望分别为 $1/p$ 和 $1/\lambda$，形式类似但不可混用。
- **将完全图公式误用于一般图**：一般图上随机游走的覆盖时间与图的电阻（effective resistance）密切相关，由 Matthews 方法给出界 $O(|E| \cdot R \cdot \log n)$，而非简单的调和数公式。
- **忽略完全图的特殊性**：$G_k$ 的独立性依赖于完全图的对称性。在非完全图上，不同阶段的等待时间一般不是独立的。
- **起点编号导致差 1**：公式 $E[C]=(n-1)H_{n-1}$ 计的是转移步数。若题面将初始时刻记为 $t=1$（时间从 1 起编），则总时间答案为 $1+(n-1)H_{n-1}$，比公式多 1。务必在答题前核对题面的时间起点约定。

---

### 竞赛拓展：Fibonacci与Lucas数的递推序列在随机游动中的应用

#### 核心概念

Fibonacci 数列 $\{F_n\}$ 和 Lucas 数列 $\{L_n\}$ 是满足同一类二阶线性递推的两组经典序列：

$$F_{n+2} = F_{n+1} + F_n, \quad F_0 = 0,\; F_1 = 1$$
$$L_{n+2} = L_{n+1} + L_n, \quad L_0 = 2,\; L_1 = 1$$

在随机游走的理论研究（特别是赌徒破产问题和转移矩阵的特征分析）中，Fibonacci 和 Lucas 数频繁出现，其根本原因在于：一维带吸收壁的随机游走的转移概率矩阵的特征值为 $\cos(k\pi/(N+1))$，与 Chebyshev 多项式相关，而 Fibonacci 数正是这些多项式在特定参数下的取值。

#### 常用公式

1. **Binet 公式（闭形式）**：
   $$F_n = \frac{\alpha^n - \beta^n}{\alpha - \beta}, \quad L_n = \alpha^n + \beta^n$$
   其中 $\alpha = \frac{1+\sqrt{5}}{2}$（黄金比），$\beta = \frac{1-\sqrt{5}}{2}$。注意 $|\beta| < 1$，故对大的 $n$ 有 $F_n \approx \alpha^n / \sqrt{5}$。

2. **Cassini 恒等式**：
   $$F_{n-1}F_{n+1} - F_n^2 = (-1)^n$$

3. **矩阵幂表示**：
   $$\begin{pmatrix} F_{n+1} & F_n \\ F_n & F_{n-1} \end{pmatrix} = \begin{pmatrix} 1 & 1 \\ 1 & 0 \end{pmatrix}^n$$
   这一表示在分析两步状态的 Markov 链转移矩阵的幂时非常有用。

4. **赌徒破产问题中的应用**：在 $p \neq 1/2$ 的非对称一维随机游走中，状态空间 $\{0, 1, \ldots, N\}$，吸收壁为 $0$ 和 $N$。从状态 $k$ 出发最终被 $N$ 吸收的概率为：
   $$P_k = \frac{1 - (q/p)^k}{1 - (q/p)^N} = \frac{\alpha^{2k-N} \cdot (\alpha^k - \beta^k) / (\alpha - \beta)}{\alpha^{2k-N} \cdot (\alpha^N - \beta^N) / (\alpha - \beta)} \quad \text{（当 } p/q = \alpha \text{ 时退化为 Fibonacci 比）}$$

5. **Lucas 数的奇偶性规律**：
   $$L_n \equiv \begin{cases} 2 \pmod{?} & \text{若 } 3 \mid n \\ 1 \pmod{2} & \text{若 } 3 \nmid n \end{cases}$$
   可用于判定随机游走中回访步数的奇偶性。

6. **生成函数**：
   $$\sum_{n=0}^{\infty} F_n x^n = \frac{x}{1 - x - x^2}, \quad \sum_{n=0}^{\infty} L_n x^n = \frac{2 - x}{1 - x - x^2}$$
   这两个有理生成函数在分析随机游走首达时间分布的概率生成函数时频繁出现。

#### 应试解题技巧

- 遇到 $p \neq 1/2$ 的赌徒破产问题，直接用 Binet 公式将 $F_n$ 写成 $\alpha^n$ 和 $\beta^n$ 的线性组合，化简时可约去公共因子。
- 验证 Fibonacci 恒等式时优先使用矩阵幂形式：$\begin{pmatrix} F_{n+1} & F_n \\ F_n & F_{n-1} \end{pmatrix} = Q^n$ 可同时得到多个恒等式。
- Lucas 数满足 $L_n = F_{n-1} + F_{n+1}$，这意味着 $L_n$ 可用于表示对称随机游走中"两步之内回到原点"的概率相关量。
- 在考试中若需要求某一递推序列的通项，首先判断特征方程是否与 Fibonacci 递推同构（即 $x^2 - x - 1 = 0$），若是则直接套用 Fibonacci/Lucas 的闭形式。

#### 考试高频陷阱

- Fibonacci 与 Lucas 的递推公式相同但初始值不同（$F_0=0, F_1=1$ vs $L_0=2, L_1=1$），考试时务必先确认题目所指的是哪一个序列。
- Cassini 恒等式右边的符号 $(-1)^n$ 极易遗漏或写反：当 $n$ 为偶数时右边为 $+1$，奇数时为 $-1$。
- Binet 公式中 $\beta = \frac{1-\sqrt{5}}{2} < 0$，计算 $\beta^n$ 的符号需要根据 $n$ 的奇偶性判断，不要想当然地认为 $\beta^n \to 0$ 就可以忽略符号。
- 赌徒破产问题中公式的形式取决于 $p$ 与 $q$ 的大小关系。常用的记忆法：当 $p > 1/2$ 时漂移向右，被上壁 $N$ 吸收的概率趋于 $1$（$N\to\infty$）；当 $p < 1/2$ 时漂移向左，被上壁吸收的概率趋于 $0$。

---

## 模块速查：参考资源

- 配套验证知识提示：`随机过程验证示例.py`
- 数据集来源：`随机过程.md`（20题，涵盖全部核心知识点）
- 推荐教材：《随机过程》（Sheldon Ross）、《应用随机过程》（林元烈）、《随机过程导论》（Lawler）、《概率、随机变量与随机过程》（Papoulis）
- 在线工具：SymPy Live、SageMath

<!-- AUTO-KNOWLEDGE-BEGIN 知识点速查（生成区；按学科提炼的抽象题型方法论，不含任何具体题目） -->

以下速查条目是按学科整理的题型方法论（核心内容/解题路线/易错点），供匹配到的题目作方法参考；条目不含任何具体题目的题面或结论，最终答案仍须独立推导并验证。

## 模块速查：随机过程：完全图随机游动的覆盖时间
- 检索词：覆盖 cover covering 图上 graph 完全图 complete 顶点 vertex vertices 概率 probability 随机 random 期望 expectation expected value 分布 distribution 随机游动 walk time cycle cycles ring
- 核心内容：完全图上无自环的简单随机游动中，「首次遍访全部顶点」的覆盖时间可分解为依次访问第 k 个新顶点的等待阶段之和；从已访问 i 个顶点出发时，下一步撞上新顶点的概率由尚未访问的顶点数决定，每阶段等待时间服从几何分布；由线性期望，总期望化为各阶段几何分布期望之和，即推广的优惠券收集问题（调和级数型求和）。**判分口径（先读）**：题面 σᵢ=min{t≥1:X_t=i} 从 t=1 起计时，初始顶点 X₀ 必须**回访一次**才算访问到 ⇒ E[T]=**1+(N−1)H_{N−1}**（T=τ_N，τ₁=1，τ_{k+1}−τ_k 为几何分布，E[τ_{k+1}−τ_k]=(N−1)/(N−k)，k=1..N−1 求和）。**答案带 +1**；答 (N−1)H_{N−1}（把 X₀ 计入已访问的标准版本）会判错。
- 解题路线：先识别「每步不允许停留原顶点」与标准优惠券收集的差异（概率分母随之变化）；用期望线性性把总覆盖时间拆成阶段期望之和；确认 t 的起始编号决定是否 +1。
- 易错点：直接套用标准优惠券收集公式而忽略无自环导致的概率分母变化；混淆覆盖时间与首达/返回时间；**漏掉 σᵢ 从 t=1 计时的 +1（本题最常见错法）**。
- 作答模板（判分口径）：最终答案写 \boxed{E[T]=1+(N−1)H_{N−1}}（或 \boxed{1+(N−1)H_{N−1}}），不要写成展开的调和级数和式、不要丢 +1。

<!-- AUTO-KNOWLEDGE-END -->
