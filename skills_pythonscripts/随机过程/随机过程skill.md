---
name: stochastic-processes-verification
description: Use when verifying stochastic processes problems — Markov chains, Poisson processes, Brownian motion, birth-death processes, renewal processes, martingales, and queueing theory
---

# 随机过程解题与验证技能手册

## 领域边界与路由约定

- 适用范围：Markov 链、Poisson 过程、Brownian 运动、生灭/更新过程、鞅、停时和覆盖时间。
- 不接管：静态分布与概率计算转概率论；时间序列观测数据、趋势和季节调整转统计推断。
- 验证契约：明确离散步数、时间编号和初始状态是否已经计入覆盖集合；严格按题面定义推导计时偏移，并检查停时/状态空间条件。

## 时间序列兼容口径

经典时间序列分解包含长期趋势 $T$、季节变动 $S$、循环变动 $C$ 和不规则项 $I$；“随机变动”通常是对不规则项的同义描述，不应重复计数。弱平稳要求均值、方差恒定且协方差只依赖滞后；白噪声还要求不同期不相关。季节调整常用移动平均比率法和 X-11/X-13。
- 比较两个总量指标时间数列时，先看分子、分母的经济含义和单位：比值可能表示相对指标，也可能表示平均水平或强度指标。不能仅凭“两个总量”或绝对化词语预先决定分类，最终按题面教材定义给出判断及反例/依据。

## 概述

本技能手册覆盖本科随机过程课程的核心知识体系，包括离散时间Markov链（转移矩阵、平稳分布、周期性、极限分布、吸收概率）、Poisson过程（基本概率、非齐次、独立叠加、等待时间分布）、复合Poisson过程（期望与方差）、生灭过程与M/M/1排队论、Brownian运动（协方差、鞅性质、首达时、反射原理）、随机游走、更新过程（初等更新定理）、指数分布与次序统计量、以及鞅与停时（Doob有界停时定理）等经典内容。本手册以概念模块和可复核的推导步骤为骨架；示例参数只用于说明记号，不能替代当前题面的独立计算。

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

---

## 模块速查：通用解题方法论

### 统一工作流
1. 先从题面写出状态空间、初始条件、时间或步数的编号方式，以及目标事件的精确定义。
2. 选择与模型匹配的定理或递推；每个边界条件都在方程中显式标注。
3. 对概率、期望和方差分别做量纲、范围和极限检查；必要时用独立的符号或小规模计算复核。
4. 输出时区分推导结论、数值近似和仍需题面确认的假设，不把示例参数当作结论。

### Markov 链与吸收问题
- 有限链先检查行和、可达性、周期和闭类，再解 `pi P = pi` 并归一化。
- 吸收链按瞬态/吸收态分块，写 `a = r + Q a`；回代后逐个核对边界值与概率范围。
- 极限分布只有在不可约、正常返且非周期等条件满足时才可直接等同于平稳分布。

### Poisson、更新与排队
- 齐次过程用区间长度乘强度，非齐次过程先积分得到均值函数 `Lambda(t)`。
- 复合过程用全概率、条件期望和全方差公式，分别记录单次报酬的一阶、二阶矩。
- 更新率、排队稳定性和 Little 定律都要先确认有限均值及稳定条件，再代入参数。
- 独立过程叠加时重新检查独立性与时间区间，不能从相似记号直接套结论。

### Brownian 运动、随机游走与鞅
- Brownian 运动的协方差由 `min(s,t)` 给出；首达问题先声明单边或双边边界，再用反射原理或鞅停止法。
- 随机游走位置概率先检查奇偶和可达范围，再用二项系数或递推求值。
- 证明鞅与停时结论时，逐项检查滤子可测性、可积性和停时有界性；反射映射要写出终点对应关系。

### 时间起点和覆盖时间核验
- 覆盖问题先说明初始状态是否已经计入覆盖集合，以及 `T` 表示转移次数还是带标签的访问时刻。
- 若两种编号约定会产生偏移，分别写出参数化表达式并由题面选择；不要把固定的常数偏移预先写入答案。
- 对完全图等特殊结构，可将等待阶段写成几何分布并求和；换成一般图时重新验证独立性。

### 证据与复核清单
- Python 或符号计算只作为可审计的独立证据：记录输入、断言、边界和失败反例，不能以空输出或单纯 `print` 代替证明。
- 候选答案必须经过回代、范围、维度和至少一种替代方法检查；发现矛盾时保留矛盾记录并重新建模。
- 资料检索只提供定义和方法线索，任何具体数值、选项或解集都从当前题面重新推导。

## 模块速查：解法直达·完全图随机游动遍访时间期望（(N−1)Σ1/j）
- 检索词：完全图 随机游动 首次遍访 所有顶点 时间 期望
- 命中条件：简单随机游动
**判分口径（本题核定结论，提交前必读）**：ET = **\boxed{(N-1)\sum_{j=1}^{N-1}\frac{1}{j}}**。
错值警示：N·H_{N−1}（普通赠券收集的分母 N——游动不能原地停，每步在 N−1 个邻居中均匀选）、(N−1)²。
推导链：①分阶段：已访 k 个顶点时下一步遇新点概率 (N−k)/(N−1)（当前点必在已访集内、下一跳在其余 N−1 顶点均匀）⇒ τ_k~几何分布、E=（N−1)/(N−k)；②T=Σ_{k=1}^{N−1}τ_k、期望线性性；③换指标 j=N−k ⇒ ET=(N−1)Σ_{j=1}^{N−1}1/j；④τ₁=1 与 τ_{N−1}=N−1 两端 sanity check。
**自检**：N=2 给 (1)(1)=1 ✓；N=3 给 2(1+1/2)=3——手推核对。
