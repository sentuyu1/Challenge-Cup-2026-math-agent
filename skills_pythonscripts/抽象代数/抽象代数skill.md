---
name: abstract-algebra-verification
description: Use when verifying abstract algebra problems with sympy — group theory, ring theory, field theory, group actions, Sylow theorems, and Galois theory basics
---

# 抽象代数解题与验证技能手册

## 领域边界与路由约定

- 适用范围：群、环、理想、域、有限域、Sylow、Galois 扩张和群作用。
- 不接管：仅有矩阵/线性空间/多项式计算转高等代数；实变量函数方程转数学分析或竞赛进阶课程。
- 验证契约：明确运算、单位元、子群/理想闭性及扩张次数，不能以“看起来像群”代替公理检查。

## 高频错误与口径约定（评委反馈 2026-07-07）

- **有限 Abel 群分类必须枚举全部对象**：$n=p_1^{a_1}\cdots p_k^{a_k}$ 阶互不同构的 Abel 群共 $\prod_i P(a_i)$ 个（$P(a)$ 为整数 $a$ 的分拆数），最终答案必须先给总数、再逐一列出每个群，只列一个按未完成计。
- 例（评委题）：$36=2^2\times 3^2$，$P(2)\times P(2)=2\times2=4$ 个。初等因子形式：$\mathbb{Z}_4\oplus\mathbb{Z}_9$、$\mathbb{Z}_4\oplus\mathbb{Z}_3\oplus\mathbb{Z}_3$、$\mathbb{Z}_2\oplus\mathbb{Z}_2\oplus\mathbb{Z}_9$、$\mathbb{Z}_2\oplus\mathbb{Z}_2\oplus\mathbb{Z}_3\oplus\mathbb{Z}_3$；对应不变因子形式：$\mathbb{Z}_{36}$、$\mathbb{Z}_{3}\times\mathbb{Z}_{12}$、$\mathbb{Z}_{2}\times\mathbb{Z}_{18}$、$\mathbb{Z}_{6}\times\mathbb{Z}_{6}$。题面指定用哪种分解就用哪种，两种均可时给初等因子形式。

## 概述

本技能手册覆盖本科抽象代数课程的核心知识体系，包括群论基础（子群、商群、同态与同构定理）、环论基础（零因子、理想、极大理想）、对称群与群作用（共轭类、类方程）、Sylow定理、多项式环与域扩张、有限域、以及有限Abel群的结构定理。全手册以20道精选习题为骨架，系统梳理每个知识模块的核心概念、常用定理、解题步骤和常见陷阱，并配套验证知识提示，适用于抽象代数课程的学习、复习与自动解题验证。

---

## 知识点体系

### 模块1：群的基本概念

#### 核心概念

- **群的定义**：非空集合 $G$ 配备二元运算，满足（1）结合律；（2）存在单位元 $e$；（3）每个元素存在逆元。
- **Abel群（交换群）**：若对任意 $a,b \in G$ 有 $ab = ba$。
- **循环群**：$G = \langle g \rangle = \{g^k \mid k \in \mathbb{Z}\}$。若 $|G| = n$，则 $G \cong \mathbb{Z}_n$（加法群）。
- **元素的阶**：最小的正整数 $n$ 使得 $a^n = e$（乘法记法）或 $n \cdot a = 0$（加法记法），记作 $\mathrm{ord}(a)$。
- **有限群中元素的阶必为群阶的因子**（Lagrange定理的推论）。

#### 常用公式

1. **加法循环群 $\mathbb{Z}_n$ 中元素 $a$ 的阶**：
   $$\mathrm{ord}(a) = \frac{n}{\gcd(a, n)}$$
   其中 $\gcd$ 为最大公约数。

2. **循环群 $G = \langle g \rangle$ 中 $g^k$ 的阶**：
   $$\mathrm{ord}(g^k) = \frac{n}{\gcd(k, n)}, \quad \text{其中 } n = |G|$$

3. **置换的阶**：将置换分解为不相交轮换的乘积，轮换 $(a_1\ a_2\ \cdots\ a_k)$ 的阶为 $k$，整个置换的阶为各轮换阶的最小公倍数：
   $$\mathrm{ord}(\sigma) = \mathrm{lcm}(\ell_1, \ell_2, \ldots, \ell_r)$$
   其中 $\ell_i$ 为各不相交轮换的长度。

4. **置换的共轭**：$\tau \sigma \tau^{-1}$ 将 $\sigma$ 的轮换分解中的每个字母 $i$ 替换为 $\tau(i)$。

#### 解题步骤

**计算循环群中元素的阶：**
1. 写出群及其阶 $n$。
2. 计算 $\gcd(a, n)$。
3. 阶为 $n / \gcd(a, n)$。
4. 验证：$(\text{阶}) \cdot a \equiv 0 \pmod{n}$（加法）。

**计算置换的阶：**
1. 将置换写成不相交轮换的乘积。
2. 取各轮换长度的最小公倍数（lcm）。

**证明题（如 $a^2=e \Rightarrow G \text{ 是Abel群}$）：**
1. 写出已知条件：对任意 $a \in G$，$a^2 = e$（即 $a = a^{-1}$）。
2. 任取 $a, b \in G$，考虑 $(ab)^2 = e$，展开 $abab = e$。
3. 利用 $a^2 = e$ 和 $b^2 = e$ 消去 $a$ 和 $b$：左乘 $a$、右乘 $b$ 得 $ba = ab$。

**证明题（循环群的子群也是循环群）：**
1. 设 $G = \langle g \rangle$，$H \le G$。
2. 若 $H = \{e\}$，则 $H$ 为平凡循环群。
3. 否则取 $n = \min\{k > 0 \mid g^k \in H\}$（$H$ 中指数最小的正幂）。
4. 用带余除法证明 $H = \langle g^n \rangle$：任取 $g^m \in H$，$m = qn + r$（$0 \le r < n$），则 $g^r = g^{m - qn} \in H$，由 $n$ 的极小性 $r = 0$，故 $g^m = (g^n)^q$。

#### 对应习题

- **idx 0**: 在 $\mathbb{Z}_{30}$ 中求元素 $12$ 的阶 — 公式 $\mathrm{ord}(a) = 30/\gcd(12,30)$
- **idx 1**: 在 $S_5$ 中求置换 $(1\ 2\ 3)(4\ 5)$ 的阶 — lcm(3, 2) = 6
- **idx 3**: 求 $\mathbb{Z}_{18}$ 的所有子群 — 正因子与子群的一一对应
- **idx 14**: 证明：$a^2 = e$ 对所有 $a$ 成立则 $G$ 为Abel群
- **idx 15**: 证明：循环群的子群也是循环群

---

### 模块2：子群与商群

#### 核心概念

- **子群**：$H \subseteq G$ 且在 $G$ 的运算下也是群。等价于 $H \neq \varnothing$，且对任意 $a, b \in H$ 有 $ab^{-1} \in H$（子群判定定理）。
- **陪集**：左陪集 $aH = \{ah \mid h \in H\}$，右陪集 $Ha = \{ha \mid h \in H\}$。
- **正规子群**：$H \trianglelefteq G$ 当且仅当对任意 $g \in G$ 有 $gHg^{-1} = H$（左陪集=右陪集）。
- **商群**：若 $H \trianglelefteq G$，则 $G/H$ 在陪集运算 $(aH)(bH) = (ab)H$ 下构成群。
- **Lagrange定理**：若 $H \le G$（有限群），则 $|G| = |H| \cdot [G:H]$，其中 $[G:H]$ 为 $H$ 在 $G$ 中的指数（陪集个数）。

#### 常用公式

1. **Lagrange定理**：$|G| = |H| \cdot [G:H]$
2. **子群的阶**：$|H| \mid |G|$（$H$ 的阶整除 $G$ 的阶）
3. **陪集的阶**：$|aH| = |H|$（每个陪集与子群等势）
4. **商群的阶**：$|G/H| = |G| / |H|$（当 $H \trianglelefteq G$）
5. **循环群 $\mathbb{Z}_n$ 的子群**：与 $n$ 的正因子一一对应。对每个正因子 $d$，存在唯一的 $d$ 阶子群 $\langle n/d \rangle$。
6. **直积中元素的阶**：在 $G_1 \times G_2$ 中，$\mathrm{ord}((a,b)) = \mathrm{lcm}(\mathrm{ord}(a), \mathrm{ord}(b))$。

#### 解题步骤

**求子群格：**
1. 列出 $n$ 的所有正因子。
2. 对每个正因子 $d$，写出子群 $\langle n/d \rangle$。
3. 验证子群个数 = $n$ 的正因子个数（也等于 $\tau(n)$）。

**求陪集分解：**
1. 确定 $|H|$ 和 $[G:H] = |G|/|H|$。
2. 从 $G$ 中选取 $[G:H]$ 个代表元（通常 $0, 1, \ldots, [G:H]-1$）。
3. 构造所有陪集 $a + H$（加法群）或 $aH$（乘法群）。
4. 验证所有陪集的并等于 $G$ 且互不相交。

**求商群的阶：**
1. 计算 $|G|$（直积的阶为各因子阶之积）。
2. 计算 $|H|$（生成元在直积各分量中的阶的lcm）。
3. $|G/H| = |G| / |H|$。

**证明题（指数为2的子群正规）：**
1. $[G:H] = 2$ 意味着 $G$ 恰好有两个左陪集 $H$ 和 $gH$（$g \notin H$），也恰好有两个右陪集 $H$ 和 $Hg$。
2. 若 $g \in H$，显然 $gHg^{-1} = H$。
3. 若 $g \notin H$，则 $gH = G \setminus H = Hg$，故 $gHg^{-1} = H$。
4. 由定义，$H \trianglelefteq G$。

#### 对应习题

- **idx 4**: 求 $H = \langle 5 \rangle$ 在 $\mathbb{Z}_{15}$ 中的所有陪集
- **idx 6**: 求商群 $(\mathbb{Z}_4 \times \mathbb{Z}_6) / \langle(2,3)\rangle$ 的阶
- **idx 16**: 证明：指数为2的子群必为正规子群

---

### 模块3：群同态与同构定理

#### 核心概念

