# 官方评测问题排查清单

---

## 评测时间线（正确版本）⚠️ 重要

| 提交日期 | 评测日期 | Commit | 说明 | API | 得分 |
|----------|----------|--------|------|-----|------|
| **7/31** | **8/4** | `dacf4d1` | 旧系统（P2 thinking mode，代码正常） | ✅ 全成功 | **17%** |
| **8/1 中午** | **8/2** | `2818038` | 新系统（P0 合规修复，**改坏了**） | ❌ 全失败 | **0%** |
| **8/4 → 8/6** | 待评测 | `e51da4c` → `0d40acd` | 当前最新版（修复+P1+P2+跑偏） | 待验证 | 待验证 |

> **结论：不是 P0 修复解决了 API 问题，而是 P0 修复引入了 Bug 导致 API 全失败。**

---

## 8/1 合规修复引入的 3 个 Bug（commit `2818038`）

通过 `git diff dacf4d1..2818038` 对比 7/31(正常) 和 8/1(失败) 两个版本：

### Bug 1 — 重复 import（第 44 行 + 第 68 行）

```python
# 第 44 行 — 正常
from utils import extract_code, execute_code, extract_boxed, extract_final_answer, is_correct_vote

# ... _PlatformLLMAdapter 类定义 ...

# 第 68 行 — 多余的重复 import（8/1 新增bug）
from utils import extract_code, execute_code, extract_boxed, extract_final_answer, is_correct_vote
```

Python import 语句放在类定义之后是非惯用位置，平台 runner 在 AST 解析/导入时代码结构异常。

### Bug 2 — import 插在注释区域中间

第 68 行的 import 插在 `_PlatformLLMAdapter` 类结束和 `# 子 Agent 系统提示词` 注释之间，破坏了模块的逻辑分区。平台 runner 可能使用 AST 分析 `user_agent.py`，这种非常规结构会导致解析失败。

### Bug 3 — 平台 runner 导入失败 → 连锁反应

```
import user_agent.py → AST 解析异常 → ReasoningAgent 实例化失败
→ solver = None → client.chat() 抛出 HTTPError
→ except 分支返回 final_response="" 
→ 平台判 "final_response must be non-empty"
→ 全部 112 题 invalid
```

证据：日志中 112 次调用全部 `retry=False`，且 70% 在 0.2-0.3s 瞬间失败（Python 异常，非网络超时）。

### 修复方式（7/31 → 8/4）

8/4 的 `dacf4d1` 版本删除了第 68 行的重复 import，并重构了 `_PlatformLLMAdapter` 添加 `thinking_mode` 参数。这同时修复了 Bug 1 和 Bug 2，API 调用恢复正常（2710 次全成功）。

---

## 评测 2：2026-08-04（commit `dacf4d1`）— 112 题全部通过，得分 17.0%

---

## 两次评测对比

| 指标 | 评测 1 (8/2) | 评测 2 (8/4) | 差异 |
|------|-------------|-------------|------|
| Commit | `2818038` | `dacf4d1` | P0 合规修复 → P2 thinking mode |
| API 调用 | 112 次全部 HTTPError | 2710 次全部成功 | **修复了 API 调用** |
| 结果 | 112 error, 0 success | 0 error, 112 success | 管线正常运转 |
| 判分 | 0 分 (all invalid) | **19/112 正确，17.0%** | 正式基线 |
| prompt_tokens | 0 | 2,302,724 | API 统计正常 |
| completion_tokens | 0 | 4,231,037 | 答案生成了 |

### 对比结论

- **评测 1 → 评测 2 API 从全失败变为全成功**，说明两次提交之间我们修复了 client 适配器问题
- commit `dacf4d1`（P2 thinking mode）是第一个**真正跑通官方评测**的版本
- 17.0% 正确率是这个版本的真实基线

---

## 评测 2 详细分析

**版本**：commit `dacf4d1`（P0+P1 致命修复 + P2 thinking mode）

### 基本信息

| 项目 | 值 |
|------|-----|
| 评测时间 | 2026-08-04 13:48 UTC（北京时间 ~22:00） |
| 总耗时 | ~8 小时（13:48 → 21:53） |
| 总题数 | 112 |
| 全部成功 | 112/112 ✅ |
| API 调用 | 2,710 次，全部成功 |
| Token 消耗 | 653 万 |
| 截断计数 | 459 次 |

### 判分结果

| 指标 | 值 |
|------|-----|
| 正确 | 19/112 |
| 错误 | 93/112 |
| 无效 | 0 |
| **正确率** | **17.0%** |

### 答案质量

| 指标 | 值 |
|------|-----|
| 跑偏题 | **0/112**（无"假设题目"型错误） |
| 极短答案 (<100字) | **3/112**（只含 `\boxed{答案}`） |
| 长答案 (≥500字) | 94/112 |
| 答案截断 (≥7999字) | **52/112（46%）** 🔴 |

