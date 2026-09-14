---
name: complex-analysis-verification
description: Use when verifying complex analysis problems with sympy — complex numbers, Cauchy-Riemann equations, Cauchy integral formula, Laurent series, residue theorem, contour integration, conformal mapping, argument principle, and Rouché theorem
---

# 复分析解题与验证技能手册

## 领域边界与路由约定

- 适用范围：全纯函数、Cauchy–Riemann 方程、复积分、Laurent 展开、留数和保形映射。
- 不接管：虚二次域的整数范数题若无复解析条件转离散数学；实变量 Fourier 变换转数学分析。
- 验证契约：先确认解析域、孤立奇点和路径方向，再检查留数、绕数及积分定向，不能把形式级数当收敛展开。

## 概述

本技能手册覆盖本科复分析课程的核心知识体系，包括复数运算与de Moivre公式、解析函数与Cauchy-Riemann方程、Cauchy积分理论与高阶导数公式、Laurent级数与收敛半径、留数定理与围道积分、保形映射（Möbius变换）、零点与极点理论（辐角原理、Rouché定理）、以及调和函数等经典内容。全手册以20道精选习题为骨架，系统梳理每个知识模块的核心概念、常用定理、解题步骤和常见陷阱，并配套验证知识提示，适用于复分析课程的学习、复习与自动解题验证。

---

## 知识点体系

### 模块1：复数运算与de Moivre公式
- 检索词：复数 complex 复数运算 moivre 高次幂 幂次 power exponent 极坐标 polar

#### 核心概念

- **复数的表示**：代数形式 $z = a + bi$（$a, b \in \mathbb{R}$），极坐标形式 $z = r(\cos\theta + i\sin\theta) = re^{i\theta}$。
- **模**：$|z| = \sqrt{a^2 + b^2} = r$。
- **辐角**：$\arg(z) = \theta + 2k\pi$（$k \in \mathbb{Z}$），主值 $\operatorname{Arg}(z) \in (-\pi, \pi]$。
- **共轭复数**：$\overline{z} = a - bi$，满足 $|z|^2 = z\overline{z} = a^2 + b^2$。
- **de Moivre公式**：$(\cos\theta + i\sin\theta)^n = \cos(n\theta) + i\sin(n\theta)$，即 $(e^{i\theta})^n = e^{in\theta}$。
- **复数的n次根**：方程 $z^n = w$ 的 $n$ 个解为 $z_k = \sqrt[n]{|w|} \cdot e^{i(\arg(w) + 2\pi k)/n}$，$k = 0, 1, \ldots, n-1$。

#### 常用公式

1. **极坐标表示**：
   $$z = a + bi \quad\Longrightarrow\quad r = \sqrt{a^2 + b^2},\quad \theta = \arctan\frac{b}{a} \text{（需根据象限调整）}$$

2. **de Moivre公式**：
   $$(r e^{i\theta})^n = r^n e^{in\theta} = r^n(\cos n\theta + i\sin n\theta)$$

3. **复数的幂运算**：
   $$(a+bi)^n = r^n \cdot (\cos n\theta + i\sin n\theta)$$

#### 解题步骤

**求复数的高次幂：**
1. 将复数化为极坐标形式 $re^{i\theta}$，计算 $r = \sqrt{a^2+b^2}$ 和 $\theta$。
2. 使用de Moivre公式 $(re^{i\theta})^n = r^n e^{in\theta}$。
3. 将结果化回代数形式 $x + yi$（利用 $e^{i\theta} = \cos\theta + i\sin\theta$）。
4. 化简三角函数值。

#### 对应习题

- **idx 0**: 求 $(\sqrt{3}+i)^{6}$ 的值 — 极坐标 + de Moivre公式

---

### 模块2：解析函数与Cauchy-Riemann方程
- 检索词：解析 analytic holomorphic 全纯 cauchy-riemann 调和 harmonic 可微 differentiable 共轭 conjugate

#### 核心概念

- **复变函数的导数**：$f'(z_0) = \lim_{h \to 0} \frac{f(z_0 + h) - f(z_0)}{h}$，其中 $h$ 是复数，从各个方向趋于0时极限必须相同。
- **解析函数（全纯函数）**：$f$ 在开集 $D$ 内每一点都可导，则称 $f$ 在 $D$ 内解析。
- **Cauchy-Riemann方程**（必要条件）：设 $f(z) = u(x,y) + iv(x,y)$，其中 $z = x + iy$。若 $f$ 在 $z_0$ 处可导，则在该点：
  $$\frac{\partial u}{\partial x} = \frac{\partial v}{\partial y}, \quad \frac{\partial u}{\partial y} = -\frac{\partial v}{\partial x}$$

- **C-R方程的充分条件**：若 $u, v$ 在区域 $D$ 内有连续的一阶偏导数且在 $D$ 内满足C-R方程，则 $f = u + iv$ 在 $D$ 内解析。
- **调和函数**：$u(x,y)$ 是调和的若 $u_{xx} + u_{yy} = 0$。解析函数的实部和虚部都是调和函数。
- **共轭调和函数**：若 $u$ 是调和函数，存在 $v$（称为 $u$ 的共轭调和函数）使得 $f = u + iv$ 解析。$v$ 通过C-R方程积分求得。

#### 常用公式

1. **Laplace方程**：
   $$\Delta u = u_{xx} + u_{yy} = 0$$

2. **通过C-R方程求共轭调和函数**：
   $$v(x,y) = \int u_x \, dy + \varphi(x)$$
   再利用 $v_x = -u_y$ 确定 $\varphi(x)$。

3. **解析函数重构**：若已知 $u$，则 $f(z) = u + iv$，其中 $v$ 满足 $dv = -u_y\,dx + u_x\,dy$（全微分）。

#### 解题步骤

**判断函数何处解析：**
1. 写出 $u(x,y)$ 和 $v(x,y)$。
2. 计算四个一阶偏导数。
3. 验证C-R方程 $u_x = v_y$ 和 $u_y = -v_x$ 成立的点的集合。
4. 若仅在某些孤立点处满足C-R方程，则函数处处不解析（解析性要求在开邻域内可导）。

**求共轭调和函数：**
1. 验证 $u$ 是调和函数（$u_{xx} + u_{yy} = 0$）。
2. 由 $v_y = u_x$ 对 $y$ 积分得 $v = \int u_x \, dy + \varphi(x)$。
3. 由 $v_x = -u_y$ 确定 $\varphi'(x)$，积分得 $\varphi(x)$。
4. 利用附加条件（如 $f(0) = 1$）确定积分常数。
5. 将 $u + iv$ 整合为仅含 $z$ 的表达式。

#### 对应习题

- **idx 1**: 判断 $f(z) = |z|^2$ 的解析性 — C-R方程仅在 $z=0$ 成立，故处处不解析
- **idx 7**: 验证 $u = e^x\cos y$ 是调和函数并求共轭调和函数 — $v = e^x\sin y$，$f(z) = e^z$
- **idx 14**: 证明C-R方程是解析的必要条件 — 沿实轴和虚轴方向求导

---

### 模块3：Cauchy积分理论
- 检索词：cauchy 积分 integral 围道 contour 环路 closed curve 曲线 路径 path

#### 核心概念

- **Cauchy积分定理**：若 $f$ 在简单闭围道 $C$ 及其内部解析，则 $\oint_C f(z)\,dz = 0$。
- **Cauchy积分公式**：若 $f$ 在简单闭围道 $C$ 及其内部解析，$a$ 在 $C$ 内部，则：
  $$f(a) = \frac{1}{2\pi i} \oint_C \frac{f(z)}{z - a}\,dz$$

- **高阶Cauchy积分公式（Cauchy导数公式）**：
  $$f^{(n)}(a) = \frac{n!}{2\pi i} \oint_C \frac{f(z)}{(z - a)^{n+1}}\,dz$$

- **ML估计**：若在围道 $C$ 上 $|f(z)| \leq M$，$C$ 的长度为 $L$，则：
  $$\left| \oint_C f(z)\,dz \right| \leq ML$$

#### 常用公式

1. **标准Cauchy积分公式**：
   $$\oint_{|z-a|=R} \frac{f(z)}{z - a}\,dz = 2\pi i \, f(a)$$

2. **高阶导数公式**：
   $$\oint_{|z-a|=R} \frac{f(z)}{(z - a)^{n+1}}\,dz = \frac{2\pi i}{n!} \, f^{(n)}(a)$$

3. **Liouville定理**（由Cauchy估计导出）：有界整函数必为常数。

#### 解题步骤

**用Cauchy积分公式计算围道积分：**
1. 确认 $f(z)$ 在围道及其内部解析。
2. 判断被积函数中奇点的位置（是否在围道内部）。
3. 将被积函数写成 $\frac{f(z)}{(z-a)^{n+1}}$ 的形式。
4. 应用Cauchy积分公式或高阶导数公式：直接代入 $f^{(n)}(a)$。
5. 将结果乘以 $2\pi i$（或 $\frac{2\pi i}{n!}$）。

#### 对应习题

- **idx 2**: $\oint_{|z|=1} \frac{e^z}{z}\,dz$ — Cauchy积分公式，$f(a)=f(0)=1$，结果为 $2\pi i$
- **idx 3**: $\oint_{|z|=2} \frac{e^z}{(z-1)^3}\,dz$ — 高阶Cauchy公式，$n=2$，$f''(1)=e$，结果为 $\pi i e$
- **idx 15**: 用Cauchy估计证明Liouville定理 — $|f'(z_0)| \leq M/R \to 0$ 当 $R \to \infty$