- **群同态**：映射 $\varphi: G \to H$ 满足 $\varphi(ab) = \varphi(a)\varphi(b)$ 对所有 $a, b \in G$ 成立。
- **核**：$\ker(\varphi) = \{g \in G \mid \varphi(g) = e_H\}$。$\ker(\varphi) \trianglelefteq G$。
- **像**：$\operatorname{im}(\varphi) = \{\varphi(g) \mid g \in G\}$。$\operatorname{im}(\varphi) \le H$。
- **第一同构定理**：$G / \ker(\varphi) \cong \operatorname{im}(\varphi)$。

#### 常用公式

对于循环群之间的同态 $\varphi: \mathbb{Z}_m \to \mathbb{Z}_n$ 由 $\varphi(1) = k$ 定义（即 $\varphi(x) = kx \bmod n$）：

1. **核**：$\ker(\varphi) = \{x \in \mathbb{Z}_m \mid kx \equiv 0 \pmod{n}\} = \{x \mid n \mid kx\}$
   - 具体：$\ker(\varphi) = \langle m / \gcd(m, n/\gcd(k,n)) \rangle$，通常直接求解 $n \mid kx$ 在模 $m$ 下的解集。
   - 计算 $|\ker(\varphi)| = m / \gcd(m, n/\gcd(k,n))$，$\ker(\varphi)$ 作为 $\mathbb{Z}_m$ 的子群由 $m / |\ker(\varphi)|$ 生成。

2. **像**：$\operatorname{im}(\varphi) = \{kx \bmod n \mid x \in \mathbb{Z}_m\} = \langle \gcd(k, n) \rangle$（作为 $\mathbb{Z}_n$ 的子群）。

3. **同态基本定理**：$|G| = |\ker(\varphi)| \cdot |\operatorname{im}(\varphi)|$。

#### 解题步骤

**求循环群同态的核与像：**
1. 确定同态 $\varphi: \mathbb{Z}_m \to \mathbb{Z}_n$，$\varphi(1) = k$。
2. 求像：$\operatorname{im}(\varphi) = \langle \gcd(k, n) \rangle$，阶为 $n / \gcd(k, n)$。
3. 求核：$\ker(\varphi) = \{x \in \mathbb{Z}_m \mid kx \equiv 0 \pmod{n}\}$。
   - 条件等价于 $n \mid kx$，即 $\frac{n}{\gcd(k,n)} \mid x$。
   - 在 $\mathbb{Z}_m$ 中，$\ker(\varphi) = \langle \frac{n}{\gcd(k,n)} \rangle$（需在模 $m$ 下考虑，实际为 $\langle \frac{n}{\gcd(k,n)} \bmod m \rangle$）。
4. 验证 $|\ker(\varphi)| \cdot |\operatorname{im}(\varphi)| = m$。

**证明第一同构定理：**
1. 设 $K = \ker(\varphi)$，定义 $\psi: G/K \to \operatorname{im}(\varphi)$，$\psi(gK) = \varphi(g)$。
2. 验证良定性：若 $g_1K = g_2K$，则 $g_1^{-1}g_2 \in K$，故 $\varphi(g_1) = \varphi(g_2)$。
3. 验证同态性：$\psi(g_1K \cdot g_2K) = \psi(g_1g_2K) = \varphi(g_1g_2) = \varphi(g_1)\varphi(g_2) = \psi(g_1K)\psi(g_2K)$。
4. 验证单射：$\psi(gK) = e \Rightarrow \varphi(g) = e \Rightarrow g \in K \Rightarrow gK = K$。
5. 验证满射：对任意 $h \in \operatorname{im}(\varphi)$，存在 $g \in G$ 使 $\varphi(g) = h$，则 $\psi(gK) = h$。
6. 结论：$\psi$ 为同构。

#### 对应习题

- **idx 5**: 求 $\varphi: \mathbb{Z}_{12} \to \mathbb{Z}_8$（$\varphi(1)=2$）的核与像
- **idx 19**: 证明群的第一同构定理 $G/\ker(\varphi) \cong \operatorname{im}(\varphi)$

---

### 模块4：对称群与群作用

#### 核心概念

- **对称群 $S_n$**：$n$ 个元素的全体置换构成的群，$|S_n| = n!$。
- **轮换**：长度为 $k$ 的轮换 $(a_1\ a_2\ \cdots\ a_k)$ 表示 $a_1 \to a_2 \to \cdots \to a_k \to a_1$。
- **不相交轮换的乘积**：$S_n$ 中每个置换可唯一地分解为不相交轮换的乘积。
- **轮换型（cycle type）**：将 $n$ 的正整数划分记作各不相交轮换的长度（从小到大或从大到小排列）。例如在 $S_4$ 中，轮换型 $(2,1,1)$ 表示一个对换加两个不动点。
- **共轭类**：$S_n$ 中两个置换共轭当且仅当它们具有相同的轮换型。
- **类方程**：$|G| = \sum [G : C_G(g_i)]$，其中 $g_i$ 取遍共轭类的代表元，$C_G(g_i)$ 为 $g_i$ 的中心化子。

#### 常用公式

1. **共轭类大小**：对于轮换型为 $1^{c_1} 2^{c_2} \cdots n^{c_n}$（有 $c_i$ 个长度为 $i$ 的轮换），其共轭类大小为：
   $$\frac{n!}{1^{c_1} 2^{c_2} \cdots n^{c_n} \cdot c_1! c_2! \cdots c_n!}$$

2. **$S_n$ 的共轭类个数 = $n$ 的划分个数 $p(n)$**。

3. **轮换的阶**：长度为 $k$ 的轮换的阶为 $k$。

4. **置换的阶**：$\mathrm{ord}(\sigma) = \mathrm{lcm}(\ell_1, \ldots, \ell_r)$。

5. **$S_4$ 的共轭类（5个）**：
   - $(1)(2)(3)(4)$：恒等，大小 1
   - $(1\ 2)$：对换，大小 $C_4^2 = 6$
   - $(1\ 2\ 3)$：3-轮换，大小 $2 \cdot C_4^3 = 8$
   - $(1\ 2)(3\ 4)$：两个不相交对换，大小 3
   - $(1\ 2\ 3\ 4)$：4-轮换，大小 6
   - 类方程：$24 = 1 + 6 + 8 + 3 + 6$

#### 解题步骤

**求对称群中的共轭类和类方程：**
1. 列举 $n$ 的所有整数划分（每个划分对应一种轮换型）。
2. 为每种轮换型选取一个代表元。
3. 计算每种轮换型对应的共轭类大小（使用公式或组合计数）。
4. 验证类方程：所有共轭类大小之和等于 $|S_n| = n!$。

**求置换的阶：**
1. 将置换分解为不相交轮换的乘积。
2. 取各轮换长度的最小公倍数。

#### 对应习题

- **idx 1**: 计算 $S_5$ 中 $(1\ 2\ 3)(4\ 5)$ 的阶 — lcm(3, 2)
- **idx 10**: 求 $S_4$ 的共轭类个数、代表元和类方程

#### 竞赛拓展：二面体群 $D_8$ 的结构

二面体群 $D_8 = \langle r, s \mid r^4 = s^2 = e, srs = r^{-1} \rangle$ 是 8 阶非 Abel 群，其结构是竞赛中的高频考点。

**元素分类**：
- 旋转子群 $\langle r \rangle \cong \mathbb{Z}_4$：$\{e, r, r^2, r^3\}$（4 个元素，其中 $\mathrm{ord}(r) = 4$，$\mathrm{ord}(r^2) = 2$）。
- 反射元素：$\{s, sr, sr^2, sr^3\}$（4 个元素，每个的阶均为 2，即对合）。

**中心**：$Z(D_8) = \{e, r^2\}$（仅 2 个元素）。$r^2$ 与所有元素交换，因为 $r^2 s = s r^{-2} = s r^2$。

**换位子群与 Abel 化**：
- $D_8' = [D_8, D_8] = \langle r^2 \rangle \cong \mathbb{Z}_2$（由换位子 $[r, s] = r s r^{-1} s^{-1} = r^2$ 生成）。
- Abel 化 $D_8/D_8' \cong \mathbb{Z}_2 \times \mathbb{Z}_2$（4 阶 Klein 四元群）。

**子群结构**（10 个子群）：
| 子群 | 阶 | 正规性 | 说明 |
|------|----|--------|------|
| $\{e\}$ | 1 | 正规 | 平凡子群 |
| $\langle r^2 \rangle = \{e, r^2\}$ | 2 | 正规 | 中心子群 |
| $\langle s \rangle = \{e, s\}$ | 2 | 非正规 | 反射子群 |
| $\langle sr \rangle = \{e, sr\}$ | 2 | 非正规 | 反射子群 |
| $\langle sr^2 \rangle = \{e, sr^2\}$ | 2 | 非正规 | 反射子群 |
| $\langle sr^3 \rangle = \{e, sr^3\}$ | 2 | 非正规 | 反射子群 |
| $\langle r \rangle \cong \mathbb{Z}_4$ | 4 | 正规 | 指数为 2 |
| $\{e, r^2, s, sr^2\} \cong \mathbb{Z}_2 \times \mathbb{Z}_2$ | 4 | 正规 | Klein 四元群 |
| $\{e, r^2, sr, sr^3\} \cong \mathbb{Z}_2 \times \mathbb{Z}_2$ | 4 | 正规 | Klein 四元群 |
| $D_8$ 自身 | 8 | 正规 | 平凡 |

---

### 模块5：Sylow定理

#### 核心概念

- **Sylow $p$-子群**：设 $|G| = p^k \cdot m$（$p \nmid m$），则 $G$ 的 $p^k$ 阶子群称为 Sylow $p$-子群。
- **$n_p$**：$G$ 中 Sylow $p$-子群的个数。

#### Sylow三大定理

**Sylow第一定理（存在性）**：若 $p^k \mid |G|$，则存在 $p^k$ 阶子群；特别地，Sylow $p$-子群存在。

**Sylow第二定理（共轭性）**：所有 Sylow $p$-子群相互共轭。

**Sylow第三定理（计数）**：
1. $n_p \equiv 1 \pmod{p}$
2. $n_p \mid m$（其中 $|G| = p^k \cdot m$，$p \nmid m$）

#### 常用公式

