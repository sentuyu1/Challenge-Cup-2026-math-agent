# Intern-S1 数学智能体系统 — 挑战杯 XH-202627 参赛方案

## 环境要求

- Python >= 3.10
- 能够访问书生平台 Intern-S1 API

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Lagent 框架

```bash
# 方式一：从 GitHub 安装（推荐）
git clone https://github.com/InternLM/lagent.git
cd lagent && pip install -e .

# 方式二：pip 直接安装
pip install lagent
```

### 3. 配置 API 密钥

```bash
# 复制环境变量模板，编辑 .env 填入你的 API Key
echo INTERN_S1_API_KEY=你的密钥 > .env
```

## 运行方式

### 交互模式（逐题问答）

```bash
# 基础单 Agent 版
python math_agent.py

# 5 Agent 推理流水线版（推荐）
python pipeline_agent.py

# 参赛完整版（内嵌 3 道示例）
python 03_lagent_competition.py
```

### 批量模式（从 JSON 文件读题）

```bash
# 直接 API 批量求解（需要 .env）
python batch_solver.py --input 18_problems.json --output results.json

# Lagent Agent 批量求解（需要 .env）
python batch_solver_lagent.py --input 18_problems.json --output results_lagent.json

# 5 Agent 流水线批量求解
python pipeline_agent.py --batch 18_problems.json --output results.json
```

## 核心架构

```
pipeline_agent.py  ← 5 Agent 推理流水线（核心创新）
  ├── 问题分析师 → 理解题意
  ├── 策略规划师 → 规划解法
  ├── 数学求解器 → 推导+代码执行
  ├── 答案校验员 → 反思纠错
  └── 启发式教师 → 知识点总结

math_agent.py  ← 基础单 Agent 版
03_lagent_competition.py  ← 参赛完整版
```

## 文件说明

```
pipeline_agent.py              核心智能体（5 Agent 推理流水线，含重试机制）
math_agent.py                  基础版智能体（单 Agent + Python 执行）
03_lagent_competition.py       参赛完整版（内嵌 3 道示例）
batch_solver.py                批量解题（直接 OpenAI API 调用）
batch_solver_lagent.py         批量解题（Lagent Agent + 代码解释器）

requirements.txt               Python 依赖

── 测试数据集 ──
18_problems.json               18 个数学领域各一题
38_hard_problems.json          38 道困难题（全领域覆盖）
fix_6_problems.json            6 道修复题（代码优先策略）
sample_18_domains_problems_only.json  赛题提供的 18 领域样本
```

## 技术栈

- **推理引擎**：Intern-S1（书生平台，OpenAI 兼容接口）
- **智能体框架**：Lagent（InternLM 开源）
- **计算支持**：NumPy / SymPy / SciPy
- **输出格式**：结构化 JSON + LaTeX 数学公式