---

### 模块4：级数展开
- 检索词：级数 series 收敛半径 radius 收敛 convergence taylor laurent 展开 expansion 幂级数 power

#### 核心概念

- **Taylor级数**：若 $f$ 在以 $a$ 为心、$R$ 为半径的圆盘内解析，则 $f(z) = \sum_{n=0}^{\infty} a_n (z-a)^n$，其中 $a_n = f^{(n)}(a)/n!$。
- **Laurent级数**：若 $f$ 在圆环 $r < |z-a| < R$ 内解析，则：
  $$f(z) = \sum_{n=-\infty}^{\infty} c_n (z-a)^n, \quad c_n = \frac{1}{2\pi i} \oint_C \frac{f(z)}{(z-a)^{n+1}}\,dz$$

- **收敛半径**：幂级数 $\sum a_n z^n$ 的收敛半径 $R = \lim_{n\to\infty} |a_n/a_{n+1}|$（比值法）或 $R = 1 / \limsup_{n\to\infty} \sqrt[n]{|a_n|}$（根值法）。
- **几何级数展开**：$\frac{1}{1-z} = \sum_{n=0}^{\infty} z^n$（$|z| < 1$），是Laurent展开的基础工具。

#### 常用公式

1. **收敛半径（比值法）**：
   $$R = \lim_{n\to\infty} \left|\frac{a_n}{a_{n+1}}\right|$$

2. **收敛半径（根值法 / Cauchy-Hadamard）**：
   $$R = \frac{1}{\limsup_{n\to\infty} \sqrt[n]{|a_n|}}$$

3. **几何级数**：
   $$\frac{1}{1-z} = \sum_{n=0}^{\infty} z^n \quad (|z| < 1)$$

4. **部分分式分解**（用于有理函数的Laurent展开）：
   $$\frac{1}{z(z-1)} = \frac{1}{z-1} - \frac{1}{z}$$

#### 解题步骤

**求圆环域内的Laurent级数：**
1. 对有理函数，先做部分分式分解。
2. 识别各分式所属的收敛区域，选择合适的几何级数展开方向：
   - 当 $|z| < 1$ 时：$\frac{1}{1-z} = \sum_{n=0}^{\infty} z^n$
   - 当 $|z| > 1$ 时：$\frac{1}{1-z} = -\frac{1}{z} \cdot \frac{1}{1-z^{-1}} = -\sum_{n=1}^{\infty} z^{-n}$
3. 合并各展开式，得到完整的Laurent级数（注意正幂部分和负幂部分）。

**求幂级数的收敛半径：**
1. 识别 $a_n$（第 $n$ 项系数）。
2. 使用比值法 $R = \lim |a_n/a_{n+1}|$ 或识别几何级数结构。
3. 特殊情况下使用根值法。

#### 对应习题

- **idx 4**: $f(z) = \frac{1}{z(z-1)}$ 在 $0 < |z| < 1$ 内的Laurent展开 — 部分分式 + 几何级数
- **idx 8**: 求 $\sum_{n=0}^{\infty} \frac{z^n}{2^n}$ 的收敛半径 — $R = 2$（几何级数或比值法）

---

### 模块5：留数理论
- 检索词：留数 residue 极点 pole 本性奇点 singularity 奇点 无穷远 infinity

#### 核心概念

- **孤立奇点**：若 $f$ 在 $z_0$ 的去心邻域内解析但在 $z_0$ 处不解析，则 $z_0$ 是 $f$ 的孤立奇点。
  - **可去奇点**：Laurent展开中无负幂项（留数为0）。
  - **$m$ 阶极点**：Laurent展开中负幂项有限，最低次为 $(z-z_0)^{-m}$。
  - **本性奇点**：Laurent展开中有无穷多负幂项。
- **留数**：$f$ 在孤立奇点 $z_0$ 处的留数 $\operatorname{Res}(f, z_0)$ 为 $f$ 在 $z_0$ 处Laurent展开中 $(z-z_0)^{-1}$ 的系数 $c_{-1}$。
- **留数定理**：若 $f$ 在简单闭围道 $C$ 及其内部除有限个孤立奇点 $z_1, \ldots, z_k$ 外解析，则：
  $$\oint_C f(z)\,dz = 2\pi i \sum_{j=1}^{k} \operatorname{Res}(f, z_j)$$

#### 常用公式

1. **简单极点留数**（$z_0$ 是一阶极点）：
   $$\operatorname{Res}(f, z_0) = \lim_{z \to z_0} (z - z_0) f(z)$$

2. **$m$ 阶极点留数**：
   $$\operatorname{Res}(f, z_0) = \frac{1}{(m-1)!} \lim_{z \to z_0} \frac{d^{m-1}}{dz^{m-1}} \left[(z - z_0)^m f(z)\right]$$