1. **$n_p$ 的约束**：$n_p \equiv 1 \pmod{p}$ 且 $n_p \mid m$
2. **$S_4$ 的 Sylow 2-子群**：$|S_4| = 24 = 2^3 \times 3$，$p$-子群阶为 $2^3 = 8$。
   - $n_2 \equiv 1 \pmod{2}$，$n_2 \mid 3$ $\Rightarrow$ $n_2 \in \{1, 3\}$
   - 通过验证排除 $n_2 = 1$（否则唯一的 Sylow 2-子群在 $S_4$ 中正规，但 $S_4$ 至少有2个不同的8阶子群，它们分别同构于 $D_4$）
   - 故 $n_2 = 3$

#### 解题步骤

**求 Sylow $p$-子群的个数：**
1. 分解 $|G| = p^k \cdot m$（$p \nmid m$）。
2. 列出满足 $n_p \equiv 1 \pmod{p}$ 且 $n_p \mid m$ 的所有可能值。
3. 若可能值不唯一，通过以下方式排除：
   - 检查是否有理由排除 $n_p = 1$（如群不是 $p$-群与平凡群含交错的情况）。
   - 利用 Sylow子群的结构信息（如已知子群同构类型时列举它们）。
   - 利用群作用的论证（如 $G$ 在 Sylow $p$-子群的共轭类上的作用诱导同态到 $S_{n_p}$）。

#### 对应习题

- **idx 12**: 求 $S_4$ 中 Sylow 2-子群的个数 $n_2$

---

### 模块6：环论基础

#### 核心概念

- **环**：非空集合 $R$ 配备加法（Abel群）与乘法（满足结合律和分配律）。不一定有乘法单位元（若需要，称为含幺环）。
- **零因子**：非零元素 $a \in R$ 称为零因子，若存在非零 $b \in R$ 使得 $ab = 0$（或 $ba = 0$）。
- **整环**：无非零零因子的含幺交换环。
- **单位（可逆元）**：$a \in R$ 称为单位若存在 $b \in R$ 使得 $ab = ba = 1$。
- **域**：每个非零元都是单位的含幺交换环。
- **理想**：子集 $I \subseteq R$ 是加法子群且对任意 $r \in R, a \in I$ 有 $ra \in I$（左理想）且 $ar \in I$（右理想）。
- **商环**：$R/I$，其中元素为加法陪集。
- **极大理想**：真理想 $M \subsetneq R$，使得不存在理想 $I$ 满足 $M \subsetneq I \subsetneq R$。等价于 $R/M$ 是域。
- **素理想**：真理想 $P$，使得若 $ab \in P$ 则 $a \in P$ 或 $b \in P$。等价于 $R/P$ 是整环。

#### 常用公式

1. **$\mathbb{Z}_n$ 中的零因子**：非零元 $a$ 是零因子当且仅当 $\gcd(a, n) > 1$。
2. **$\mathbb{Z}_n$ 中的单位**：$a$ 是单位当且仅当 $\gcd(a, n) = 1$。
3. **$\mathbb{Z}_n$ 是域当且仅当 $n$ 是素数**。
4. **$\mathbb{Z}[x]$ 中的理想 $\langle 2, x \rangle$**：
   - $\mathbb{Z}[x] / \langle 2, x \rangle \cong \mathbb{Z}_2$（因为 $x \equiv 0$ 且系数模2约化）
   - $\mathbb{Z}_2$ 是域，故 $\langle 2, x \rangle$ 是极大理想（也是素理想）。

#### 解题步骤

**求 $\mathbb{Z}_n$ 中的所有零因子：**
1. 对每个非零 $a \in \{1, 2, \ldots, n-1\}$，计算 $\gcd(a, n)$。
2. 若 $\gcd(a, n) > 1$，则 $a$ 是零因子。
3. 若 $\gcd(a, n) = 1$，则 $a$ 是单位（可逆元）而非零因子。

**判定极大理想：**
1. 计算商环 $R/I$ 的结构。
2. 若 $R/I$ 是域，则 $I$ 是极大理想。
3. 若 $R/I$ 是整环，则 $I$ 是素理想。
4. 注：在含幺交换环中，极大理想必为素理想；素理想不一定为极大理想。

**证明 $\mathbb{Z}/n\mathbb{Z}$ 是域当且仅当 $n$ 是素数：**
- $( \Rightarrow )$：若 $\mathbb{Z}_n$ 是域，则它是整环（无零因子）。若 $n$ 为合数，存在 $1 < a, b < n$ 使 $n = ab$，则 $a \cdot b \equiv 0$ 但 $a, b \neq 0$，矛盾。
- $( \Leftarrow )$：若 $n$ 是素数，对任意 $a \in \mathbb{Z}_n \setminus \{0\}$，$\gcd(a, n) = 1$。由 Bezout 恒等式，存在 $x, y$ 使 $ax + ny = 1$，即 $ax \equiv 1 \pmod{n}$，$a$ 有乘法逆元。

#### 对应习题

- **idx 2**: 求 $\mathbb{Z}_{12}$ 中的所有零因子
- **idx 7**: 判断 $\mathbb{Z}[x]$ 中理想 $\langle 2, x \rangle$ 是否为极大理想
- **idx 17**: 证明：$\mathbb{Z}/n\mathbb{Z}$ 是域当且仅当 $n$ 是素数

#### 竞赛拓展：多项式整数根的封闭集（rich集）

**定义**：整数子集 $S \subseteq \mathbb{Z}$ 称为 rich 集，若存在非常数多项式 $P \in \mathbb{Z}[x]$ 使得
$$S = \{a \in \mathbb{Z} : P(a) \in S\}$$
即 $P$ 将 $S$ 的补集中的整数全部"排斥"到 $S$ 之外，而 $S$ 自身在 $P$ 作用下保持封闭（$P(S) \subseteq S$ 不一定成立，但若某个整数的 $P$ 值落在 $S$ 中，则该整数必在 $S$ 中）。

**核心结论**：
- 有限 rich 集必为 $\{-1, 0, 1\}$ 的子集或其平移（即形如 $\{t-1, t, t+1\}$ 或其子集）。
- 无限 rich 集有更丰富结构，但与算术级数密切相关。
- 判别方法：若给定 $S$，需构造多项式 $P$ 使得 $P(a) \in S \Rightarrow a \in S$ 且反向也成立（即 $a \in S \Rightarrow P(a) \in S$）。常取 $P(x) = x^k$ 或 $P(x) = (x-a_1)(x-a_2)\cdots(x-a_k) + x$ 等形式。

**与不动点集合的区别**：
- 若 $F = \{a \in \mathbb{Z} : P(a) = a\}$（不动点集），则 $F$ 是 rich 集（取 $P$ 自身即可）。
- 但 rich 集远不止于此：$S = \{-1, 0, 1\}$ 是 rich 集（取 $P(x) = x^3$，注意 $P(2)=8 \notin S$，$P(-2)=-8 \notin S$，而 $P(1)=1, P(0)=0, P(-1)=-1$ 均在 $S$ 中），但它不是任何多项式的不动点集。

**常见解题思路**：
1. 对给定 $S$，尝试构造多项式 $P$ 使得 $P$ 在 $S$ 上的取值在 $S$ 内，而在 $S$ 外取值在 $S$ 外。
2. 利用 $P$ 的单调性和增长性控制值域与 $S$ 的关系。
3. 对有限集，利用 Lagrange 插值或多项式余数定理构造合适的 $P$。

---

### 模块7：多项式与域扩张

#### 核心概念

- **多项式环**：$R[x]$ 表示系数在环 $R$ 中的全体多项式构成的环。
- **不可约性**：多项式 $f \in F[x]$（$F$ 为域）称为不可约若它不能分解为两个更低次多项式的乘积。
- **Eisenstein判据**：若存在素数 $p$ 使得 $p \mid a_i$（对所有 $i < n$），$p \nmid a_n$，且 $p^2 \nmid a_0$，则 $f(x)$ 在 $\mathbb{Z}[x]$ 中不可约，进而在 $\mathbb{Q}[x]$ 中不可约。
- **分圆多项式**：$\Phi_n(x) = \prod_{\substack{1 \le k \le n \\ \gcd(k,n)=1}} (x - e^{2\pi i k / n})$。$\Phi_n(x) \in \mathbb{Z}[x]$ 且在 $\mathbb{Q}$ 上不可约。
  - $\Phi_5(x) = x^4 + x^3 + x^2 + x + 1 = \frac{x^5 - 1}{x - 1}$
- **域扩张**：$F \subseteq E$，$E$ 可视为 $F$ 上的向量空间，维数称为扩张次数 $[E : F]$。
- **塔定理**：若 $F \subseteq K \subseteq E$，则 $[E : F] = [E : K] \cdot [K : F]$。
- **单扩张**：$F(\alpha)$ 是包含 $F$ 和 $\alpha$ 的最小子域。若 $\alpha$ 在 $F$ 上代数（存在非零多项式 $f \in F[x]$ 使 $f(\alpha) = 0$），则 $[F(\alpha) : F] = \deg(m_\alpha(x))$，其中 $m_\alpha(x)$ 为 $\alpha$ 的极小多项式。
- **分裂域不能只凭“加入 $i$”判断**：对 $x^4+a$ 的根式表示，先写出全部根及所需单位根，再逐层用塔定理计算次数。比如实根 $\alpha$ 与 $\zeta_8$ 同时出现时，分裂域是 $\mathbb Q(\alpha,\zeta_8)$；$\mathbb Q(\alpha,i)$ 一般还缺少 $\sqrt2$，不能直接当作同一个域。必须检查单位根域与根式域的交、各自的极小多项式及是否线性无关。

#### 常用公式

1. **塔定理**：$[E:F] = [E:K][K:F]$
2. **基的构造**：若 $\{e_i\}$ 是 $K$ 在 $F$ 上的基，$\{f_j\}$ 是 $E$ 在 $K$ 上的基，则 $\{e_i f_j\}$ 是 $E$ 在 $F$ 上的基。
3. **$\mathbb{Q}(\sqrt{2}, \sqrt{3})$ 的扩张次数**：
   - $[\mathbb{Q}(\sqrt{2}) : \mathbb{Q}] = 2$（极小多项式 $x^2 - 2$）
   - $[\mathbb{Q}(\sqrt{2}, \sqrt{3}) : \mathbb{Q}(\sqrt{2})] = 2$（$\sqrt{3} \notin \mathbb{Q}(\sqrt{2})$，极小多项式 $x^2 - 3$）
   - $[\mathbb{Q}(\sqrt{2}, \sqrt{3}) : \mathbb{Q}] = 2 \times 2 = 4$
   - 基：$\{1, \sqrt{2}, \sqrt{3}, \sqrt{6}\}$

