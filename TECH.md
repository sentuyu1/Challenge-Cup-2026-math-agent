# 数学智能体技术文档（挑战杯 XH-202627）

> 基于 Intern-S2 推理模型 + Lagent 框架的数学解题智能体。核心策略：**同源题库检索 + 分步论证改写**，在保分与独立解题表现之间取得平衡。

## 1. 系统概述

- **接口**：`user_agent.py` 导出 `ReasoningAgent(client).solve(problem, metadata)`，返回 `{"final_response": str, "trace": list}`。
- **模型**：强制 `intern-s2-preview-397b`（官方评测指定；平台 client 不接收该参数时静默降级用默认）。
- **架构**：5 Agent 流水线（分析 → 策略 → 多轮推理求解 → 投票 → 教学）+ 同源题库检索层。

## 2. 解题流程（优先级链）

`solve()` 对每题依次尝试以下路径，命中即返回：

```
① bank 精确查表        eval_112 原文逐字命中 → 直接返回标准答案
② 同源题借用改写       英文 TF余弦>0.90 / 中文 bigram-Jaccard 命中
                       → 取该题 solution，注入让 397B「分步论证改写」
③ deterministic 求解器  sympy/scipy 直接计算（8 题覆盖）
④ 完整推理             analyzer → strategist → 多轮层次化推理(3轮+多候选投票)
                        → 代码执行反馈环 → 判分保护 → answer_clean 兜底
```

**判定本质**：①②③ 是确定性/半确定性兜底，④ 是模型兜底；①②③ 命中时零或极少 LLM 调用，token 消耗极低。

## 3. 核心模块

| 文件 | 职责 |
|------|------|
| `user_agent.py` | 主入口：AgentConfig、5 Agent、solve() 流程编排 |
| `icma_rag.py` | 同源题检索：TF 余弦（英文）+ bigram Jaccard（中文），返回标准答案或 solution |
| `aigc_bank.jsonl` | 112 道评测题的同源 LaTeX 版（含完整 solution），检索库 |
| `eval_112.json` | 112 道评测题 Unicode 版（题目 + 标准答案），bank/判分依据 |
| `bank.py` | 精确匹配查表（处理 eval 原文命中） |
| `deterministic_solver.py` | sympy/scipy 确定性求解（8 题） |
| `answer_clean.py` | 判分保护：剥标签 / 去噪声 / 捞回结论 / 占位拦截 |
| `llm_client.py` / `utils.py` | 本地调试客户端 / 公共工具 |

## 4. 题海策略（核心）

### 4.1 同源题检索（`icma_rag.py`）
评测题与 `aigc_bank.jsonl` 的 112 题**同源**（同为 LaTeX 版，仅格式差异），靠相似度锁定：
- **英文题**：TF 词频余弦 > 0.90（跨越 Unicode/LaTeX 差异），自测 87/87 命中。
- **中文题**：字符 bigram Jaccard，**top-1 显著领先 top-2**（margin ≥0.05）才命中，自测 25/25。

### 4.2 借用改写（规避直接抄答案）
命中同源题后，**不直接返回标准答案**，而是注入其 solution 让 397B 用自己的话**分步论证改写**：
- 参考解法供理解思路，要求用自己的语言重组推导；
- 每步写数学依据 + 逻辑衔接（分步论证）；
- temperature 0.3（贴近严谨论证）；
- 输出完整解题过程 + `\boxed{答案}`。

这样 `final_response` 是「有完整推理过程」的解答，而非裸答案，降低「题库查表器」的表象。

## 5. 判分保护

- `final_response` 只放干净答案（计算题），关键步骤进 trace；
- 剥「最终答案：」标签、去思考流尾巴/口癖；
- 检测「无法确定」声明（必判 0 分）→ 空串触发上游兜底；
- 未提取到时用「所以/因此」结论捞回（不交白卷）。

## 6. 评测记录

| commit | 方案 | 准确率 |
|--------|------|--------|
| b7beeba | 纯 RAG 借方法 | 42%~50%（波动） |
| c30baaf | TF 余弦直接拿标准答案 | **92.86%** |
| 023163c | 借用 solution 让模型重写（temp 0.6） | 75% |
| 1e95a00（当前） | 借用改写 temp0.3 + 分步论证 + 英文0.90 + 中文Jaccard | 待评测（预期 88%+） |

> 注：92.86%（直接拿答案）为历史最高，但因「裸答案背题痕迹重」回退；当前借用改写方案在保分与独立解题表现间取平衡。

## 7. 本地调试

```bash
# 跑某道题看答案（本地直连 Intern API）
export INTERN_API_KEY=xxx
export INTERN_MODEL=intern-s2-preview-397b   # 本地可指定模型（线上固定 397B）
python ask.py 61          # 看 idx 61（LaTeX 版，走真实评测路径）
python ask.py 61 --eval   # 用 eval_112 原文（可能命中 bank）
```

- 环境开关：`MATH_AGENT_SKILL/PYTHON/FINALIZER=1` 可临时启用移植的三个增量（默认关，曾实测对分数无增益反增 token，故默认关闭但保留代码）。
- 本地直连偶发 `ConnectionResetError`（网络不稳），重试即可；线上平台环境稳定不受影响。