3. **有理函数 $f(z) = \frac{P(z)}{Q(z)}$ 在简单极点处的留数**（$P(z_0) \neq 0$，$Q(z_0) = 0$，$Q'(z_0) \neq 0$）：
   $$\operatorname{Res}(f, z_0) = \frac{P(z_0)}{Q'(z_0)}$$

4. **留数定理**：
   $$\oint_C f(z)\,dz = 2\pi i \sum \operatorname{Res}(f, z_j) \text{ （C内所有奇点）}$$

#### 解题步骤

**求孤立奇点处的留数：**
1. 确定奇点类型（简单极点、$m$ 阶极点、本性奇点）。
2. 对简单极点：使用公式 $\operatorname{Res} = \lim_{z \to z_0} (z - z_0) f(z)$。
3. 对 $m$ 阶极点：使用公式 $\operatorname{Res} = \frac{1}{(m-1)!} \lim \frac{d^{m-1}}{dz^{m-1}}[(z - z_0)^m f(z)]$。
4. 对本性奇点：通过Laurent展开直接读取 $c_{-1}$ 系数。
5. 验证：所有孤立奇点留数之和等于无穷远点留数的相反数。

#### 对应习题

- **idx 5**: 求 $f(z) = \frac{1}{z(z-1)^2}$ 在各孤立奇点处的留数 — $z=0$ 为简单极点，$z=1$ 为二阶极点

---

### 模块6：围道积分与实积分计算
- 检索词：围道 contour 实积分 improper 反常积分 三角积分 trigonometric 有理函数 rational

#### 核心概念

- **用留数定理计算实积分**：将实积分转化为复平面上的围道积分，然后利用留数定理。
- **典型围道**：
  - **上半平面大半圆围道**：用于 $\int_{-\infty}^{\infty} \frac{P(x)}{Q(x)}\,dx$（$\deg Q \geq \deg P + 2$）
  - **单位圆围道**：用于 $\int_0^{2\pi} R(\cos\theta, \sin\theta)\,d\theta$（令 $z = e^{i\theta}$）
  - **扇形/矩形围道**：用于含指数函数的积分
  - **钥匙孔围道**：用于含多值函数的积分
- **Jordan引理**：用于处理含 $e^{i\alpha z}$（$\alpha > 0$）的积分，保证大半圆弧部分积分趋于0。

#### 常用公式

1. **有理函数积分的标准形式**：
   $$\int_{-\infty}^{\infty} \frac{P(x)}{Q(x)}\,dx = 2\pi i \sum_{\operatorname{Im}(z_k) > 0} \operatorname{Res}\left(\frac{P(z)}{Q(z)}, z_k\right)$$
   其中 $z_k$ 取遍上半平面所有极点。

2. **三角积分的代换**（$z = e^{i\theta}$）：
   $$\cos\theta = \frac{z + z^{-1}}{2},\quad \sin\theta = \frac{z - z^{-1}}{2i},\quad d\theta = \frac{dz}{iz}$$
   $$\int_0^{2\pi} R(\cos\theta, \sin\theta)\,d\theta = \oint_{|z|=1} R\left(\frac{z+z^{-1}}{2}, \frac{z-z^{-1}}{2i}\right) \frac{dz}{iz}$$

3. **含三角函数的无穷积分**：
   $$\int_{-\infty}^{\infty} \frac{\cos x}{x^2 + a^2}\,dx = 2\pi i \cdot \operatorname{Res}\left(\frac{e^{iz}}{z^2 + a^2}, ia\right) \text{ 的实部}$$

4. **含 $e^{iz}$ 的标准结果**：
   $$\int_{-\infty}^{\infty} \frac{e^{i\alpha x}}{x^2 + 1}\,dx = \frac{\pi}{e^{\alpha}} \quad (\alpha > 0)$$

#### 解题步骤

**用围道积分求 $\int_{-\infty}^{\infty} \frac{P(x)}{Q(x)}\,dx$：**
1. 验证分母次数 $\geq$ 分子次数 $+2$（保证大半圆弧积分趋于0）。
2. 在上半平面找出 $P(z)/Q(z)$ 的所有极点。
3. 计算每个极点的留数（通常为简单极点，使用 $P(z_0)/Q'(z_0)$ 公式）。
4. 应用留数定理，积分值 = $2\pi i \times$（上半平面留数之和）。

**用围道积分求 $\int_0^{2\pi} R(\cos\theta, \sin\theta)\,d\theta$：**
1. 作代换 $z = e^{i\theta}$，将 $\cos\theta, \sin\theta, d\theta$ 用 $z$ 表示。
2. 被积式化为 $\oint_{|z|=1} f(z)\,dz$ 的形式。
3. 找出 $|z| = 1$ 内部的极点。
4. 计算留数，积分值 = $2\pi i \times$（单位圆内留数之和）。

**含 $\cos x$ 或 $\sin x$ 的无穷积分：**
1. 改写为 $\int_{-\infty}^{\infty} \operatorname{Re}[e^{i\alpha x} f(x)]\,dx$。
2. 用上半平面大半圆围道计算 $\oint e^{i\alpha z} f(z)\,dz$。
3. 应用Jordan引理验证大半圆弧积分为0。
4. 取实部（或虚部）得到最终结果。

#### 对应习题

- **idx 6**: $\int_{-\infty}^{\infty} \frac{dx}{x^4+1}$ — 上半平面两个简单极点，结果 $\pi/\sqrt{2}$
- **idx 11**: $\int_0^{2\pi} \frac{d\theta}{5+4\cos\theta}$ — $z = e^{i\theta}$ 代换，结果 $2\pi/3$
- **idx 12**: $\int_0^{\infty} \frac{\cos x}{x^2+1}\,dx$ — 上半平面 $z=i$ 极点 + Jordan引理，结果 $\pi/(2e)$
- **idx 13**: $\int_0^{2\pi} e^{\cos\theta} \cos(\sin\theta - \theta)\,d\theta$ — 改写为 $\operatorname{Re}[e^{e^{i\theta}} e^{-i\theta}]$，结果 $2\pi$

---

### 模块7：保形映射
- 检索词：保形 conformal 映射 mapping 双线性 bilinear 单位圆 unit disk 上半平面 upper half

#### 核心概念

- **解析函数的保形性**：若 $f$ 在 $z_0$ 解析且 $f'(z_0) \neq 0$，则 $f$ 在 $z_0$ 处保角（保形）。
- **分式线性变换（Möbius变换）**：
  $$w = T(z) = \frac{az + b}{cz + d}, \quad ad - bc \neq 0$$

- **Möbius变换的性质**：
  - 将圆（含直线，视为过无穷远点的圆）映为圆。
  - 保对称性（关于圆的对称点映为关于像圆的对称点）。
  - 保交比：$(z_1, z_2; z_3, z_4) = (w_1, w_2; w_3, w_4)$。
- **边界对应原理**：若 $f$ 在区域 $D$ 内解析、在 $\partial D$ 上连续且将 $\partial D$ 一对一地映为 $\partial \Omega$，则 $f$ 将 $D$ 一对一地映为 $\Omega$。

#### 常用公式

1. **标准上半平面到单位圆盘的映射**：
   $$w = \frac{z - i}{z + i} \quad \text{将上本平面 } \mathbb{H} \text{ 映为单位圆盘 } \mathbb{D}$$

2. **Möbius变换的逆**：
   $$T^{-1}(w) = \frac{-dw + b}{cw - a}$$

3. **Möbius变换的交比保持**：
   $$\frac{(z - z_1)(z_2 - z_3)}{(z - z_3)(z_2 - z_1)} = \frac{(w - w_1)(w_2 - w_3)}{(w - w_3)(w_2 - w_1)}$$

#### 解题步骤

**判断Möbius变换的区域映射：**
1. 确定映射 $w = T(z)$ 的逆映射。
2. 验证边界映射：实轴 $\to$ 单位圆周（通过计算 $|T(x)| = 1$ 对于 $x \in \mathbb{R}$）。
3. 取一个内部测试点（如上本平面的 $z = i$），计算其像，验证其落在目标区域内。
4. 由边界对应原理得出完整区域映射结论。

#### 对应习题

- **idx 10**: 验证 $w = \frac{z-i}{z+i}$ 将上半平面映为单位圆盘 — 实轴 $|w|=1$，$z=i \to w=0$

---

### 模块8：零点与极点理论
- 检索词：零点 zero 极点 pole 辐角 argument 原理 principle 有理型 meromorphic

#### 核心概念

- **零点**：若 $f(z_0) = 0$，则 $z_0$ 是 $f$ 的零点。若 $f^{(k)}(z_0) = 0$（$k = 0, 1, \ldots, m-1$）而 $f^{(m)}(z_0) \neq 0$，则 $z_0$ 是 $m$ 重零点。
- **极点**：若 $1/f$ 以 $z_0$ 为 $m$ 重零点，则 $z_0$ 是 $f$ 的 $m$ 阶极点。
- **亚纯函数**：在区域内除极点外处处解析的函数。
- **辐角原理**：设 $f$ 在简单闭围道 $C$ 及其内部亚纯，在 $C$ 上 $f(z) \neq 0$，则：
  $$\frac{1}{2\pi i} \oint_C \frac{f'(z)}{f(z)}\,dz = N - P$$
  其中 $N$ 为零点个数（计重数），$P$ 为极点个数（计重数）。
  等价地：$\Delta_C \arg f(z) = 2\pi(N - P)$（辐角变化）。

- **Rouché定理**：设 $f$ 和 $g$ 在简单闭围道 $C$ 及其内部解析，且在 $C$ 上 $|f(z)| > |g(z)|$，则 $f$ 和 $f + g$ 在 $C$ 内部有相同个数的零点（计重数）。

#### 常用公式

1. **辐角原理（积分形式）**：
   $$\frac{1}{2\pi i} \oint_C \frac{f'(z)}{f(z)}\,dz = N - P$$

2. **辐角原理（辐角形式）**：
   $$\Delta_C \arg f(z) = 2\pi(N - P)$$

3. **对数导数在零点的留数**：若 $z_0$ 是 $f$ 的 $m$ 重零点，则 $\operatorname{Res}(f'/f, z_0) = m$。

4. **对数导数在极点的留数**：若 $z_0$ 是 $f$ 的 $k$ 阶极点，则 $\operatorname{Res}(f'/f, z_0) = -k$。

#### 解题步骤

**用Rouché定理求方程在区域内的零点个数：**
1. 在边界 $C$ 上比较 $|f(z)|$ 和 $|g(z)|$ 的大小。
2. 选取占优项 $f(z)$（在边界上模最大）。
3. 验证 $|f(z)| > |g(z)|$ 在 $C$ 上成立。
4. 由Rouché定理，$f+g$ 与 $f$ 在 $C$ 内零点数相同。
5. 计算 $f(z)$ 在 $C$ 内的零点个数（计重数）作为答案。

**证明辐角原理：**
1. 考察 $f'/f$ 的奇点（恰为 $f$ 的零点和极点）。
2. 在 $m$ 重零点附近：$f(z) = (z-z_0)^m g(z)$，$g(z_0) \neq 0$，则 $f'/f = m/(z-z_0) + g'/g$，留数为 $m$。
3. 在 $k$ 阶极点附近：$f(z) = (z-z_0)^{-k} h(z)$，$h(z_0) \neq 0$，则 $f'/f = -k/(z-z_0) + h'/h$，留数为 $-k$。
4. 由留数定理，围道积分 = $2\pi i(\sum m_i - \sum k_j) = 2\pi i(N-P)$。

**用辐角原理证明Rouché定理：**
1. 在 $C$ 上 $f \neq 0$ 且 $f+g \neq 0$（因为 $|f| > |g|$）。
2. 构造同伦族 $F_t(z) = f(z) + t \cdot g(z)$，$0 \leq t \leq 1$，在 $C$ 上 $F_t \neq 0$。
3. $N(t) = \frac{1}{2\pi i} \oint_C F_t'/F_t$ 是 $t$ 的连续函数且取整数值，故为常数。
4. $N(0) = N(1)$，即 $f$ 和 $f+g$ 零点数相同。
5. 或使用辐角论证：$|g/f| < 1$ 在 $C$ 上，$1 + g/f$ 在以1为心的单位圆盘内，辐角变化为0。

#### 对应习题

- **idx 9**: 用Rouché定理求 $z^8 + 3z^3 + 1 = 0$ 在 $|z| < 1$ 内的零点数 — 取 $f(z) = 3z^3$，$g(z) = z^8 + 1$，结果为3
- **idx 18**: 证明辐角原理 — 对数导数留数 + 留数定理
- **idx 19**: 用辐角原理证明Rouché定理 — 同伦论证或辐角论证

---

### 模块9：经典定理
- 检索词：liouville 最大模 maximum modulus 代数基本定理 fundamental 辐角原理 rouche 解析延拓 continuation

#### Liouville定理

**定理陈述**：若 $f$ 是整函数（在整个复平面上解析）且有界（存在 $M > 0$ 使得对所有 $z \in \mathbb{C}$ 有 $|f(z)| \leq M$），则 $f$ 为常数。

**证明要点**：
1. 由Cauchy积分公式的导数形式：$f'(z_0) = \frac{1}{2\pi i} \oint_{|z-z_0|=R} \frac{f(z)}{(z-z_0)^2}\,dz$。
2. ML估计：$|f'(z_0)| \leq \frac{1}{2\pi} \cdot \frac{M}{R^2} \cdot 2\pi R = \frac{M}{R}$。
3. 令 $R \to \infty$，得 $f'(z_0) = 0$。
4. 由 $z_0$ 的任意性，$f'(z) \equiv 0$，故 $f$ 为常数。

#### 最大模原理

**定理陈述**：若 $f$ 在区域 $D$ 内解析且非常数，则 $|f(z)|$ 不能在 $D$ 内部取到最大值。

**证明要点**：
1. 反证法：假设 $|f|$ 在 $z_0 \in D$ 处取最大值 $M = |f(z_0)|$。
2. 由解析函数的平均值性质：$f(z_0) = \frac{1}{2\pi} \int_0^{2\pi} f(z_0 + re^{i\theta})\,d\theta$。
3. 取模：$M = |f(z_0)| \leq \frac{1}{2\pi} \int_0^{2\pi} |f(z_0 + re^{i\theta})|\,d\theta \leq M$。
4. 等号迫使 $|f(z_0 + re^{i\theta})| \equiv M$ 对所有 $\theta$ 成立。
5. 由 $r$ 的任意性和唯一性定理，$f$ 为常数，矛盾。

#### 代数学基本定理

**定理陈述**：任意非常数复系数多项式 $P(z) = a_n z^n + \cdots + a_0$（$a_n \neq 0$，$n \geq 1$）在复数域中至少有一个根。

**证明要点（用Liouville定理）**：
1. 反证法：假设 $P(z)$ 无零点，则 $1/P(z)$ 是整函数。
2. 由于 $\lim_{|z| \to \infty} |P(z)| = \infty$（首项占优），存在 $R$ 使得当 $|z| > R$ 时 $|1/P(z)| < 1$。
3. 在紧集 $|z| \leq R$ 上 $|1/P(z)|$ 连续故有界，因此 $1/P(z)$ 在 $\mathbb{C}$ 上有界。
4. 由Liouville定理，$1/P(z)$ 为常数，从而 $P(z)$ 为常数，矛盾。

#### 辐角原理

**定理陈述**：设 $f$ 在简单闭围道 $C$ 及其内部亚纯（除极点外解析），且在 $C$ 上 $f(z) \neq 0$，则：
$$\frac{1}{2\pi i} \oint_C \frac{f'(z)}{f(z)}\,dz = N - P$$
其中 $N$ 为 $f$ 在 $C$ 内部零点的个数（计重数），$P$ 为极点的个数（计重数）。

#### Rouché定理

**定理陈述**：设 $f$ 和 $g$ 在简单闭围道 $C$ 及其内部解析，且在 $C$ 上满足 $|f(z)| > |g(z)|$，则 $f$ 和 $f+g$ 在 $C$ 内部具有相同个数的零点（计重数）。

#### 对应习题

- **idx 15**: 用Cauchy估计证明Liouville定理 — $|f'(z_0)| \leq M/R \to 0$
- **idx 16**: 证明最大模原理 — 平均值性质 + 反证法
- **idx 17**: 用Liouville定理证明代数学基本定理 — $1/P(z)$ 有界整函数
- **idx 18**: 证明辐角原理 — 对数导数的留数分析
- **idx 19**: 用辐角原理证明Rouché定理 — 同伦族 + 连续整数值函数

---

## 模块速查：通用解题方法论

### 1. 题型识别

拿到题目后首先判断：

| 题型特征 | 对应模块 |
|---------|---------|
| "求 $(\cdots)^n$" / "化为标准形式" / 含 $\sqrt{3}+i$ 的高次幂 | 模块1：复数运算与de Moivre公式 |
| "何处解析" / "判断解析性" / 验证/证明C-R方程 | 模块2：解析函数与Cauchy-Riemann方程 |
| "调和函数" / "共轭调和函数" / 含 $u_x, u_y$ | 模块2：调和函数 |
| "用Cauchy积分公式" / "$\oint$" 含 $f(z)/(z-a)$ | 模块3：Cauchy积分理论 |
| "高阶Cauchy" / "$\oint$" 含 $(z-a)^n$ 分母 | 模块3：高阶导数公式 |
| "Laurent级数" / "圆环域展开" | 模块4：级数展开 |
| "收敛半径" / "幂级数" 含 $\sum$ | 模块4：收敛半径 |
| "求留数" / "$\operatorname{Res}$" | 模块5：留数理论 |
| "实积分" $\int_{-\infty}^{\infty}$ + 有理函数 | 模块6：围道积分 |
| "$\int_0^{2\pi}$" + 三角函数 | 模块6：三角积分围道法 |
| "保形映射" / "Möbius变换" / "上半平面映为" | 模块7：保形映射 |
| "Rouché定理" / "零点个数" / 含 $|z| < 1$ | 模块8：Rouché定理应用 |
| "辐角原理" / "$N-P$" / "对数导数" | 模块8：辐角原理 |
| "Liouville" / "有界整函数" | 模块9：Liouville定理 |
| "最大模" / "$|f(z)|$ 取最大值" | 模块9：最大模原理 |
| "代数学基本定理" / "多项式至少有一个根" | 模块9：代数学基本定理 |

### 2. 方法选择

| 问题类型 | 首选方法 | 备选方法 |
|---------|---------|---------|
| 求复数的高次幂 | 极坐标 + de Moivre公式 | 二项式展开（低次时） |
| 判断解析性 | 验证C-R方程 + 开邻域论证 | 直接求导极限 |
| 求共轭调和函数 | C-R方程逐次积分 | Milne-Thomson方法 |
| 计算Cauchy积分 | $\oint f/(z-a) = 2\pi i f(a)$ | 参数化直接积分 |
| 计算高阶Cauchy积分 | $\oint f/(z-a)^{n+1} = \frac{2\pi i}{n!} f^{(n)}(a)$ | 展开后逐项积分 |
| 求Laurent级数 | 部分分式 + 几何级数展开 | 直接积分公式 $c_n$ |
| 求收敛半径 | 比值法 $R = \lim \|a_n/a_{n+1}\|$ | 根值法 |
| 计算留数 | 极点阶数判定 + 对应公式 | Laurent展开读取 $c_{-1}$ |
| 求实积分（有理函数） | 上半平面留数之和 | 其他围道 |
| 求三角积分 | $z = e^{i\theta}$ 代换 | 三角恒等变形 |
| 求含 $\cos x$ 的无穷积分 | 构造 $e^{iz}$ 围道 + 取实部 | 奇偶对称性简化 |
| 判断区域映射 | 边界对应原理 + 测试点 | 交比构造 |
| 求零点个数 | Rouché定理选择占优项 | 辐角原理 |
| 证明复分析定理 | 核定理（Cauchy积分/留数定理） + 不等式估计 | 反证法 |

### 3. 结果验证

- **de Moivre结果验证**：$|z^n| = |z|^n$，$\arg(z^n)$ 匹配。
- **C-R验证**：$u_{xx} + u_{yy} = 0$ 和 $v_{xx} + v_{yy} = 0$。
- **围道积分验证**：奇点必须在围道内部才能贡献非零积分；若所有奇点都在围道外则积分必为0。
- **留数验证**：所有有限孤立奇点留数之和 $+ \operatorname{Res}(f, \infty) = 0$。
- **实积分结果验证**：对称性（偶函数积分 = $2\int_0^\infty$）、正性（被积函数恒正则积分 > 0）。
- **收敛半径验证**：$R$ 满足 $|z| < R$ 时级数绝对收敛，$|z| > R$ 时发散。
- **Rouché验证**：在边界上确实满足 $|f| > |g|$（严格大于）。
- **sympy 独立验证**：对计算题结果用 sympy 独立验算。

---

## 模块速查：sympy验证技巧

本节给出可供 Python 生成阶段使用的 SymPy 核验思路，覆盖复数运算、级数展开、留数计算和围道积分；题面数据仍为唯一的数值来源。

## 模块速查：sympy验证：复数基础运算

```python
from sympy import I, re, im, Abs, arg, conjugate, expand, simplify

# 构造复数
z = 3 + 4*I
w = 1 + I

# 基本运算
z_plus_w = z + w          # 加法
z_times_w = z * w         # 乘法
z_div_w = z / w           # 除法

# 模和辐角
modulus = Abs(z)          # 5
argument = arg(z)         # atan(4/3)

# 共轭
z_conj = conjugate(z)     # 3 - 4*I

# 验证 |z|^2 = z * conjugate(z)
assert Abs(z)**2 == expand(z * conjugate(z))
```

## 模块速查：sympy验证：de Moivre公式与复数的高次幂

```python
from sympy import I, expand, sqrt, pi, cos, sin, simplify

# 例：idx 0 - 求 (sqrt(3) + i)^6
z = sqrt(3) + I

# 方法1：直接计算
result_direct = expand(z**6)     # -64

# 方法2：极坐标 + de Moivre
from sympy import Abs, arg
r = Abs(z)                       # 2
theta = arg(z)                   # pi/6
# (r * exp(i*theta))^6 = r^6 * exp(i*6*theta)
result_polar = simplify(r**6 * (cos(6*theta) + I*sin(6*theta)))  # -64

# 验证两种方法一致
assert simplify(result_direct - result_polar) == 0
```

```python
# 通项模式：求任意复数的高次幂
from sympy import I, expand, symbols, Abs, arg, cos, sin, simplify

a, b, n = symbols('a b n', integer=True)
z_expr = 1 + sqrt(3)*I
r_val = Abs(z_expr)
theta_val = arg(z_expr)
# 结果 = r^n * (cos(n*theta) + i*sin(n*theta))
```

## 模块速查：sympy验证：Cauchy-Riemann方程验证

```python
from sympy import I, symbols, diff, expand

x, y = symbols('x y', real=True)

# 例：idx 1 - 验证 f(z) = |z|^2 的C-R条件
u = x**2 + y**2
v = 0

ux = diff(u, x)    # 2x
uy = diff(u, y)    # 2y
vx = diff(v, x)    # 0
vy = diff(v, y)    # 0

# C-R方程: ux == vy 且 uy == -vx
cr1 = simplify(ux - vy)        # 2x == 0 => x=0
cr2 = simplify(uy + vx)        # 2y == 0 => y=0
# 仅在 (x,y) = (0,0) 处满足C-R方程，但不是开集内每一点都满足

# 例：idx 7 - 验证 u = e^x cos y 是调和函数
u_harm = exp(x) * cos(y)
uxx = diff(u_harm, x, 2)       # e^x cos y
uyy = diff(u_harm, y, 2)       # -e^x cos y
laplace = simplify(uxx + uyy)  # 0 -> 调和

# 求共轭调和函数: v_y = u_x, v_x = -u_y
# 步骤通过符号积分完成
from sympy import integrate, symbols
C1 = symbols('C1')
v_candidate = integrate(diff(u_harm, x), y)  # e^x sin y
# 验证 v_x = -u_y
vx_check = diff(v_candidate, x)        # e^x sin y
uy_neg = -diff(u_harm, y)              # e^x sin y
assert simplify(vx_check - uy_neg) == 0
```

## 模块速查：sympy验证：Cauchy积分公式

```python
from sympy import I, pi, exp, diff, symbols

z, a = symbols('z a')

# 例：idx 2 - ∮ e^z/z dz 沿 |z|=1
# Cauchy积分公式: ∮ f(z)/(z-a) dz = 2πi f(a)
# 取 f(z) = e^z, a = 0
f_z = exp(z)
result = 2*pi*I * f_z.subs(z, 0)  # 2πi * e^0 = 2πi

# 例：idx 3 - ∮ e^z/(z-1)^3 dz 沿 |z|=2
# 高阶Cauchy: ∮ f(z)/(z-a)^{n+1} dz = (2πi/n!) f^{(n)}(a)
# n = 2, a = 1, f(z) = e^z
n = 2
a_val = 1
f_n = diff(exp(z), z, n)            # e^z
f_n_at_a = f_n.subs(z, a_val)       # e^1 = e
result_high = (2*pi*I / factorial(n)) * f_n_at_a  # πie

from sympy import factorial
def factorial_sympy(k):
    from sympy import factorial as sp_factorial
    return sp_factorial(k)

result_high = (2*pi*I / factorial_sympy(n)) * f_n_at_a
```

## 模块速查：sympy验证：级数展开与收敛半径

```python
from sympy import symbols, series, oo, limit_seq, summation

z = symbols('z')

# 例：idx 4 - Laurent展开: 1/(z(z-1)) 在 0<|z|<1
f = 1/(z*(z-1))

# 部分分式分解
from sympy import apart
f_partial = apart(f, z)  # -1/z - 1/(1-z) 或 1/(z-1) - 1/z

# 1/(1-z) 的展开 (|z| < 1): Σ z^n
# 1/(z-1) = -1/(1-z) = -(1+z+z^2+...)
# 因此 f(z) = -1/z - 1 - z - z^2 - z^3 - ...

# Taylor级数验证（在z=0展开，注意这是Laurent级数）
from sympy import series as sp_series
laurent = sp_series(f, z, n=6)  # 返回带O(z^5)的级数
# 应该得到 -1/z - 1 - z - z^2 - z^3 - z^4 + O(z^5)

# 例：idx 8 - 收敛半径: Σ z^n/2^n
# 使用比值法
n = symbols('n', integer=True, positive=True)
a_n = 1 / (2**n)
a_np1 = 1 / (2**(n+1))
from sympy import limit
R = limit(a_n / a_np1, n, oo)  # 2

# 或识别为几何级数 Σ (z/2)^n，收敛当 |z/2| < 1，即 |z| < 2
```

## 模块速查：sympy验证：留数计算

```python
from sympy import I, oo, limit, diff, symbols

z = symbols('z')

# 例：idx 5 - 求 f(z) = 1/(z*(z-1)^2) 的留数
f = 1 / (z * (z-1)**2)

# z=0 是简单极点
res_0 = limit(z * f, z, 0)  # 1

# z=1 是二阶极点
# Res(f, 1) = (1/1!) * lim_{z->1} d/dz[(z-1)^2 * f(z)]
g = (z-1)**2 * f              # 1/z
dg = diff(g, z)               # -1/z^2
res_1 = limit(dg, z, 1)       # -1

# 验证留数之和 = 0（包括无穷远点，期望 ΣRes + Res(∞) = 0）
# 对于此函数 Res(∞) = 0，所以 ΣRes = 1 + (-1) = 0

# 通用留数计算函数
def compute_residue(f, z0, order=1):
    """计算函数 f 在 z=z0 处的留数（假设为 order 阶极点）"""
    if order == 1:
        return limit((z - z0) * f, z, z0)
    else:
        g = (z - z0)**order * f
        dg = diff(g, z, order - 1)
        from sympy import factorial as sp_fact
        return limit(dg, z, z0) / sp_fact(order - 1)
```

## 模块速查：sympy验证：实积分计算（留数定理）

```python
from sympy import I, pi, oo, limit, diff, cos, sin, symbols, expand, simplify, factor

z, theta, x = symbols('z theta x')

# 例：idx 6 - ∫_{-∞}^{∞} dx/(x^4+1)
# 上半平面极点: z_k = e^{iπ(2k+1)/4}, k = 0, 1 (在第一、二象限)
# z_0 = e^{iπ/4} = (1+i)/√2, z_1 = e^{i3π/4} = (-1+i)/√2
# 对简单极点 z_k: Res(P/Q, z_k) = P(z_k)/Q'(z_k) = 1/(4z_k^3)

# 计算留数
f_rational = 1 / (z**4 + 1)
Q_prime = diff(z**4 + 1, z)  # 4z^3

# 上半平面极点
import sympy as sp
z0 = sp.exp(sp.I * sp.pi / 4)      # e^{iπ/4}
z1 = sp.exp(3 * sp.I * sp.pi / 4)  # e^{i3π/4}

res_z0 = simplify(1 / Q_prime.subs(z, z0))
res_z1 = simplify(1 / Q_prime.subs(z, z1))
sum_res = simplify(res_z0 + res_z1)  # -i/(2√2) = -I/(2*sqrt(2))
result_6 = simplify(2 * pi * I * sum_res)  # π/√2

# 例：idx 11 - ∫_0^{2π} dθ/(5+4cos θ)
# 代换: z = e^{iθ}, cosθ = (z+z^{-1})/2, dθ = dz/(iz)
z = symbols('z')
cos_theta = (z + 1/z) / 2
dtheta = 1 / (I * z)
integrand = 1 / (5 + 4 * cos_theta) * dtheta  # 1/(iz(5+2(z+z^{-1})))

# 化简
integrand_simp = simplify(integrand)
# = 1/(I*(2*z**2 + 5*z + 2))
# 因式分解分母
denom = 2*z**2 + 5*z + 2  # = (2z+1)(z+2)
# 在 |z|=1 内仅 z = -1/2 是极点
# Res = 1/(I*(2*(z+2))) 在 z = -1/2 处 = 1/(I*2*(-1/2+2)) = 1/(3I)
# 积分 = 2πi * (1/(3i)) = 2π/3

# 例：idx 12 - ∫_0^∞ cos x/(x^2+1) dx
# 考虑 ∮ e^{iz}/(z^2+1) dz 沿上半平面大半圆
# 在上半平面仅 z = i 是极点
res_i = limit((z - I) * sp.exp(I*z) / (z**2 + 1), z, I)
# = e^{i·i}/(2i) = e^{-1}/(2i)
# 积分 = π/e (整条实轴)
# 由偶对称性，∫_0^∞ = π/(2e)
```

## 模块速查：sympy验证：全参数化验证流程

```python
from sympy import I, pi, oo, limit, diff, cos, sin, symbols, expand, simplify, Abs, arg, integrate

z, x, y, theta = symbols('z x y theta', real=False)

# ============ 验证 idx 0：复数高次幂 ============
result_0 = expand((sp.sqrt(3) + I)**6)
assert simplify(result_0) == -64

# ============ 验证 idx 2：Cauchy积分公式 ============
# ∮ e^z/z dz = 2πi
result_2 = 2 * pi * I * sp.exp(0)
assert simplify(result_2) == 2*pi*I

# ============ 验证 idx 4：Laurent 展开 ============
from sympy import apart
f4 = 1/(z*(z-1))
partial = apart(f4, z)  # 1/(z-1) - 1/z
# 在 0<|z|<1 内: 1/(z-1) = -1/(1-z) = -(1+z+z^2+...)
# f4 = -1/z - 1 - z - z^2 - ... = -Σ_{n=-1}^{∞} z^n

# ============ 验证 idx 5：留数 ============
f5 = 1 / (z * (z-1)**2)
res5_0 = limit(z * f5, z, 0)  # 1
# z=1是二阶极点
g5 = (z-1)**2 * f5  # 1/z
res5_1 = limit(diff(g5, z), z, 1)  # -1
assert res5_0 == 1 and res5_1 == -1

# ============ 验证 idx 8：收敛半径 ============
# Σ z^n/2^n, a_n = 1/2^n
n_sym = symbols('n', integer=True, positive=True)
R8 = sp.limit(1/(2**n_sym) / (1/(2**(n_sym+1))), n_sym, oo)
assert R8 == 2
```

---

## 模块速查：习题索引

| idx | 题型 | 难度 | 主题 | 关键公式/定理 | 核心方法 | 验证方法 |
|-----|------|------|------|-------------|---------|---------|
| 0 | 计算 | 简单 | 复数运算与de Moivre公式 | $(re^{i\theta})^n = r^n e^{in\theta}$ | 化为极坐标 + de Moivre | `expand(z**6)` 直接计算 |
| 1 | 计算 | 简单 | Cauchy-Riemann方程 | $u_x = v_y$, $u_y = -v_x$ | 分离实虚部 + 验证C-R方程 | sympy `diff` 验证偏导 |
| 2 | 计算 | 简单 | Cauchy积分公式 | $\oint \frac{f(z)}{z-a} dz = 2\pi i f(a)$ | 直接代入Cauchy公式 | $2\pi i \cdot f(0)$ |
| 3 | 计算 | 中等 | 高阶Cauchy积分公式 | $\oint \frac{f(z)}{(z-a)^{n+1}} dz = \frac{2\pi i}{n!} f^{(n)}(a)$ | 识别 $n=2$, $f(z)=e^z$, $a=1$ | sympy `diff(f, z, n)` |
| 4 | 计算 | 中等 | Laurent级数 | 几何级数 $\frac{1}{1-z} = \sum z^n$ | 部分分式 + 几何级数展开 | `apart` + `series` |
| 5 | 计算 | 中等 | 留数计算 | $\operatorname{Res}(f,z_0) = \frac{1}{(m-1)!} \lim \frac{d^{m-1}}{dz^{m-1}}[(z-z_0)^m f]$ | 判断极点阶数 + 留数公式 | `limit` + `diff` 留数公式 |
| 6 | 计算 | 中等 | 留数定理求实积分 | $\int_{-\infty}^{\infty} = 2\pi i \sum_{\operatorname{Im}>0} \operatorname{Res}$ | 上半平面极点 + 留数定理 | sympy 留数计算 + 求和 |
| 7 | 计算 | 中等 | 调和函数与共轭调和函数 | $u_{xx}+u_{yy}=0$, C-R积分 | 验证调和性 + C-R积分求 $v$ | `diff(u, x, 2)+diff(u, y, 2)` |
| 8 | 计算 | 中等 | 收敛半径 | $R = \lim \|a_n/a_{n+1}\|$ | 比值法或识别几何级数 | `limit(a_n/a_{n+1})` |
| 9 | 计算 | 中等 | Rouché定理应用 | Rouché: $\|f\| > \|g\|$ 在 $C$ 上 | 边界比较 + 占优项零点计数 | 逻辑验证 $|f| > |g|$ |
| 10 | 计算 | 中等 | 保形映射 | Möbius: $w = \frac{az+b}{cz+d}$ 保圆 | 验证边界映射 + 内部测试点 | $\|T(x)\|$ 计算 |
| 11 | 计算 | 中等 | 留数求三角积分 | $z = e^{i\theta}$, $\cos\theta = \frac{z+z^{-1}}{2}$ | 变量代换 + 单位圆内留数 | sympy 留数计算 |
| 12 | 计算 | 困难 | 围道积分 | Jordan引理 + $\operatorname{Re}[\oint e^{iz}f(z)]$ | 上半平面围道 + 取实部 | sympy 留数 + 取实部 |
| 13 | 计算 | 困难 | 级数与特殊积分 | $e^{\cos\theta}\cos(\sin\theta-\theta) = \operatorname{Re}[e^{e^{i\theta}} e^{-i\theta}]$ | 复指数改写 + 留数定理 | sympy `series` 留数展开 |
| 14 | 证明 | 简单 | C-R方程必要性 | 沿实轴和虚轴方向取极限 | 两方向导数相等 + 实虚部比较 | 逻辑验证 |
| 15 | 证明 | 中等 | Liouville定理 | Cauchy估计 $\|f'(z_0)\| \leq M/R$ | Cauchy导数公式 + ML估计 | 不等式推导逻辑 |
| 16 | 证明 | 中等 | 最大模原理 | 平均值性质 $f(z_0) = \frac{1}{2\pi}\int f(z_0+re^{i\theta})d\theta$ | 反证法 + 平均值性质 | 逻辑推导 |
| 17 | 证明 | 中等 | 代数学基本定理 | Liouville定理 | 反证法: $1/P(z)$ 有界整函数 | 逻辑推导 |
| 18 | 证明 | 困难 | 辐角原理 | $\frac{1}{2\pi i}\oint \frac{f'}{f} = N-P$ | 对数导数 + 留数定理 | 留数分析逻辑 |
| 19 | 证明 | 困难 | Rouché定理 | 同伦族 $F_t = f + tg$ | 辐角原理 + 连续整数值函数 | 同伦论证逻辑 |

---

## 模块速查：常见错误与陷阱

### 复数运算
1. **辐角计算忽略象限**：$\arctan(b/a)$ 只给出 $(-\pi/2, \pi/2)$ 内的值。当 $a < 0$ 时辐角应为 $\arctan(b/a) + \pi$（或 $-\pi$），否则会差 $\pi$。例如 $\sqrt{3}+i$ 的辐角是 $\pi/6$，但 $-\sqrt{3}+i$ 的辐角是 $5\pi/6$ 而非 $\arctan(-1/\sqrt{3}) \approx -\pi/6$。
2. **de Moivre公式中忘记乘以 $r^n$**：$(re^{i\theta})^n = r^n e^{in\theta}$，而不仅仅是 $e^{in\theta}$。遗漏 $r^n$ 是常见错误。
3. **高次幂的辐角简化错误**：$e^{i\cdot n\theta}$ 需化简到主值范围（通常 $(-\pi, \pi]$ 或 $[0, 2\pi)$）。如 $e^{i\pi} = -1$ 而非保留 $e^{i\pi}$。
4. **混淆代数形式和极坐标形式**：平方时 $(a+bi)^2 = a^2 - b^2 + 2abi$ 结果不含根号，但极坐标形式结果可能含三角函数值，两种形式应当统一简化为 $x+yi$。

### 解析函数与Cauchy-Riemann方程
5. **混淆"满足C-R方程"与"解析"**：C-R方程只在一点处满足不足以保证函数在该点解析。必须在开邻域内每一点都满足C-R方程且在邻域内 $u, v$ 偏导数连续，函数才在该点解析。
6. **C-R方程中虚部的符号错误**：正确的C-R方程是 $u_x = v_y$ 且 $u_y = -v_x$。常见错误是写成 $u_y = v_x$（遗漏负号）。
7. **用 $|z|^2$ 的C-R验证时忘记 $v=0$ 的特殊性**：$f(z) = |z|^2$ 的虚部恒为0，此时 $u_x = v_y = 0 \Rightarrow 2x = 0$ 且 $u_y = -v_x = 0 \Rightarrow 2y = 0$，立刻得到只在原点满足。但解析性需要开邻域条件，故处处不解析。
8. **求共轭调和函数时遗漏积分常数**：由 $v_y = u_x$ 积分得到 $v = \int u_x\,dy + \varphi(x)$ 后，必须通过 $v_x = -u_y$ 确定 $\varphi(x)$ 的具体形式并积分得到完整常数。

### Cauchy积分理论
9. **混淆Cauchy积分公式和高阶导数公式的系数**：$\oint \frac{f(z)}{(z-a)^{n+1}}\,dz = \frac{2\pi i}{n!} f^{(n)}(a)$，不是 $\frac{2\pi i}{n} f^{(n)}(a)$ 也不是 $2\pi i f^{(n)}(a)$。遗漏 $1/n!$ 是常见错误。
10. **忘记验证奇点是否在围道内部**：Cauchy积分公式和高阶导数公式都要求奇点 $a$ 在围道内部。若奇点在围道外部，积分结果为0。
11. **Cauchy积分定理的适用条件**：要求 $f$ 在围道及其内部解析。如果奇点在围道内部，不能直接使用Cauchy积分定理得出积分为0。

### 级数展开
12. **Laurent展开中 $\frac{1}{1-z}$ 的展开方向错误**：当 $|z| < 1$ 时 $\frac{1}{1-z} = \sum_{n=0}^{\infty} z^n$；当 $|z| > 1$ 时 $\frac{1}{1-z} = -\frac{1}{z}\frac{1}{1-z^{-1}} = -\sum_{n=0}^{\infty} z^{-(n+1)}$。搞反展开方向会导致级数不收敛。
13. **部分分式分解后再展开时遗漏符号**：$\frac{1}{z(z-1)} = \frac{1}{z-1} - \frac{1}{z}$。$\frac{1}{z-1} = -\frac{1}{1-z} = -\sum_{n=0}^{\infty} z^n$，遗漏负号会得到错误系数。
14. **收敛半径计算中比值法使用不当**：$R = \lim |a_n/a_{n+1}|$，注意是 $a_n$ 在上、$a_{n+1}$ 在下，而不是反过来。根值法中 $R = 1/\limsup \sqrt[n]{|a_n|}$。

### 留数理论
15. **简单极点留数公式的误用**：$\operatorname{Res}(f, z_0) = \lim_{z \to z_0} (z-z_0)f(z)$ 只适用于简单极点（一阶极点）。对高阶极点必须使用导数公式。
16. **极点阶数判断错误**：$z=0$ 在 $1/(z(z-1)^2)$ 中是简单极点（因分母中的 $z$ 只有一次），$z=1$ 是二阶极点（因分母中有 $(z-1)^2$）。混淆阶数会使用错误的留数公式。
17. **$m$ 阶极点留数公式的阶乘因子**：$\operatorname{Res}(f, z_0) = \frac{1}{(m-1)!} \lim \frac{d^{m-1}}{dz^{m-1}}[(z-z_0)^m f(z)]$。遗漏 $1/(m-1)!$ 因子是常见错误。
18. **三角积分代换中遗漏 $dz/(iz)$ 因子**：$d\theta = dz/(iz)$，不是 $dz/z$ 也不是 $iz\,dz$。遗漏 $i$ 或弄反 $i$ 会得到错误的积分值。
19. **有理函数围道积分忘记验证次数条件**：$\int_{-\infty}^{\infty} P(x)/Q(x)\,dx$ 要求 $\deg Q \geq \deg P + 2$，以确保大半圆弧积分趋于0。若只差1次，需要使用Jordan引理或其他方法。

### 保形映射
20. **Möbius变换边界验证的遗漏**：$w = \frac{z-i}{z+i}$ 映实轴时，对 $z=x \in \mathbb{R}$，$|w| = |x-i|/|x+i| = 1$（因为分子分母互为共轭）。不验证这一点就无法保证边界对应正确。
21. **混淆上半平面和下半平面的映射方向**：同一个映射 $w = \frac{z-i}{z+i}$ 将上半平面映为单位圆盘内部，将下半平面映为单位圆盘外部。必须用测试点确定方向。

### 经典定理
22. **Liouville定理反证中遗漏有界性的归结**：证明代数学基本定理时，需要分别论证 $|z| > R$ 时 $|1/P(z)| < 1$ 和 $|z| \leq R$ 时 $|1/P(z)|$ 由连续性有界。遗漏任一论证都无法得出整函数有界。
23. **最大模原理证明中等号条件的误判**：平均值性质取模后得到的不等式链中，等号成立需要 $|f(z_0+re^{i\theta})| \equiv M$ 对所有 $\theta$ 恒成立，这需要连续的三角不等式等号条件，而非仅在某一点成立。
24. **Rouché定理应用时占优项选取不当**：在 $|z|=1$ 上比较 $|z^8|=1$、$|3z^3|=3$ 和 $|1|=1$ 时，应选取 $|3z^3| = 3$ 作为 $|f(z)|$（模最大者），其余两项之和作为 $|g(z)|$。选取错误的占优项会导致无法满足 $|f| > |g|$。
25. **辐角原理中零点/极点重数的遗漏**：$m$ 重零点贡献的留数是 $m$，$k$ 阶极点贡献的留数是 $-k$。计重数是辐角原理的核心要求，遗漏重数会使 $N-P$ 的值不正确。

---

## 模块速查：关键公式速查表

### 复数运算

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **极坐标表示** | $z = r(\cos\theta + i\sin\theta) = re^{i\theta}$ | $r = \|z\|$, $\theta = \arg(z)$ |
| **de Moivre公式** | $(re^{i\theta})^n = r^n e^{in\theta}$ | $n \in \mathbb{Z}$ |
| **模的性质** | $\|z_1 z_2\| = \|z_1\| \|z_2\|$, $\|z^n\| = \|z\|^n$ | 任意复数 |
| **共轭性质** | $\overline{z_1 z_2} = \overline{z_1} \cdot \overline{z_2}$, $z\overline{z} = \|z\|^2$ | 任意复数 |

### 解析函数与C-R方程

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **Cauchy-Riemann方程** | $u_x = v_y$, $u_y = -v_x$ | $f=u+iv$ 在某点可导 |
| **Laplace方程** | $u_{xx} + u_{yy} = 0$, $v_{xx} + v_{yy} = 0$ | $u, v$ 是解析函数的实/虚部 |
| **导数表达式** | $f'(z) = u_x + iv_x = v_y - iu_y$ | 在解析点处 |
| **共轭调和函数通式** | $v = \int u_x\,dy - \int (u_y + \frac{\partial}{\partial x}\int u_x\,dy)\,dx$ | $u$ 调和 |

### Cauchy积分理论

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **Cauchy积分定理** | $\oint_C f(z)\,dz = 0$ | $f$ 在 $C$ 及其内部解析 |
| **Cauchy积分公式** | $f(a) = \frac{1}{2\pi i} \oint_C \frac{f(z)}{z-a}\,dz$ | $f$ 在 $C$ 及内部解析，$a$ 在 $C$ 内 |
| **高阶Cauchy公式** | $f^{(n)}(a) = \frac{n!}{2\pi i} \oint_C \frac{f(z)}{(z-a)^{n+1}}\,dz$ | $f$ 在 $C$ 及内部解析，$a$ 在 $C$ 内 |
| **ML估计** | $\left\|\oint_C f(z)\,dz\right\| \leq ML$ | $\|f(z)\| \leq M$, $L$ 为 $C$ 的长度 |

### 级数展开

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **几何级数** | $\frac{1}{1-z} = \sum_{n=0}^{\infty} z^n$ | $\|z\| < 1$ |
| **几何级数（外侧）** | $\frac{1}{1-z} = -\sum_{n=1}^{\infty} z^{-n}$ | $\|z\| > 1$ |
| **收敛半径（比值法）** | $R = \lim_{n\to\infty} \left\|\frac{a_n}{a_{n+1}}\right\|$ | 极限存在 |
| **收敛半径（根值法）** | $R = 1 / \limsup_{n\to\infty} \sqrt[n]{\|a_n\|}$ | 一般情况 |

### 留数理论

| 公式名称 | 精确表达式 | 适用条件 |
|---------|-----------|---------|
| **留数定理** | $\oint_C f(z)\,dz = 2\pi i \sum \operatorname{Res}(f, z_j)$ | $f$ 在 $C$ 内除 $z_j$ 外解析 |
| **简单极点留数** | $\operatorname{Res}(f, z_0) = \lim_{z\to z_0} (z-z_0)f(z)$ | $z_0$ 为一阶极点 |
| **$m$ 阶极点留数** | $\operatorname{Res}(f, z_0) = \frac{1}{(m-1)!} \lim_{z\to z_0} \frac{d^{m-1}}{dz^{m-1}}[(z-z_0)^m f(z)]$ | $z_0$ 为 $m$ 阶极点 |
| **$P/Q$ 在简单极点的留数** | $\operatorname{Res}(P/Q, z_0) = P(z_0)/Q'(z_0)$ | $P(z_0)\neq 0$, $Q(z_0)=0$, $Q'(z_0)\neq 0$ |
| **三角积分代换** | $z=e^{i\theta}$, $d\theta = dz/(iz)$, $\cos\theta = (z+z^{-1})/2$ | $\theta \in [0, 2\pi]$ |

### 经典定理

| 定理 | 精确陈述 | 典型应用 | 相关习题 |
|------|---------|---------|---------|
| **Liouville定理** | 有界整函数必为常数 | 证明代数学基本定理 | idx 15, 17 |
| **最大模原理** | 非常数解析函数的模不能在区域内取最大值 | 解析函数模的上下界估计 | idx 16 |
| **代数学基本定理** | $n$ 次（$n \geq 1$）复系数多项式在复数域中恰有 $n$ 个根（计重数） | 多项式根的分布 | idx 17 |
| **辐角原理** | $\frac{1}{2\pi i} \oint_C \frac{f'}{f} = N - P$ | 计算区域内零点与极点个数之差 | idx 18 |
| **Rouché定理** | 若在 $C$ 上 $\|f\| > \|g\|$，则 $f$ 和 $f+g$ 在 $C$ 内零点数相同 | 确定方程在指定区域内的零点数 | idx 9, 19 |
| **平均值性质** | $f(z_0) = \frac{1}{2\pi} \int_0^{2\pi} f(z_0 + re^{i\theta})\,d\theta$ | 证明最大模原理 | idx 16 |
| **Cauchy估计** | $\|f^{(n)}(z_0)\| \leq \frac{n! M}{R^n}$（其中 $M$ 为 $f$ 在圆盘上的上界） | 证明Liouville定理 | idx 15 |
| **Jordan引理** | $\lim_{R\to\infty} \int_{\Gamma_R} e^{i\alpha z}f(z)\,dz = 0$（$\alpha > 0$, $\Gamma_R$ 为上半圆） | 含三角函数的无穷积分 | idx 12 |

### 保形映射

| 公式名称 | 精确表达式 | 映射关系 |
|---------|-----------|---------|
| **上半平面到单位圆盘** | $w = \frac{z-i}{z+i}$ | $\mathbb{H} \to \mathbb{D}$ |
| **单位圆盘到上半平面** | $w = i\frac{1-z}{1+z}$（Cayley变换） | $\mathbb{D} \to \mathbb{H}$ |
| **一般Möbius变换** | $w = \frac{az+b}{cz+d}$（$ad-bc \neq 0$） | 圆到圆，保对称性 |

---

## 模块速查：计算题标准解法速查

### 类型A：复数高次幂（de Moivre公式）
**步骤**：极坐标 $re^{i\theta}$ $\to$ $(re^{i\theta})^n = r^n e^{in\theta}$ $\to$ 化回代数形式

例：$(\sqrt{3}+i)^6 = (2e^{i\pi/6})^6 = 64 e^{i\pi} = -64$。

### 类型B：判断解析性
**步骤**：分离 $u(x,y)$ 和 $v(x,y)$ $\to$ 计算偏导 $\to$ 检查C-R方程 $u_x=v_y$, $u_y=-v_x$ 成立的点的范围 $\to$ 判断是否在开邻域内成立

例：$f(z)=|z|^2$: $u=x^2+y^2$, $v=0$, C-R给出 $2x=0$, $2y=0$，仅在原点满足，故处处不解析。

### 类型C：Cauchy积分公式
**步骤**：验证 $f$ 解析且 $a$ 在围道内 $\to$ $\oint \frac{f(z)}{z-a} dz = 2\pi i f(a)$

例：$\oint_{|z|=1} \frac{e^z}{z} dz = 2\pi i \cdot e^0 = 2\pi i$。

### 类型D：高阶Cauchy积分公式
**步骤**：识别 $n$ 和 $a$ $\to$ 求 $f^{(n)}(a)$ $\to$ $\oint \frac{f(z)}{(z-a)^{n+1}} dz = \frac{2\pi i}{n!} f^{(n)}(a)$

例：$\oint_{|z|=2} \frac{e^z}{(z-1)^3} dz$：$n=2$, $f^{(2)}(z)=e^z$, $f^{(2)}(1)=e$, 结果 $\pi i e$。

### 类型E：Laurent级数展开
**步骤**：部分分式 $\to$ 根据圆环域选择几何级数展开方向 $\to$ 合并正负幂

例：$\frac{1}{z(z-1)} = \frac{1}{z-1} - \frac{1}{z} = -\frac{1}{1-z} - \frac{1}{z} = -\sum_{n=0}^{\infty} z^n - \frac{1}{z}$（$0<|z|<1$）。

### 类型F：留数计算
**步骤**：判断奇点类型 $\to$ 简单极点用 $\lim (z-z_0)f(z)$；$m$ 阶极点用导数公式

例：$f = 1/[z(z-1)^2]$：$z=0$ 简单极点 $\operatorname{Res}=1$；$z=1$ 二阶极点 $\operatorname{Res}=-1$。

### 类型G：有理函数实积分
**步骤**：验证 $\deg Q \geq \deg P + 2$ $\to$ 找上半平面极点 $\to$ 计算留数 $\to$ 积分 $ = 2\pi i \sum \operatorname{Res}$

例：$\int_{-\infty}^{\infty} \frac{dx}{x^4+1} = 2\pi i \cdot \sum_{\operatorname{Im}>0} \frac{1}{4z_k^3} = \frac{\pi}{\sqrt{2}}$。

### 类型H：三角积分围道法
**步骤**：$z=e^{i\theta}$ 代换 $\to$ 化简为 $\oint_{|z|=1} f(z) dz$ $\to$ 在单位圆内求留数 $\to$ 积分 $ = 2\pi i \sum \operatorname{Res}$

例：$\int_0^{2\pi} \frac{d\theta}{5+4\cos\theta} = 2\pi i \cdot \frac{1}{3i} = \frac{2\pi}{3}$。

### 类型I：Rouché定理应用
**步骤**：在边界 $C$ 上比较各项的模 $\to$ 确定占优项 $f(z)$（模最大）$\to$ 验证 $|f| > |g|$（$g$ 为其余项之和）$\to$ 计算 $f(z)$ 的零点数

例：在 $|z|=1$ 上 $|3z^3|=3 > |z^8+1|\leq 2$，由Rouché定理有3个零点。

### 类型J：保形映射区域判断
**步骤**：验证边界映射 $\to$ 取一个内部测试点 $\to$ 由边界对应原理得出结论

例：$w=\frac{z-i}{z+i}$：实轴 $\to |w|=1$；$z=i \to w=0 \in \mathbb{D}$，故将上半平面映为单位圆盘。

---

## 模块速查：证明题标准策略速查

### 策略1：双方向极限法
**适用**：C-R方程必要性（idx 14）

模式：令 $h$ 沿实轴和虚轴分别趋于0，两个极限必须相等，比较实部和虚部得出C-R方程。

### 策略2：不等式估计 + 极限法
**适用**：Liouville定理（idx 15）

模式：利用Cauchy导数公式写出 $f'$ 的积分表示 $\to$ ML估计得 $|f'| \leq M/R$ $\to$ 令 $R \to \infty$ 得 $f'=0$ $\to$ $f$ 为常数。

### 策略3：反证法 + 平均值性质
**适用**：最大模原理（idx 16）

模式：假设在某内点取最大模 $\to$ 取小圆周应用平均值性质 $\to$ 不等式链迫使模在圆周上恒为常数 $\to$ 唯一性定理推出矛盾。

### 策略4：反证法 + Liouville定理
**适用**：代数学基本定理（idx 17）

模式：假设多项式无根 $\to$ $1/P$ 是整函数 $\to$ 证明 $1/P$ 有界 $\to$ Liouville定理 $\to$ 矛盾。

### 策略5：留数分析 + 留数定理
**适用**：辐角原理（idx 18）

模式：考察 $f'/f$ 的奇点（恰为 $f$ 的零点和极点）$\to$ 在零点和极点处分别计算留数（$m$ 和 $-k$）$\to$ 用留数定理求和。

### 策略6：同伦族 + 辐角原理
**适用**：Rouché定理（idx 19）

模式：构造 $F_t = f + tg$ 的同伦族 $\to$ $N(t) = \frac{1}{2\pi i} \oint F_t'/F_t$ 是连续整数值函数故为常数 $\to$ $N(0) = N(1)$ 得证。

---

## 模块速查：参考资源

- 配套验证知识提示：`复分析验证示例.py`
- 数据集来源：`复分析.md`（20题，涵盖全部核心知识点）
- 推荐教材：《复变函数》（Ahlfors）、《Complex Analysis》（Stein-Shakarchi）、《复变函数与积分变换》
- 在线工具：SymPy Live、SageMath、Wolfram Alpha

---

## 模块速查：虚二次域范数方程与复数表示

### 核心概念

设 $d > 0$ 为无平方因子正整数，虚二次域 $\mathbb{Q}(\sqrt{-d})$ 中的代数整数形如：
$$z = a + b\sqrt{-d} = a + bi\sqrt{d} \quad (a, b \in \mathbb{Z})$$

其**范数**定义为：
$$N(z) = z \cdot \overline{z} = a^2 + d b^2$$

范数是乘性的：$N(z_1 z_2) = N(z_1)N(z_2)$。

### 范数方程与丢番图方程

虚二次域的范数方程 $N(z) = n$ 等价于丢番图方程：
$$a^2 + d b^2 = n$$

其中 $a, b$ 为整数（若考虑代数整数环）或有理数（若考虑域本身）。

**典型问题：** 给定 $n$ 和 $d$，求所有满足 $a^2 + d b^2 = n$ 的整数解 $(a, b)$。这在竞赛中以 Pell 型方程或二次型表示整数的形式出现。

### 复数视角下的范数方程

将虚二次域嵌入复平面：$\sqrt{-d} \leftrightarrow i\sqrt{d}$。则 $z = a + bi\sqrt{d}$ 是复平面上以 $\sqrt{d}$ 为虚轴缩放因子的格点：

$$|z|^2 = a^2 + d b^2 = N(z)$$

因此 $N(z) = n$ 表示复平面上格点 $z$ 到原点的距离平方为 $n$。

**分解性质：** 若 $n = n_1 n_2$ 且 $n_1 = a_1^2 + d b_1^2$, $n_2 = a_2^2 + d b_2^2$，则 $n$ 也可表示为平方和：
$$n = (a_1 a_2 - d b_1 b_2)^2 + d(a_1 b_2 + a_2 b_1)^2$$

这对应于复数乘法的范数乘性：
$$(a_1 + b_1 i\sqrt{d})(a_2 + b_2 i\sqrt{d}) = (a_1 a_2 - d b_1 b_2) + (a_1 b_2 + a_2 b_1)i\sqrt{d}$$

### 竞赛常见题型

1. **整数的平方和表示唯一性：** 在虚二次域中讨论 $a^2 + d b^2$ 表示的唯一性（与类数相关）
2. **范数方程的整数解计数：** 利用虚二次域的整数环结构（特别是 $d=1,2,3$ 时为主理想环）分析解的存在性和个数
3. **单位根与对称性：** 虚二次域的单位群（$\mathbb{Z}[\sqrt{-d}]$ 的单位）限制为 $\pm 1$（$d \ge 2$ 时），仅在 $d=1$（Gauss整数）和 $d=3$（Eisenstein整数）时有额外单位根，这影响了解的分类

### 易错点

- **混淆范数与模**：$N(a+b\sqrt{-d}) = a^2 + d b^2$，而 $|a+b\sqrt{-d}| = \sqrt{a^2 + d b^2} = \sqrt{N(z)}$。范数是模的平方
- **$d=1$ 的特殊性**：Gauss整数环 $\mathbb{Z}[i]$ 的范数为 $a^2 + b^2$，与通常复数模平方一致。对于 $d > 1$，范数中的系数 $d$ 使格点沿虚轴拉伸
- **分解不唯一**：在类数大于1的虚二次域中，代数整数环不是 UFD，范数方程的求解需要更细致的分析

### 应试解题技巧

- 判断 $n$ 能否表示为 $a^2 + d b^2$：先检查模 $p$ 条件（二次剩余），再利用复数乘法的范数乘性进行分解
- 利用复数共轭的范数等式快速验证解的合法性：$N(z_1 z_2) = N(z_1)N(z_2)$ 可用于约化高次范数方程