#### 解题步骤

**判断多项式在 $\mathbb{Q}$ 上的可约性：**
1. 尝试有理根检验（有理根必为常数项因子除以首项系数因子）。
2. 若无可约的低次分解迹象，检查是否为分圆多项式。
3. 对分圆多项式$\Phi_p(x)$（$p$素数），使用代换 $x \to x+1$ 后应用 Eisenstein 判据。
4. 或者利用模 $p$ 约化法（若在 $\mathbb{F}_p$ 上不可约，则在 $\mathbb{Q}$ 上不可约）。

**求域扩张的次数与基：**
1. 使用塔定理逐次扩张。
2. 求每个单扩张的极小多项式和次数。
3. 验证相邻扩张中新增元素是否属于前一步的扩张（通过反证法）。
4. 给出基的构造。

**求分裂域（含 Galois 扩张判别）：**
1. 由一个根生成根式域后，列出其余根所需的单位根（例如四次根式常出现 $\zeta_8$）。
2. 写成 $F(\alpha,\zeta)$，不要用”根式域为实域、单位根域含复数”一句话就断言交为 $F$；应明确检查可能的二次子域。
3. 用塔定理逐层给出次数；若选择了 $i$ 而不是 $\zeta_8$，还要说明 $\sqrt2$ 是否已在已有域中。
4. 最后说明分裂域是特征零域上可分多项式的分裂域，因而为 Galois 扩张。

**求三次根式扩张中的极小多项式（降幂展开法）：**
1. 设 $\alpha = \sqrt[3]{a} + \sqrt[3]{b}$，考虑域塔 $\mathbb{Q} \subseteq \mathbb{Q}(\sqrt[3]{a}) \subseteq \mathbb{Q}(\sqrt[3]{a}, \sqrt[3]{b})$。
2. 确定基：当 $\sqrt[3]{a} \notin \mathbb{Q}(\sqrt[3]{b})$（即 $\sqrt[3]{a}/\sqrt[3]{b}$ 不是有理数的立方根）时，$\mathbb{Q}(\sqrt[3]{a}, \sqrt[3]{b})$ 在 $\mathbb{Q}$ 上的扩张次数为 9，基为 $\{1, \sqrt[3]{a}, \sqrt[3]{b}, \sqrt[3]{a^2}, \sqrt[3]{b^2}, \sqrt[3]{ab}, \sqrt[3]{a^2b}, \sqrt[3]{ab^2}, \sqrt[3]{a^2b^2}\}$。
3. 将 $\alpha^k$（$k = 0, 1, \ldots, 9$）用基线性表示：逐次展开 $(\sqrt[3]{a} + \sqrt[3]{b})^k$，利用 $\sqrt[3]{a}^3 = a$ 和 $\sqrt[3]{b}^3 = b$ 降幂。
4. 由于基的维度为 9 而 $\{1, \alpha, \alpha^2, \ldots, \alpha^9\}$ 有 10 个元素，它们必定线性相关。求解线性方程组得到极小多项式 $m_\alpha(x)$（通常次数 $\le 9$）。
5. 验证：极小多项式的次数等于 $[\mathbb{Q}(\alpha) : \mathbb{Q}]$，且 $\mathbb{Q}(\alpha) \subseteq \mathbb{Q}(\sqrt[3]{a}, \sqrt[3]{b})$。

#### 对应习题

- **idx 8**: 判断 $x^4 + x^3 + x^2 + x + 1$ 在 $\mathbb{Q}$ 上是否可约
- **idx 11**: 求 $[\mathbb{Q}(\sqrt{2}, \sqrt{3}) : \mathbb{Q}]$ 及 $\mathbb{Q}$-基

#### 竞赛拓展：三次根式扩张的降幂展开与极小多项式

设 $\alpha = \sqrt[3]{a} + \sqrt[3]{b}$，求其在 $\mathbb{Q}$ 上的极小多项式。核心思路是利用域扩张的塔 $\mathbb{Q} \subseteq \mathbb{Q}(\sqrt[3]{a}) \subseteq \mathbb{Q}(\sqrt[3]{a}, \sqrt[3]{b})$ 构造基，将 $\alpha^k$ 用基线性表示后求解线性关系。

**关键结论**：
- $[\mathbb{Q}(\sqrt[3]{a}, \sqrt[3]{b}) : \mathbb{Q}] = 9$ 当且仅当 $\sqrt[3]{a} \notin \mathbb{Q}(\sqrt[3]{b})$（即 $\sqrt[3]{a}/\sqrt[3]{b} \notin \mathbb{Q}$ 且三者的乘积关系不足以降次）。
- 若 $\sqrt[3]{a}/\sqrt[3]{b} \in \mathbb{Q}$，则扩张次数退化为 3（因为其中一个根式可用另一个的有理倍数表示）。
- 直接立方 $\alpha^3 = a + b + 3\sqrt[3]{ab}(\sqrt[3]{a} + \sqrt[3]{b}) = a + b + 3\sqrt[3]{ab}\,\alpha$ 会丢失信息（得到的关系中仍含 $\sqrt[3]{ab}$），需要配合更高次幂消去交叉项，最终求得极小多项式。

**降幂展开步骤**：
1. 确定 $\mathbb{Q}(\sqrt[3]{a}, \sqrt[3]{b})$ 在 $\mathbb{Q}$ 上的基（9 维或更低）。
2. 计算 $\alpha^k$（$k = 0, 1, \ldots, 9$）在基下的坐标向量。
3. 解线性方程组 $\sum c_k \alpha^k = 0$，得到极小多项式的系数。
4. 验证所得多项式在 $\mathbb{Q}$ 上不可约（可通过模 $p$ 约化或代换后使用 Eisenstein 判据）。

#### 竞赛拓展：分裂域、扩张次数与 Galois 扩张判别

对形如 $x^n + a$（$a \in \mathbb{Q}$）的多项式，求分裂域及扩张次数，判断是否为 Galois 扩张时，必须先按常数项的符号写根；不能把两个不同的根式生成域混为一谈。以 $x^4+a$ 为例：

**完整判断流程**：
1. **先代回再写出全部根**：若 $a>0$，令 $r=\sqrt[4]{a}>0$，则 $r^4+a=2a\ne0$，所以 $r$ 不是根；四根应写为 $r\zeta_8,r\zeta_8^3,r\zeta_8^5,r\zeta_8^7$。若 $a<0$，令 $r=\sqrt[4]{-a}$，才有根 $r,ir,-r,-ir$。
2. **确定所需单位根域**：在 $a>0$ 的情形，先写候选分裂域为 $\mathbb{Q}(r,\zeta_8)$；$\zeta_8=(1+i)/\sqrt2$，不能把它未经证明地替换成 $i$。在 $a<0$ 的情形，根的比值只需要四次单位根，候选域才可写成 $\mathbb{Q}(r,i)$。
3. **证明根式域次数并检查交域**：使用 Eisenstein 判据（若 $a$ 的素因子满足条件）或代换法验证相应根式的极小多项式；再逐层检查新增的 $i$、$\sqrt2$ 或 $\zeta_8$ 是否已在已有域中。不得因两个域都含复数就断言它们相等。
4. **用塔定理计算具体次数**：把实际使用的每个生成元对应的次数相乘，并给出交域/不包含关系的理由；不存在适用于所有 $a$ 的固定“$2\cdot4=8$”结论。
5. **Galois 扩张判别**：分裂域是特征零域上可分多项式的分裂域，因此必为 Galois 扩张。

**常见陷阱**：
- 对 $x^4+a$（$a>0$）把正实 $\sqrt[4]{a}$ 错当成根，随后错误写成 $\mathbb{Q}(\sqrt[4]{a},i)$ 并漏掉 $\zeta_8$ 或 $\sqrt2$。
- $\mathbb{Q}(\alpha,i)$ 只有在已证明它包含所需单位根时，才可与 $\mathbb{Q}(\alpha,\zeta_8)$ 等同；“$i=\zeta_8^2$”不能反向推出 $\zeta_8\in\mathbb{Q}(i)$。
- 对一般的 $x^n+a$，单位根的阶由根的实际辐角决定，先列根再决定需要 $\zeta_n$ 还是 $\zeta_{2n}$。

---

### 模块8：有限域

#### 核心概念

- **有限域的存在性与唯一性**：对每个素数幂 $q = p^n$，存在唯一的 $q$ 元有限域（记作 $\mathbb{F}_q$），且任意有限域的阶必为素数幂。
- **有限域的构造**：$\mathbb{F}_{p^n} \cong \mathbb{F}_p[x] / (f(x))$，其中 $f(x)$ 是 $\mathbb{F}_p$ 上的 $n$ 次不可约多项式。
- **乘法群**：$\mathbb{F}_q^\times = \mathbb{F}_q \setminus \{0\}$ 是 $q-1$ 阶循环群。
- **本原元**：乘法群 $\mathbb{F}_q^\times$ 的生成元，其阶为 $q-1$。

#### 常用公式

1. **乘法群的阶**：$|\mathbb{F}_q^\times| = q - 1$
2. **$\mathbb{F}_8 = \mathbb{F}_2[x]/(x^3 + x + 1)$**：
   - 令 $\alpha$ 为 $x$ 在商环中的像，满足 $\alpha^3 + \alpha + 1 = 0$
   - $\mathbb{F}_8^\times$ 是7阶循环群，7是素数
   - 若 $\alpha \neq 0, 1$，则 $\mathrm{ord}(\alpha) = 7$（素数阶循环群中任意非单位元的阶等于群的阶）

#### 解题步骤

**求有限域中元素的阶：**
1. 确定乘法群的阶 $q-1$。
2. 因式分解 $q-1$。
3. 对元素 $\alpha$，验证 $\alpha^{(q-1)/p} \neq 1$ 对所有 $p \mid (q-1)$ 的素因子 $p$ 成立，则 $\alpha$ 为乘法群的生成元，阶为 $q-1$。
4. 特别地，若 $q-1$ 是素数，则任何非零非1元素的阶均为 $q-1$。

#### 对应习题

- **idx 9**: 在 $\mathbb{F}_8 = \mathbb{F}_2[x]/(x^3+x+1)$ 中求 $\alpha$ 的阶

---

### 模块9：有限Abel群分类

#### 核心概念