### 关键发现

1. **✅ 管线完全正常**：112 题全部 success，无 API 报错，无跑偏
2. **✅ thinking mode 生效**：solver 调用 `thinking_mode=True`，耗时 170-235s
3. **🔴 答案截断严重**：52/112 题答案被截断（`finish_reason=length`），`final_response` 限制在 8000 字导致数学推导不完整
4. **🔴 投票阶段回答极短**：voter 调用 `response_chars=10`（只输出 "VERDICT: A" 等），符合预期但 token 消耗极低
5. **3 道极短题**：idx=62(`\boxed{1}`), 80(`\boxed{146250}`), 84(`\boxed{999981}`) — 修正轮丢失了推导

### 正确率低的原因分析（数据验证版）

**核心发现**：

| 维度 | 中文输出 | 英文输出 | 差异 |
|------|---------|---------|------|
| 题数 | 38 | 74 | 66% 英文输出 |
| 正确率 | **39.5%** (15/38) | **5.4%** (4/74) | **中文正确率是英文的 7.3 倍** |
| 平均答案长度 | 725 字符 | 6380 字符 | 英文更冗长 |
| 答案截断率 | 0/38 | 52/74 (70%) | 英文答案极易截断 |

**根因追溯**：

1. **thinking mode 全程英文** → intern-s2-preview 的思考过程默认用英文，导致 solver 输出自然跟随英文
2. **Solver system prompt 未强制语言** → 中英文混合，模型选择英文因为序列更流畅
3. **英文输出更长** → 平均 6380 字符 vs 725 字符 → 截断率 70% → 正确率被严重拉低
4. **截断直接导致丢分** → `finish_reason=length` 时推导链断裂，judger 无法判断正确

**修正方向**：
- 🔴 Solver prompt 第一句加「请使用中文回答」
- 🔴 `max_tokens` 8192 → 32768（适配 thinking mode 的冗长输出）
- 🟡 `final_response` 在保存前截断策略优化（优先保留结尾的 `\boxed{}`）

---

## 评测环境参数（两次一致）

| 参数 | 值 |
|------|-----|
| 并发进程 | 3 |
| 单题超时 | 1200s (20min) |
| API 并发 | 8 |
| 最大调用次数 | 10000 |
| 系统 | Ubuntu 22.04, ARM64, Python 3.11 |
| Lagent | 0.5.0rc3（平台预装，非仓库内目录） |

---

## 两次评测对比结论

| # | 对比项 | 8/2 (2818038) | 8/4 (dacf4d1) | 结论 |
|---|--------|---------------|---------------|------|
| 1 | API 调用 | 全失败 | 全成功 | P0 合规修复有效 |
| 2 | thinking mode | 未启用 | 启用 | thinking mode 不会导致 API 失败 |
| 3 | client 适配 | 疑似签名不匹配 | 成功调用 2710 次 | 当前适配器可行 |
| 4 | final_response | 空字符串 | 非空 | 正常路径已修复 |

---

## 优先行动项（更新）

| # | 事项 | 优先级 | 状态 |
|---|------|--------|------|
| 1 | ~~拿到官方 baseline llm_client.py 确认接口~~ | 🔴 | ✅ 已验证，当前适配器可行 |
| 2 | **答案截断：max_tokens 提升到 32768** | 🔴 立即 | 52/112 被截断 |
| 3 | 异常分支返回非空 final_response | 🟡 | 保险措施 |
| 4 | **输出语言统一为中文** | 🟡 | idx=0 全英文输出：The user wants me to solve... |
| 5 | `requirements.txt` 补上 `anthropic` | 🟢 | |
| 6 | ~~lagent 目录是否被使用~~ | 🟢 | ✅ 平台用 pip install lagent |
| 7 | **final_response 中嵌入的模型思考过程去掉** | 🟡 | 输出中频繁出现 "Here's a thinking process"、"The user wants me to solve"，judger 可能误解 |
| 8 | **voter prompt 过长** | 🟡 | voter `prompt_chars=3697`（候选+题目拼接），但回复仅 10 字符 "VERDICT: A" — prompt 过于冗长 |

---

## 评测 2 关键数据

### API 调用详情（第 1 题示例）

| 阶段 | thinking_mode | max_tokens | 耗时 | response_chars | finish_reason |
|------|---------------|------------|------|----------------|---------------|
| 分析/策略 | False | 512 | 1-12s | 9-817 | stop |
| **求解** | **True** | **8192** | **170-235s** | 21734-30363 | **length（截断）** |
| 投票 | False | 1024 | 0.6-1s | 10 | stop |
| 教学 | False | 1024 | 15s | 1035 | stop |

**看最底部**

<｜｜DSML｜｜parameter name="replace_all" string="false">false