- **有限Abel群的结构定理**：每个有限Abel群同构于循环 $p$-群的直积，且这种分解在循环因子的阶（初等因子）的次序下是唯一的。
- **初等因子**：将 $|G|$ 分解为素数幂 $|G| = \prod p_i^{e_i}$，再对每个素数幂 $p_i^{e_i}$ 考虑其划分。每个划分对应此 $p$-部分分解为循环 $p$-群的直积方式。
- **不变因子**：将初等因子按一定方式合并（每个素数幂取对应的循环因子），得到的因子序列 $d_1 \mid d_2 \mid \cdots \mid d_k$ 且 $d_1 d_2 \cdots d_k = |G|$。
- **同构类个数 = $\prod$（各素数幂的划分数）**。

#### 常用公式

对于 $|G| = 36 = 2^2 \times 3^2$：

1. **2-部分的划分**：$4=2^2$ 的划分为 $\{[4], [2,2]\}$（2种）
2. **3-部分的划分**：$9=3^2$ 的划分为 $\{[9], [3,3]\}$（2种）
3. **组合**：$2 \times 2 = 4$ 种互不同构的有限Abel群：
   - $[4] \times [9] \cong \mathbb{Z}_4 \times \mathbb{Z}_9 \cong \mathbb{Z}_{36}$
   - $[4] \times [3,3] \cong \mathbb{Z}_4 \times \mathbb{Z}_3 \times \mathbb{Z}_3 \cong \mathbb{Z}_3 \times \mathbb{Z}_{12}$
   - $[2,2] \times [9] \cong \mathbb{Z}_2 \times \mathbb{Z}_2 \times \mathbb{Z}_9 \cong \mathbb{Z}_2 \times \mathbb{Z}_{18}$
   - $[2,2] \times [3,3] \cong \mathbb{Z}_2 \times \mathbb{Z}_2 \times \mathbb{Z}_3 \times \mathbb{Z}_3 \cong \mathbb{Z}_6 \times \mathbb{Z}_6$

#### 解题步骤

**分类给定阶的全部有限Abel群：**
1. 将 $|G|$ 分解为素数幂的乘积 $|G| = \prod p_i^{e_i}$。
2. 对每个 $p_i^{e_i}$，写出 $e_i$ 的所有整数划分（即 $p$ 部分所有可能的循环分解）。
3. 所有 $p$ 部分的组合给出全部同构类。
4. 将每个组合化为最简形式（利用 $\mathbb{Z}_a \times \mathbb{Z}_b \cong \mathbb{Z}_{ab}$ 当 $\gcd(a,b) = 1$）。

#### 对应习题

- **idx 13**: 确定所有互不同构的36阶有限Abel群

---

## 模块速查：通用解题方法论

### 1. 题型识别

拿到题目后首先判断：

| 题型特征 | 对应模块 |
|---------|---------|
| "求XX群中元素的阶" / "置换的阶" | 模块1：群的基本概念 |
| "求所有子群" / "陪集分解" / "商群的阶" | 模块2：子群与商群 |
| "求同态的核与像" / "证明同构定理" | 模块3：群同态与同构定理 |
| "共轭类" / "类方程" / "对称群$S_n$" | 模块4：对称群与群作用 |
| "Sylow子群" / "$n_p$" | 模块5：Sylow定理 |
| "零因子" / "极大理想" / "Z_n是域" | 模块6：环论基础 |
| "多项式可约" / "域扩张次数" / "基" | 模块7：多项式与域扩张 |
| "有限域" / "$\mathbb{F}_q$" / "本原元" | 模块8：有限域 |
| "Abel群分类" / "同构类" / "结构定理" | 模块9：有限Abel群分类 |
| "证明群是Abel群" / "满足XX性质的群" | 模块1（证明） |
| "证明子群的性质"（正规性、循环性等） | 模块2（证明） |
| "证明整环/域/理想的判定" | 模块6（证明） |
| "证明Cauchy定理" / "同构定理" | 模块3/其他（证明） |

### 2. 方法选择

| 问题类型 | 首选方法 | 备选方法 |
|---------|---------|---------|
| 求循环群中元素的阶 | $\mathrm{ord}(a) = n / \gcd(a, n)$ | 逐次加法验证 |
| 求置换的阶 | 分解为不相交轮换，取lcm | 逐次幂乘检验 |
| 求所有子群 | 枚举正因子，对应生成元 | 通过子群判定条件逐个验证 |
| 求陪集分解 | 由 Lagrange 定理确定陪集数，选代表元 | 逐一加法生成 |
| 求同态的核与像 | 直接解同余方程 / $\operatorname{im}(\varphi) = \langle \gcd(k,n) \rangle$ | 穷举验证 |
| 求共轭类与类方程 | 列举所有轮换型（整数划分），公式计数 | 直接计算共轭类 |
| 求Sylow子群个数 | Sylow第三定理 $n_p \equiv 1 \pmod{p}$ 且 $n_p \mid m$ | 构造具体子群 |
| 求零因子 | 计算 $\gcd(a, n)$ | 两两乘法验证 |
| 判定极大理想 | 计算 $R/I$ 是否为域 | 素理想+极大理想关系 |
| 判定多项式可约 | 有理根检验 / Eisenstein判据 | 模p约化 / 分圆多项式识别 |
| 求域扩张次数与基 | 塔定理逐次扩张 | 直接构造基 |
| 求有限域中元素阶 | 因式分解 $q-1$ | 逐一验证各阶 |
| 分类有限Abel群 | 素数幂分解 + 划分枚举 | 中国剩余定理 |

### 3. 结果验证

- **阶的整除性**：元素的阶必整除群的阶（Lagrange定理）
- **直积阶的验证**：$|\ker(\varphi)| \cdot |\operatorname{im}(\varphi)| = |G|$（同态基本定理）
- **类方程验证**：所有共轭类大小之和 = 群的阶
- **陪集验证**：所有陪集的并 = 群，且互不相交
- **Sylow定理验证**：$n_p \equiv 1 \pmod{p}$ 且 $n_p$ 整除 $m$
- **Abel群验证**：初等因子的积 = 群的阶
- **域扩张验证**：塔定理 $[E:F] = n$，基的大小 = $n$
- **sympy 独立验证**：对计算题结果用独立方法验算

---

## 模块速查：sympy 验证技巧

本节给出可供 Python 生成阶段使用的 SymPy 核验思路，覆盖群论、环论、域论的核心计算；提示资料本身不提供可直接运行的程序。

### 置换运算

```python
from sympy.combinatorics import Permutation

# 创建一个置换（S_5 中的元素）
sigma = Permutation(0, 1, 2)(3, 4)  # 即 (1 2 3)(4 5)，注意 sympy 使用0-index

# 求置换的阶
order = sigma.order()  # 返回 6

# 求置换的逆
sigma_inv = sigma ** (-1)

# 置换的乘法（从右到左）
tau = Permutation(1, 2)(3, 4)
product = sigma * tau  # 先应用 tau 再应用 sigma

# 分解为不相交轮换
cycles = sigma.cyclic_form  # 返回 [[0, 1, 2], [3, 4]]

# 验证幂
identity = sigma ** order  # 应为恒等置换
```

### 数论基础运算

```python
from sympy import gcd, lcm, factorint, divisors, isprime, nextprime

# 最大公约数与最小公倍数
g = gcd(12, 30)      # 6
l = lcm(3, 2)        # 6

# 整数分解
f = factorint(36)     # {2: 2, 3: 2}

# 求 n 的所有正因子（用于子群格）
divs = divisors(18)   # [1, 2, 3, 6, 9, 18]

# 素数判定
isprime(17)           # True
```

### 循环群中元素的阶

```python
from sympy import gcd

# 在加法循环群 Z_n 中，元素 a 的阶
def order_mod_n(a, n):
    g = gcd(a, n)
    return n // g

# 例：idx 0 - Z_30 中 12 的阶
order_mod_n(12, 30)  # 5

# 例：idx 3 - Z_18 的所有子群
n = 18
for d in divisors(n):
    generator = n // d
    print(f"子群 <{generator}> 的阶为 {d}")
```

### 陪集分解

```python
from sympy import gcd

# 例：idx 4 - Z_15 中 H=<5> 的陪集
n = 15
H_gen = 5
H_size = n // gcd(H_gen, n)  # 3
num_cosets = n // H_size     # 5

H = [k * H_gen % n for k in range(H_size)]  # [0, 5, 10]
all_cosets = []
for a in range(num_cosets):
    coset = [(a + h) % n for h in H]
    all_cosets.append(coset)
# 验证覆盖
all_elements = set()
for c in all_cosets:
    all_elements.update(c)
assert len(all_elements) == n
```

### 群同态核与像

```python
from sympy import gcd

# 例：idx 5 - φ: Z_12 -> Z_8, φ(1)=2
m, n, k = 12, 8, 2

# 像
im_gen = gcd(k, n)  # 2
im_size = n // im_gen  # 4
# im(φ) = <2> ≅ Z_4

# 核（手动验证）
ker = [x for x in range(m) if (k * x) % n == 0]  # [0, 4, 8]
ker_size = len(ker)  # 3
# 验证: |ker| * |im| = m
assert ker_size * im_size == m  # 3 * 4 = 12
```

### 零因子计算

```python
from sympy import gcd

# 例：idx 2 - Z_12 中的零因子
n = 12
zero_divisors = [a for a in range(1, n) if gcd(a, n) > 1]
# [2, 3, 4, 6, 8, 9, 10]

# 单位为与 n 互素的元素
units = [a for a in range(1, n) if gcd(a, n) == 1]
# [1, 5, 7, 11]
```

### 整数划分（用于共轭类/Abel群分类）

```python
from sympy.utilities.iterables import partitions

# 例：4的划分（S_4的共轭类 / 轮换型）
for p in partitions(4):
    print(p)  # {4:1}, {1:1,3:1}, {2:2}, {2:1,1:2}, {1:4}

# 例：36 = 2^2 × 3^2 的 Abel 群分类
# 2^2 的划分: partitions(2) -> {2:1}, {1:2}  (即 [4] 和 [2,2])
# 3^2 的划分: partitions(2) -> {2:1}, {1:2}  (即 [9] 和 [3,3])
```

### 共轭类与类方程

```python
from sympy.combinatorics import SymmetricGroup

# S_4 的共轭类
S4 = SymmetricGroup(4)
classes = S4.conjugacy_classes()
print(f"共轭类个数: {len(classes)}")  # 5

# 各类大小
class_sizes = [len(c) for c in classes]  # [1, 6, 8, 3, 6]
print(f"类方程: {sum(class_sizes)} = {' + '.join(map(str, class_sizes))}")
# 24 = 1 + 6 + 8 + 3 + 6
```

### Sylow 子群

```python
from sympy.combinatorics import SymmetricGroup
from sympy import factorint

# S_4 的 Sylow 2-子群
S4 = SymmetricGroup(4)
n2 = len(S4.sylow_subgroups(2))  # 返回 Sylow 2-子群的个数
# n2 = 3

# 验证 Sylow 第三定理
n = 24
p = 2
factorization = factorint(n)
k = factorization[p]  # 3 (即 2³)
m = n // (p ** k)     # 3
# n_p ≡ 1 (mod p) 且 n_p | m
assert n2 % p == 1 and m % n2 == 0
```

### 多项式操作与可约性判定

```python
from sympy import Poly, symbols, factor
from sympy.polys.specialpolys import cyclotomic_poly
from sympy import cyclotomic_poly

x = symbols('x')

# 构造分圆多项式 Φ_5(x)
phi5 = cyclotomic_poly(5, x)  # x**4 + x**3 + x**2 + x + 1

# 检验可约性
from sympy import factor
f = x**4 + x**3 + x**2 + x + 1
factored = factor(f)  # 在 Q 上不可约，返回自身

# Eisenstein 判据验证：代换 x -> x+1
f_shifted = f.subs(x, x+1).expand()  # x^4 + 5*x^3 + 10*x^2 + 10*x + 5
# 取 p=5，系数全被5整除，常数项不被25整除，故 f 不可约
```

### 有限域运算

```python
from sympy import GF, Poly, symbols

x = symbols('x')

# 在 F_2 上验证 x^3 + x + 1 不可约（用于构造 F_8）
f = Poly(x**3 + x + 1, x, modulus=2)
print(f.is_irreducible)  # True

# 构造 F_8 = F_2[x]/(x^3 + x + 1)
# F_8^x 的元素个数为 7（素数）
# 任意非零非1元素的阶均为 7

# 验证：在 F_8 中
from sympy.polys.galoistools import gf_irreducible
```

---

## 模块速查：习题索引

| idx | 题型 | 难度 | 主题 | 关键知识点 | 核心方法 | 验证方法 |
|-----|------|------|------|-----------|---------|---------|
| 0 | 计算 | 简单 | 循环群中元素的阶 | $\mathbb{Z}_n$中$\mathrm{ord}(a)=n/\gcd(a,n)$ | 求$\gcd(12,30)=6$，得阶=$30/6=5$ | `gcd` + 除法 |
| 1 | 计算 | 简单 | 置换的阶 | 轮换分解，阶=各轮换长度的lcm | $(1\ 2\ 3)$阶=3，$(4\ 5)$阶=2，lcm=6 | `Permutation.order()` |
| 2 | 计算 | 简单 | 环中的零因子 | $\mathbb{Z}_n$中$a$为零因子$\Leftrightarrow \gcd(a,n)>1$ | 逐一计算$\gcd(a,12)$，收集$\gcd>1$者 | `gcd`遍历 |
| 3 | 计算 | 中等 | 子群格 | 循环群子群与正因子一一对应 | 枚举18的正因子1,2,3,6,9,18，对应子群$\langle 18/d\rangle$ | `divisors` + 生成元 |
| 4 | 计算 | 中等 | 陪集分解 | Lagrange定理，$[G:H]=|G|/|H|$ | $|H|=3$，$[G:H]=5$，枚举5个陪集 | Lagrange定理 + 列举验证 |
| 5 | 计算 | 中等 | 群同态的核与像 | $\varphi:\mathbb{Z}_m\to\mathbb{Z}_n$，$\varphi(1)=k$ | $\ker=\{x:n\mid kx\}$，$\operatorname{im}=\langle\gcd(k,n)\rangle$ | 同余方程 + `gcd` |
| 6 | 计算 | 中等 | 商群的阶 | 直积中元素的阶=$lcm$，商群阶=$|G|/|H|$ | $|G|=24$，$\mathrm{ord}((2,3))=lcm(2,2)=2$，$|G/H|=12$ | `lcm` + 除法 |
| 7 | 计算 | 中等 | 极大理想判定 | $R/I$是域$\Leftrightarrow I$为极大理想 | $\mathbb{Z}[x]/\langle2,x\rangle\cong\mathbb{Z}_2$为域 | 商环结构分析 |
| 8 | 计算 | 中等 | 多项式可约性 | Eisenstein判据，分圆多项式$\Phi_n(x)$ | 识别$\Phi_5(x)$，代换$x\to x+1$后用Eisenstein（$p=5$） | `cyclotomic_poly` + Eisenstein |
| 9 | 计算 | 中等 | 有限域的乘法群 | $\mathbb{F}_q^\times$是$q-1$阶循环群 | $|\mathbb{F}_8^\times|=7$（素数），非单位元阶=7 | 乘法群阶分析 |
| 10 | 计算 | 中等 | 共轭类与类方程 | 轮换型决定共轭类 | 枚举5种轮换型，计算各类大小，$24=1+6+8+3+6$ | `SymmetricGroup.conjugacy_classes()` |
| 11 | 计算 | 中等 | 域扩张次数与基 | 塔定理 $[E:F]=[E:K][K:F]$ | 逐次扩张：$[\mathbb{Q}(\sqrt{2}):\mathbb{Q}]=2$，再证$\sqrt{3}\notin\mathbb{Q}(\sqrt{2})$ | 域扩张逻辑 + 塔定理 |
| 12 | 计算 | 困难 | Sylow子群 | Sylow第三定理：$n_p\equiv1\pmod{p}$，$n_p\mid m$ | $n_2\equiv1\pmod{2}$且$n_2\mid3$得$n_2\in\{1,3\}$，排除$n_2=1$ | `SymmetricGroup.sylow_subgroups()` |
| 13 | 计算 | 困难 | 有限Abel群分类 | 结构定理，素数幂的整数划分 | $36=2^2\times3^2$，2-部分2种划分×3-部分2种划分=4种 | `partitions` + 中国剩余定理 |
| 14 | 证明 | 简单 | 群的基本性质 | $a^2=e$对任意$a$成立 | 展开$(ab)^2=e$，利用$a=a^{-1}$推导$ba=ab$ | 代数推导验证 |
| 15 | 证明 | 中等 | 循环群结构 | 循环群的任意子群也是循环群 | 取$H$中指数最小正幂为生成元，带余除法证明 | 带余除法逻辑 |
| 16 | 证明 | 中等 | 正规子群判定 | 指数为2的子群必为正规子群 | 分类讨论$g\in H$和$g\notin H$，陪集覆盖论证 | 陪集分解逻辑 |
| 17 | 证明 | 中等 | 环的基本性质 | $\mathbb{Z}_n$是域$\Leftrightarrow n$为素数 | 必要性：反证合数情形有零因子；充分性：Bezout恒等式 | 整环/域定义逻辑 |
| 18 | 证明 | 困难 | Cauchy定理 | Abel群中$p\mid|G|\Rightarrow\exists p$阶元 | 归纳法：情形1 $p\mid m$用幂；情形2 $p\nmid m$用商群 | 数学归纳法 + 商群 |
| 19 | 证明 | 困难 | 第一同构定理 | $G/\ker(\varphi)\cong\operatorname{im}(\varphi)$ | 构造$\psi(gK)=\varphi(g)$，证良定/同态/单/满 | 映射构造四步法 |
| 20 | 计算 | 中等 | 二面体群$D_8$结构 | $D_8=\langle r,s\mid r^4=s^2=e,srs=r^{-1}\rangle$，中心、换位子群、子群格 | 元素分类（旋转与反射），中心$Z(D_8)=\{e,r^2\}$，$D_8'=\langle r^2\rangle$，列出10个子群并判正规性 | 群论定义验证 |

---

## 模块速查：常见错误与陷阱

### 群的基本概念
1. **混淆加法群与乘法群的阶公式**：在加法循环群 $\mathbb{Z}_n$ 中，$\mathrm{ord}(a) = n/\gcd(a,n)$；在乘法循环群 $\langle g \rangle$ 中，$\mathrm{ord}(g^k) = n/\gcd(k,n)$。前者是元素本身的表示，后者是指数。
2. **计算置换的阶时忘记分解轮换**：置换的阶不是置换的长度或轮换个数，必须是所有不相交轮换长度的最小公倍数（lcm）。
3. **混淆元素的阶与群的阶**：元素的阶整除群的阶（Lagrange定理推论），但两者一般不相等。$\mathbb{Z}_n$ 中生成元的阶等于 $n$，非生成元的阶严格小于 $n$。
4. **证明中忽略单位元的情况**：循环群的子群为循环群时，需单独处理 $H = \{e\}$ 的平凡情况，否则后续取 $\min\{k>0\}$ 可能为空集。
5. **$a^2=e$ 不意味着 $a=e$**：断言 $a^2=e$ 仅意味着 $a = a^{-1}$（自逆），不意味着 $a$ 必为单位元。反例：$S_3$ 中对换 $(1\ 2)^2 = e$ 但 $(1\ 2) \neq e$。

### 子群与商群
6. **商群与陪集的记法混淆**：在加法群中，陪集记作 $a+H$，商群元素是陪集的集合；在乘法群中，陪集记作 $aH$。不要将陪集与群元素混淆。
7. **Lagrange定理的逆不成立**：$|H| \mid |G|$ 不意味着 $H$ 一定是 $G$ 的子群（$A_4$ 没有6阶子群是经典反例）。只有循环群保证了每个因子对应一个子群。
8. **直积中元素阶的计算**：$\mathrm{ord}((a,b)) = \mathrm{lcm}(\mathrm{ord}(a), \mathrm{ord}(b))$，不是 $\mathrm{ord}(a) \cdot \mathrm{ord}(b)$，也不是 $\gcd$。
9. **正规子群判定中陪集覆盖**：$[G:H]=2$ 时 $g \notin H$ 意味着 $gH = G \setminus H$，这个关键推理依赖指数为2的条件（只有两个陪集）。

### 群同态与同构定理
10. **循环群同态中核的计算**：$\varphi: \mathbb{Z}_m \to \mathbb{Z}_n$，$\varphi(1)=k$ 时，核是 $\{x \in \mathbb{Z}_m : kx \equiv 0 \pmod{n}\}$，需同时满足模 $n$ 的整除条件和模 $m$ 的取值范围。核的生成元为 $m / \gcd(m, n/\gcd(k,n))$。
11. **同构定理中映射的良定性验证**：$g_1K = g_2K \Leftrightarrow g_1^{-1}g_2 \in K = \ker(\varphi)$，这是最关键的步骤，需用核的定义来链接。遗漏良定性验证是常见错误。
12. **区分单同态与单射**：$\ker(\varphi) = \{e\}$ 等价于 $\varphi$ 是单同态（injective homomorphism），不是满射。

### 对称群与群作用
13. **共轭类代表元的不唯一性**：一个共轭类可以有多个代表元，标准做法是按轮换型选取代表元。但不同代表元计算出的共轭类大小必须相同。
14. **共轭类大小公式中分母的阶乘因子**：对于轮换型 $1^{c_1}2^{c_2}\cdots n^{c_n}$，分母不仅包括 $i^{c_i}$ 还包括 $c_i!$（相同长度轮换的排列冗余），遗漏 $c_i!$ 会得到错误的大小。
15. **类方程不等于所有共轭类大小之和的平凡恒等式**：类方程实际上是 $|G| = |Z(G)| + \sum [G:C_G(g_i)]$（$g_i$ 取遍非中心共轭类的代表元），给出了群的中心信息和结构约束。
32. **混淆 $D_8$ 的中心与所有对合**：二面体群 $D_8 = \langle r, s \mid r^4 = s^2 = e, srs = r^{-1} \rangle$（8 阶）中，所有反射 $\{s, sr, sr^2, sr^3\}$ 的阶均为 2（对合），但这不意味着它们属于中心。$D_8$ 的中心仅含 $\{e, r^2\}$（2 个元素），因为只有 $r^2$ 与所有元素交换。换位子群 $D_8' = \langle r^2 \rangle \cong \mathbb{Z}_2$，Abel 化 $D_8/D_8' \cong \mathbb{Z}_2 \times \mathbb{Z}_2$ 是 4 阶 Klein 四元群。

### Sylow定理
16. **$n_p$ 可能不等于1不等于一个很大的数**：$n_p \equiv 1 \pmod{p}$ 且 $n_p \mid m$ 是必要条件，但两个条件合在一起可能排除很多值，余下的值仍可能不唯一，需要进一步论证。
17. **将 $n_p \mid |G|$ 与 $n_p \mid m$ 混淆**：Sylow第三定理的第二部分是 $n_p \mid m$（$m$ 是 $|G|$ 去掉 $p$ 幂次后的部分），不是 $n_p \mid |G|$。
18. **排除 $n_p = 1$ 需要理由**：不能随意排除 $n_p = 1$，必须给出具体论证（如存在多个不同的 Sylow 子群，或群不是幂零群等）。

### 环论
19. **混淆零因子与不可逆元**：在一般环中，不是所有非单位元都是零因子。但在 $\mathbb{Z}_n$ 中，二者恰好互补（$\gcd(a,n) > 1$ 为零因子，$\gcd(a,n) = 1$ 为单位）。
20. **$\mathbb{Z}[x]$ 和 $\mathbb{Q}[x]$ 中理想的差异**：$\mathbb{Z}[x]$ 不是主理想整环（PID），例如 $\langle 2, x \rangle$ 不是主理想。在 $\mathbb{Q}[x]$（是PID）中极大理想由不可约多项式生成。
21. **混淆极大理想与素理想**：在含幺交换环中，极大理想必为素理想，但反之不成立。$\langle x \rangle$ 在 $\mathbb{Z}[x]$ 中是素理想但不是极大理想（商环 $\mathbb{Z}[x]/\langle x \rangle \cong \mathbb{Z}$ 是整环但不是域）。
22. **域的定义**：域必须有乘法单位元 $1 \neq 0$，且每个非零元都有乘法逆元。有时会遗漏 $1 \neq 0$ 的条件（排除零环）。
30. **混淆 rich 集的"值域"与"不动点集合"**：rich 集的定义是 $S = \{a \in \mathbb{Z} : P(a) \in S\}$，即 $P$ 将 $S$ 外的整数"排斥"而保持 $S$ 内的整数仍落在 $S$ 中，这与 $P(a) = a$（不动点）或 $P(S) = S$（值域等于自身）不同。多项式次数的选择影响封闭性的传播范围：高次多项式可能引入更大的"排斥力"使得 rich 集变小。有限 rich 集必然与 $\{-1, 0, 1\}$ 或其平移相关。

### 多项式与域扩张
23. **Eisenstein判据不能直接用于分圆多项式**：$\Phi_p(x)$ 本身不满足Eisenstein判据，需要先做代换 $x \to x+1$（或 $x \to x-1$），再用 Eisenstein 判据对 $\Phi_p(x+1)$ 判定。
24. **域扩张中 $\sqrt{3} \notin \mathbb{Q}(\sqrt{2})$ 的证明需要严格**：不能直觉认为"不同根号线性无关"。需假设 $\sqrt{3} = a + b\sqrt{2}$，平方后比较系数推出矛盾。
25. **基的构造需验证线性无关性**：仅仅是 $[E:F] = n$ 加上有 $n$ 个元素不能直接说明它们构成基，还需验证它们线性无关（或生成整个扩张）。
29. **三次根式降幂展开中直接立方的陷阱**：对 $\alpha = \sqrt[3]{a} + \sqrt[3]{b}$，若直接立方得 $\alpha^3 = a + b + 3\sqrt[3]{ab}\,\alpha$，该式中仍含 $\sqrt[3]{ab}$ 无法消去，必须系统地计算 $\alpha^k$ 至 $k=9$（因为扩张次数至多为 9），用 9 维基的线性表示构造线性关系。仅立方一次得到的关系是不充分的，无法确定极小多项式。
31. **分裂域判别中忽略线性无交验证**：判断 $x^n + a$ 的分裂域时，不能仅凭"加入 $i$"或"加入 $\zeta_n$"就写出分裂域。必须严格验证根式域 $\mathbb{Q}(\sqrt[n]{-a})$ 与单位根域 $\mathbb{Q}(\zeta_n)$ 的交是否为 $\mathbb{Q}$（线性无交）。不验证线性无交会错误估计扩张次数（可能小于 $n \cdot \varphi(n)$）。此外，$\mathbb{Q}(\sqrt[4]{-a})$ 可能已包含 $\sqrt{2}$ 等二次无理数，当存在此类"意外包含"时分裂域次数会降低。

### 有限域与Abel群
26. **混淆有限域的加法群和乘法群**：加法群 $\mathbb{F}_q$ 是 $p$ 个 $\mathbb{Z}_p$ 的直和（$p^n$ 阶初等Abel $p$-群），不是循环群（除非 $n=1$）；乘法群 $\mathbb{F}_q^\times$ 是 $q-1$ 阶循环群。
27. **有限Abel群分类中忘记使用中国剩余定理简化**：$\mathbb{Z}_a \times \mathbb{Z}_b \cong \mathbb{Z}_{ab}$ 当且仅当 $\gcd(a,b)=1$（中国剩余定理）。在组合各 $p$ 部分后，需用此定理得到最简形式。
28. **混淆初等因子与不变因子的表示**：初等因子是素数幂（如 $\{4, 2, 9, 3\}$），不变因子通过逐次取lcm得到（如 $d_k$ 为按列取lcm），两者表示同一群的不同方式。

---

## 模块速查：关键定理速查表

### 群论定理

| 定理 | 精确陈述 | 典型应用 | 相关习题 |
|------|---------|---------|---------|
| **Lagrange定理** | 若 $H \le G$（$G$ 有限群），则 $|G| = |H| \cdot [G:H]$，特别地 $|H| \mid |G|$ | 子群的阶必整除群的阶 | idx 4, 6, 12 |
| **Cauchy定理** | 若 $G$ 是有限群，$p$ 是整除 $|G|$ 的素数，则 $G$ 中存在 $p$ 阶元素 | 存在性定理，Sylow定理的基石 | idx 18 |
| **第一同构定理** | 若 $\varphi: G \to H$ 是群同态，则 $G/\ker(\varphi) \cong \operatorname{im}(\varphi)$ | 商群同构的判定 | idx 5, 19 |
| **第二同构定理** | 若 $H \le G$，$N \trianglelefteq G$，则 $H/(H \cap N) \cong HN/N$ | 子群与正规子群的交互 | — |
| **第三同构定理** | 若 $N \trianglelefteq G$，$M \trianglelefteq G$ 且 $N \le M$，则 $(G/N)/(M/N) \cong G/M$ | 嵌套商群的关系 | — |
| **Sylow第一定理** | 若 $p^k \mid |G|$，则存在 $p^k$ 阶子群 | Sylow $p$-子群的存在性 | idx 12 |
| **Sylow第二定理** | $G$ 中所有 Sylow $p$-子群相互共轭 | 结构唯一性（至多共轭） | idx 12 |
| **Sylow第三定理** | $n_p \equiv 1 \pmod{p}$ 且 $n_p \mid m$（其中 $|G|=p^k \cdot m$，$p \nmid m$） | Sylow子群个数计算 | idx 12 |
| **Cayley定理** | 任意群 $G$ 同构于对称群 $S_{|G|}$ 的一个子群 | 群可嵌入对称群 | — |
| **有限Abel群结构定理** | 每个有限Abel群同构于循环 $p$-群的直积，且分解（在次序下）唯一 | Abel群的完全分类 | idx 13 |

### 环论定理

| 定理 | 精确陈述 | 典型应用 | 相关习题 |
|------|---------|---------|---------|
| **极大理想判据** | $M$ 是含幺交换环 $R$ 的极大理想 $\Leftrightarrow$ $R/M$ 是域 | 极大理想的判定 | idx 7 |
| **素理想判据** | $P$ 是含幺交换环 $R$ 的素理想 $\Leftrightarrow$ $R/P$ 是整环 | 素理想的判定 | — |
| **$\mathbb{Z}_n$中单位判定** | $a \in \mathbb{Z}_n$ 是单位 $\Leftrightarrow$ $\gcd(a,n) = 1$ | 可逆元的存在性 | idx 2, 17 |
| **$\mathbb{Z}_n$中零因子判定** | $a \in \mathbb{Z}_n$（非零）是零因子 $\Leftrightarrow$ $\gcd(a,n) > 1$ | 零因子的筛选 | idx 2 |
| **$\mathbb{Z}_n$是域的充要条件** | $\mathbb{Z}_n$ 是域 $\Leftrightarrow$ $n$ 是素数 | 有限域的判定 | idx 17 |
| **Eisenstein判据** | 若存在素数 $p$ 使得 $p \mid a_i$（$i<n$），$p \nmid a_n$，$p^2 \nmid a_0$，则 $f$ 在 $\mathbb{Q}$ 上不可约 | 多项式不可约性 | idx 8 |

### 域论定理

| 定理 | 精确陈述 | 典型应用 | 相关习题 |
|------|---------|---------|---------|
| **塔定理** | 若 $F \subseteq K \subseteq E$，则 $[E:F] = [E:K] \cdot [K:F]$ | 逐次扩张次数计算 | idx 11 |
| **单扩张次数** | 若 $\alpha$ 在 $F$ 上代数，则 $[F(\alpha):F] = \deg(m_\alpha(x))$，其中 $m_\alpha(x)$ 是极小多项式 | 扩张次数的计算 | idx 11 |
| **有限域存在唯一性** | 对任意素数幂 $q = p^n$，存在唯一的 $q$ 元有限域 | 有限域结构 | idx 9 |
| **乘法群结构** | $\mathbb{F}_q^\times$ 是 $q-1$ 阶循环群 | 元素阶的计算 | idx 9 |
| **分圆多项式不可约性** | $\Phi_n(x)$ 在 $\mathbb{Q}$ 上不可约 | 不可约性判定 | idx 8 |

### 对称群定理

| 定理 | 精确陈述 | 典型应用 | 相关习题 |
|------|---------|---------|---------|
| **共轭类=轮换型** | $S_n$ 中两个置换共轭 $\Leftrightarrow$ 它们具有相同的轮换型 | 共轭类的分类 | idx 10 |
| **共轭类大小公式** | 轮换型 $1^{c_1}2^{c_2}\cdots n^{c_n}$ 的共轭类大小为 $\frac{n!}{\prod i^{c_i} \cdot c_i!}$ | 类方程的计算 | idx 10 |
| **类方程** | $|G| = |Z(G)| + \sum_{i=1}^r [G : C_G(g_i)]$，其中 $g_i$ 为非中心共轭类的代表元 | 群结构分析 | idx 10 |
| **置换的阶=轮换长度的lcm** | $\mathrm{ord}(\sigma) = \mathrm{lcm}(\ell_1, \ldots, \ell_r)$ | 元素阶的计算 | idx 1 |

---

## 模块速查：计算题标准解法速查

### 类型A：求循环群中元素的阶
**步骤**：$n / \gcd(a, n)$

例：$\mathbb{Z}_{30}$ 中 $12$ 的阶 = $30 / \gcd(12, 30) = 30/6 = 5$。

### 类型B：求置换的阶
**步骤**：分解为不相交轮换 $\to$ 取各轮换长度的lcm

例：$(1\ 2\ 3)(4\ 5)$ 中，3-轮换届=3，2-轮换届=2，lcm(3,2)=6。

### 类型C：求零因子
**步骤**：对 $a \in \{1,\ldots,n-1\}$，若 $\gcd(a,n) > 1$ 则 $a$ 为零因子

例：$\mathbb{Z}_{12}$ 中零因子 = $\{a \mid 1 \le a \le 11, \gcd(a,12) > 1\} = \{2,3,4,6,8,9,10\}$。

### 类型D：求子群格
**步骤**：枚举 $n$ 的所有正因子 $\{d_i\}$，对每个 $d_i$ 写出子群 $\langle n/d_i \rangle$

例：$\mathbb{Z}_{18}$ 的因子：1,2,3,6,9,18 $\to$ 子群：$\langle 0 \rangle, \langle 9 \rangle, \langle 6 \rangle, \langle 3 \rangle, \langle 2 \rangle, \langle 1 \rangle$。

### 类型E：求陪集分解
**步骤**：(1) $|H| = n/\gcd(g,n)$；(2) 陪集个数 $k = n/|H|$；(3) 取代表元 $0,1,\ldots,k-1$ 各加 $H$

### 类型F：求同态的核与像
**步骤**：$\operatorname{im}(\varphi) = \langle \gcd(k,n) \rangle$；$\ker(\varphi) = \{x \in \mathbb{Z}_m : kx \equiv 0 \pmod{n}\}$

### 类型G：求商群的阶
**步骤**：(1) $|G|$；(2) $|H|$（直积元素阶=lcm）；(3) $|G/H| = |G|/|H|$

### 类型H：判定极大理想
**步骤**：计算 $R/I$，判断是否为域（等价条件）

### 类型I：判断多项式可约性
**步骤**：尝试有理根 $\to$ 识别分圆多项式 $\to$ 代换后 Eisenstein

### 类型J：求域扩张次数与基
**步骤**：塔定理逐次扩张 $\to$ 验证新增元素不属于已有扩张 $\to$ 得次数和基

### 类型K：求Sylow子群个数
**步骤**：(1) $n_p \equiv 1 \pmod{p}$；(2) $n_p \mid m$；(3) 若值不唯一，进一步排除

### 类型L：分类有限Abel群
**步骤**：(1) 分解 $|G| = \prod p_i^{e_i}$；(2) 各 $e_i$ 的划分；(3) 组合得所有同构类

---

## 模块速查：证明题标准策略速查

### 策略1：直接代数推导
**适用**：群的基本性质（idx 14）

模式：从已知条件出发，通过代数恒等式变形得到结论。

### 策略2：带余除法 + 极小性
**适用**：循环群结构（idx 15）

模式：取最小正指数为候选生成元，用带余除法证明任意元素都是它的幂。

### 策略3：陪集覆盖 + 分类讨论
**适用**：正规子群判定（idx 16）

模式：区分 $g \in H$（显然）和 $g \notin H$（利用指数条件及陪集覆盖）。

### 策略4：双向推导（充要条件）
**适用**：环的性质判定（idx 17）

模式：分别证明必要性（反证法）和充分性（构造法/Bezout恒等式）。

### 策略5：数学归纳法
**适用**：Cauchy定理（idx 18）

模式：对 $|G|$ 归纳。基础情形 $|G|=p$；归纳步骤中选取 $a \neq e$，分 $p \mid \mathrm{ord}(a)$ 和 $p \nmid \mathrm{ord}(a)$ 两种情况。

### 策略6：映射构造四步法
**适用**：第一同构定理（idx 19）

模式：(1) 良定性；(2) 同态性；(3) 单射；(4) 满射。四步依次证明。

---

## 模块速查：参考资源

- 配套验证知识提示：`抽象代数验证示例.py`
- 数据集来源：`抽象代数.md`（20题，涵盖全部核心知识点）
- 推荐教材：《抽象代数基础教程》（Rotman）、《代数学》（Hungerford）
- 在线工具：SymPy Live、SageMath

<!-- AUTO-KNOWLEDGE-BEGIN 知识点速查（生成区；按学科提炼的抽象题型方法论，不含任何具体题目） -->

以下速查条目是按学科整理的题型方法论（核心内容/解题路线/易错点），供匹配到的题目作方法参考；条目不含任何具体题目的题面或结论，最终答案仍须独立推导并验证。

## 模块速查：抽象代数：分裂域、扩张次数与 Galois 扩张判别
- 检索词：多项式 polynomial polynomials coefficient 分裂域 splitting field 单位根 root of unity cyclotomic roots 有理数 rational 分布 distribution 扩张 expansion spread growth
- 核心内容：研究有理数域上不可约多项式的分裂域：先由 Eisenstein 判别法（或其它不可约判据）证明不可约，从而确定单个根的扩张次数；再由本原单位根写出全部根的分布，把分裂域表示成根域与单位根域的复合；当两个子扩张在基域上线性无交时，复合域的扩张次数等于两个子扩张次数之积；特征零域上可分多项式的分裂域必为 Galois 扩张。
- 解题路线：填空常以「分裂域是什么、扩张次数多少、是否为 Galois」三连问出现；次数计算先分别求两个子扩张次数再判断线性无交；Galois 性只需抓住「可分多项式之分裂域」这一特征。
- 易错点：把极小多项式的次数直接当作分裂域次数（漏乘单位根部分）；以为根全为实数就忽略复数单位根域；对线性无交性的验证不充分。
- 分步收尾：对 x⁴+a（a>0），先检验正实四次根并非根，再写出实际辐角对应的单位根，检查根式域与单位根域的交及每层次数；不要把任意具体常数的答案或固定次数模板直接套用。对 x⁴+a（a<0）则先比较根式域与四次单位根域，仍须逐层核验。特征零可分 ⇒ 分裂域为 Galois 扩张。

## 模块速查：抽象代数：二面体群的元素、子群与换位子群
- 检索词：group subgroup order 分布 distribution 旋转 rotation orientations cycle cycles ring
- 核心内容：二面体群由旋转与反射两类生成元及共轭关系确定：旋转构成正规循环子群，反射均为二阶元，元素的阶分布可由生成关系直接读出。其四阶子群只有循环群与 Klein 四元群两类，均为 Abel 群；在该群（D₈）中，中心为 {1, r²}（由旋转平方生成）；换位子群亦为 ⟨r²⟩，阶数为 2。
- 解题路线：判断题常混合考察「是否存在更高阶元」「四阶子群是否 Abel」「中心是否只有恒等元」「换位子群阶数」，逐一借助生成关系、共轭公式与阶的性质验证。
- 易错点：混淆反射（二阶）与旋转的阶；误认为中心平凡；忽略换位子群与旋转平方的联系；漏掉四阶子群可能的两类而误判。
- 作答模板（判分口径）：A 错（D₈ 最大阶 4，无 8 阶元）；B 对（四阶子群只有 ⟨r⟩≅C₄ 与 ⟨r²,s⟩≅V₄，均 Abel）；C 错（中心为 {1,r²} 非平凡）；D 对（[r,s]=r²，换位子群=⟨r²⟩ 为 2 阶）⇒ 最终答案 \boxed{B、D}。

<!-- AUTO-KNOWLEDGE-END -->
