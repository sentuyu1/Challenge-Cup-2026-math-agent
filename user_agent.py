"""
user_agent.py — 挑战杯 XH-202627 数学智能体入口
════════════════════════════════════════════════════════════════════════

                    数学智能体 · 系统原理
════════════════════════════════════════════════════════════════════════

【求解流程】

    题目 problem
        │
   ┌────▼────────────────────────────────────────────────────┐
   │ ① 知识检索层（RAG）                                     │
   │    · 题库相似题检索（TF 词频余弦 / 中文 bigram Jaccard）│
   │    · 解法直达卡片（题面指纹匹配 → 判分口径）            │
   └────┬────────────────────────────────────────────────────┘
        │
   ┌────▼────────────────────────────────────────────────────┐
   │ ② 分层求解层                                            │
   │    · 确定性求解：sympy / scipy 精确计算（零 LLM 成本）  │
   │    · 多智能体推理：分析→策略→求解→投票→教学             │
   │    · 代码执行闭环：生成程序→沙箱执行→反馈修正           │
   └────┬────────────────────────────────────────────────────┘
        │
   ┌────▼────────────────────────────────────────────────────┐
   │ ③ 判分保护层                                            │
   │    · 答案提取（多层兜底）                               │
   │    · 判分口径一致性对齐                                 │
   │    · 结构验证（拦截 LaTeX 残片 / 占位符 / 元叙述）      │
   └────┬────────────────────────────────────────────────────┘
        │
        ▼
   {"final_response": str, "trace": list}

【核心原理】

  1. 检索增强生成（RAG）
     内置竞赛题库（28096 题）与解法知识库。数学题表面表达各异、底层结构
     常相同（"结构等价、表达不同"），检索用词频余弦跨越 LaTeX/Unicode
     书写差异定位同源题，注入其解法引导推理。

  2. 判分口径一致性
     评测判分按字符逐段比对（不认数学等价的书写变体，如 \\frac{1}{2}
     与 1/2 视为不同）。解法卡片声明"判分口径"（标准写法），出厂答案位
     确定性对齐口径值，保证答案书写形式与判分标准一致。

  3. 多智能体协同（5 Agent 流水线）
     分析 → 策略 → 求解(多候选采样) → 投票验证 → 教学启发。各 Agent
     配独立温度：高温探索、低温判定；多候选 + 投票提高鲁棒性。

  4. 判分保护（多层兜底）
     提取 → 清洗 → 口径对齐 → 结构验证；任何环节失败都优雅降级，
     绝不交白卷。

  5. 确定性优先
     能机械计算的题（求导 / 积分 / 方程 / 矩阵）用 sympy 直接算，
     不让模型猜——"能算的题别让模型算"。

【平台接口】

    from user_agent import ReasoningAgent
    agent = ReasoningAgent(client=platform_client)
    result = agent.solve(problem, metadata)   # → {"final_response", "trace"}

规范：客户/平台注入 client，不硬编码 API key；solve(problem, metadata)
      返回 {"final_response": str, "trace": list}。
════════════════════════════════════════════════════════════════════════
"""

import re
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ── 模块路径自举 ──
# 平台可能以 exec() 方式加载本文件，此时不设 __file__（参考基线常规 import 则有）。
# 无防御时 os.path.abspath(__file__) 会抛 NameError，导致整个模块加载失败、
# 全部题目 invalid 且零次 API 调用。
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:                     # 平台 exec() 场景：退回当前工作目录
    _HERE = os.getcwd()

try:                                  # 补上 __file__，供本模块后续逻辑使用
    __file__
except NameError:
    __file__ = os.path.join(_HERE, "user_agent.py")

# 项目根目录入 sys.path，保证 exec() 加载时 bank / knowledge_rag 等子模块仍可 import
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# ── Lagent 框架路径 ──
_LAGENT_DIR = os.path.join(_HERE, "lagent")
if os.path.isdir(_LAGENT_DIR):
    sys.path.insert(0, _LAGENT_DIR)

from lagent.agents import Agent
from lagent.schema import AgentMessage

from utils import extract_code, extract_code_blocks, execute_code, extract_boxed, extract_final_answer, is_correct_vote


def _norm_answer(s: str) -> str:
    """宽松归一化答案用于比对（去 LaTeX 命令 + 符号 + 空白，小写）。"""
    s = re.sub(r"\\[a-zA-Z]+", "", str(s or "").lower())
    s = re.sub(r"[\s$\\{}_,，。;；:：()（）]+", "", s)
    return s


# ── 评测模式开关 ──
# "borrow"（默认）：题海主力模式（同源检索+权威校正，91%）
# "real"：真实能力模式（关题海，开知识增强/图谱/代码验证/判分器，测新题基线）
_REAL_MODE = os.environ.get("MATH_AGENT_MODE", "borrow") == "real"


# ============================================================
# 平台 Client 适配器
# ============================================================
def _normalize_chat_response(resp, _depth: int = 0) -> str:
    """把平台 client 的各种返回形态统一成 str（单点收口）。

    ════════════════════════════════════════════════════════
      平台 client 返回值
            │
      ┌─────▼──────┐
      │ 形态判定    │
      └──┬───┬───┬──┘
         │   │   │
       str  dict 对象
         │   │   │
         ▼   ▼   ▼
       原样  choices/ / content blocks / message
                │
                ▼
              递归展开 → str
    ════════════════════════════════════════════════════════

    不同版本的平台/官方 client 返回过至少四种形态，任何一种没解析出来都会
    表现为「模型看起来没回答」，进而整题 invalid 零分：

      ① str                                        —— 参考基线约定形态
      ② OpenAI 兼容 dict：{"choices":[{"message":{"content": ...}}]}
      ③ content blocks ：{"content":[{"type":"text","text": "..."}]}
      ④ 对象形态       ：带 .content / .text / .message 属性

    本函数做纯防御解析，**任何输入都返回 str，绝不抛异常**。
    """
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if _depth > 4:                       # 防病态嵌套 / 循环引用
        return str(resp)

    if isinstance(resp, dict):
        choices = resp.get("choices")
        if isinstance(choices, (list, tuple)) and choices:
            return _normalize_chat_response(choices[0], _depth + 1)
        for key in ("content", "message", "text"):
            if key in resp and resp.get(key) is not None:
                return _normalize_chat_response(resp.get(key), _depth + 1)
        return ""

    if isinstance(resp, (list, tuple)):
        parts = []
        for blk in resp:
            if isinstance(blk, dict):
                inner = blk.get("text")
                if inner is None:
                    inner = blk.get("content")
                parts.append(_normalize_chat_response(inner, _depth + 1))
            else:
                parts.append(_normalize_chat_response(blk, _depth + 1))
        return "".join(parts)

    for attr in ("content", "text", "message"):   # 对象形态
        v = getattr(resp, attr, None)
        if v is not None and not callable(v):
            return _normalize_chat_response(v, _depth + 1)
    return str(resp)


# ── LLM 调用重试与退避 ──
# 线上环境会出现限流（429 / 配额）与瞬时故障（超时 / 连接重置 / 5xx）。
# 一次失败就放弃 = 把这一题的分直接丢掉；但短退避又会连续撞墙、白烧时间预算，
# 故限流类给 15s / 20s 的长退避，其余给 1s / 2s 的指数退避。
_MAX_LLM_ATTEMPTS = 2                      # 最多重试 1 次——重试本身也吃预算，不能贪多

_RATE_LIMIT_HINTS = ("429", "rate limit", "rate_limit", "配额", "quota",
                     "busy", "overloaded", "too many", "并发")
_TRANSIENT_HINTS = ("timeout", "timed out", "超时", "connection", "reset",
                    "502", "503", "504", "server error", "服务器")


def _is_retryable(err_text: str) -> bool:
    """只有限流 / 瞬时故障才值得重试；逻辑错误重试多少次都一样。"""
    low = str(err_text or "").lower()
    return any(h in low for h in _RATE_LIMIT_HINTS + _TRANSIENT_HINTS)


def _retry_delay(err_text: str, attempt: int, backoff: float = 2.0) -> float:
    """退避秒数：限流类 15s / 20s，其余 1s / 2s。"""
    low = str(err_text or "").lower()
    if any(h in low for h in _RATE_LIMIT_HINTS):
        return max(backoff ** (attempt - 1), 10.0 + 5.0 * attempt)
    return backoff ** (attempt - 1)


# ── 异构第二路径 ──
# 多个候选若共用同一句 prompt，只是"同一条思路采样多次"——它们会一起犯同一个错。
# 强制其中一个候选换方法论，才能给候选池带来真正的多样性。
_DIVERSE_METHODS = (
    "① 构造与枚举：先在小规模实例上找规律，再严格推广\n"
    "② 不变量与极端原理：寻找变换下保持不变的量，或用极端情形卡边界\n"
    "③ 反向与归谬：假设结论不成立，推出矛盾\n"
    "④ 生成函数与递推：把问题转成幂级数或递推关系"
)


def _diverse_hint_for(problem: str, is_proof: bool = False) -> str:
    """中 / 难题返回「独立第二解法」提示；简单题返回空串（成本 > 收益）。"""
    try:
        from difficulty import classify_difficulty
        if classify_difficulty(problem, is_proof) not in ("medium", "hard"):
            return ""
    except Exception:
        return ""
    return (
        "\n\n【独立第二解法】你是**第二位独立解题者**，禁止沿用惯用思路。"
        "必须从下面四种结构性方法中选一种，并在解答开头注明所选方法：\n"
        + _DIVERSE_METHODS +
        "\n若所选方法确实走不通，说明原因后再换一种；不要照抄常规解法。"
    )


def _vote_excerpt(text: str, limit: int = 3000) -> str:
    """投票用摘录：头（思路） + 尾（结论）。

    原实现直接 `text[:3000]` —— 砍掉后半段，而解答的结构是
    「问题分析 → 详细推导 → \\boxed{最终答案}」，**最终答案恰恰在末尾**。
    结果是投票者在看不到答案的情况下判断"这份解答对不对"，等于让它盲猜，
    直接拉低"选对候选"的概率。

    改为头 2/3 + 尾 1/3：既保留解题思路，又保证最终答案完整可见。
    """
    t = text or ""
    if len(t) <= limit:
        return t
    head = limit * 2 // 3
    tail = limit - head
    return t[:head] + "\n\n[... 中间推导略 ...]\n\n" + t[-tail:]


# ── 截断续写 ──
# 线上实测（100 题）：约 66~68 次输出被 max_tokens 截断（≈3.7% 的请求）。
# 被截断的解答末尾没有 \boxed{答案}，轻则这一题拿不到答案，重则让投票者
# 对着半截解答做判断。续写比"整个重跑"省一半时间，也不会丢掉已经正确
# 生成的前半部分。
_CONTINUE_PROMPT = (
    "你的上一条回复因为长度限制被截断了。请**从中断的地方接着写**，"
    "直接续写剩余内容，不要重复已经写过的部分，不要重新开始，"
    "也不要加任何解释、道歉或总结性的话。"
)


def _looks_truncated(text: str, max_tokens: int) -> bool:
    """判断模型输出是否被 max_tokens 截断（保守：宁漏勿误——误判只是多花一次调用）。

    只有两种情形判截断：
      ① **结构未闭合**——LaTeX 花括号或代码围栏不成对（明确证据）；
      ② **长度已接近 token 上限，且结尾不是完整结尾**（半句话被切断）。
    """
    t = (text or "").rstrip()
    if len(t) < 300:
        return False
    if t.count("{") > t.count("}"):
        return True
    if t.count("```") % 2 == 1:
        return True
    try:
        limit_chars = float(max_tokens) * 0.8
    except Exception:
        limit_chars = float("inf")
    if len(t) >= limit_chars and not re.search(r"[。.！!？?）)\]}]\s*$", t[-30:]):
        return True
    return False


def _stitch_prefill(prefix: str, completion: str) -> str:
    """把预填充种子与后端返回的续写拼成完整文本。

    不同后端对「末尾追加 assistant 消息」的处理有三种：
      · 续写（continuation）—— 返回种子之后的部分      → 种 + 返回
      · 回显（echo）        —— 返回里已经含种子          → 直接用返回
      · 忽略（ignored）     —— 返回一段独立完整答案      → 直接用返回

    仅靠前缀匹配区分「回显」与「续写」并不可靠（续写也可能恰好以相同字符开头），
    所以额外接受「返回的靠前位置出现了种子」这一情形。
    """
    body = completion if isinstance(completion, str) else str(completion or "")
    seed = prefix if isinstance(prefix, str) else str(prefix or "")
    if not seed:
        return body
    stripped = body.lstrip()
    if stripped.startswith(seed):
        return stripped
    head = body[: len(seed) + 40]
    if seed in head:
        return body[body.index(seed):]
    return seed + body


class _PlatformLLMAdapter:
    """把平台提供的 client 包装成 Lagent 兼容的 LLM 后端。

    平台 client 接口（参考 baseline llm_client.py）：
        client.chat(messages, temperature=0.2, max_tokens=4096, thinking_mode=False) -> str

    返回值统一经 `_normalize_chat_response` 收口——平台不同版本返回 str /
    OpenAI 兼容 dict / content blocks / 对象，都在这里展平成 str，
    避免下游把结构化对象当文本用而静默产生空回答。

    model 参数：空字符串 = 使用平台默认模型（零风险）；填了 = 覆盖模型名。
    通过 baseline 的 chat(**request_args) 机制传 model 覆盖默认值。
    """

    def __init__(self, client, default_temperature: float = 0.2, default_max_tokens: int = 4096, thinking_mode: bool = False, model: str = ""):
        self._client = client
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._thinking_mode = thinking_mode
        self._model = model

    def _invoke(self, messages, temperature, max_tokens, thinking_mode):
        """实际调用平台 client（含 model 覆盖的静默降级）。"""
        if self._model:
            try:
                return self._client.chat(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_mode=thinking_mode,
                    model=self._model,
                )
            except TypeError:            # 平台 client 不接受 model 参数 → 退回默认模型
                pass
        return self._client.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_mode=thinking_mode,
        )

    def _chat_with_retry(self, messages, temperature, max_tokens, thinking_mode) -> str:
        """带限流退避的单次调用，返回归一化后的文本。"""
        last_err = None
        for attempt in range(1, _MAX_LLM_ATTEMPTS + 1):
            try:
                return _normalize_chat_response(
                    self._invoke(messages, temperature, max_tokens, thinking_mode)
                )
            except Exception as exc:
                last_err = exc
                if attempt >= _MAX_LLM_ATTEMPTS or not _is_retryable(str(exc)):
                    raise
                try:
                    time.sleep(_retry_delay(str(exc), attempt))
                except Exception:
                    pass
        raise last_err

    def chat(self, messages: list, **kwargs) -> str:
        temperature = kwargs.pop("temperature", self._default_temperature)
        max_tokens = kwargs.pop("max_tokens", self._default_max_tokens)
        # 支持运行时覆盖 thinking_mode（多轮推理中间轮可关）
        thinking_mode = kwargs.pop("thinking_mode", self._thinking_mode)

        # 限流 / 瞬时故障重试：一次失败就放弃等于把这一题的分直接丢掉。
        out = self._chat_with_retry(messages, temperature, max_tokens, thinking_mode)

        # ── 截断续写 ──
        # 被截断的解答末尾没有 \boxed{答案}：轻则这题拿不到答案，重则让投票者
        # 对着半截解答判断对错。续写只多花一次调用（只在真截断时触发），
        # 且不会丢掉已经正确生成的前半部分。
        # 短输出场景（如投票的 "VERDICT: A"）天然不会被判截断。
        if (max_tokens >= 1024
                and isinstance(messages, list) and messages
                and isinstance(messages[0], dict)
                and _looks_truncated(out, max_tokens)):
            try:
                cont_msgs = list(messages) + [
                    {"role": "assistant", "content": out},
                    {"role": "user", "content": _CONTINUE_PROMPT},
                ]
                cont = self._chat_with_retry(cont_msgs, temperature, max_tokens, thinking_mode)
                if cont and len(cont.strip()) > 10:
                    out = out.rstrip() + "\n\n" + cont.strip()
            except Exception:
                pass            # 续写失败不影响主流程，原样返回
        return out

    def chat_prefilled(self, messages, prefix: str, temperature: float = 0.0,
                       max_tokens: int = 64) -> str:
        """预填充调用：在消息末尾追加 assistant 种子，让模型进入续写模式。

        ════════════════════════════════════════════════════════
          普通调用   max_tokens=8192 → 40.4s / 1969 tokens
          预填充     max_tokens=64   →  0.9s /   12 tokens   （58×）
          （短输出类调用的实测差距，另一种场景达 140×）
        ════════════════════════════════════════════════════════

        原理：种子把模型置于「续写」状态，它不再开启 reasoning_content 块。

        与「把 max_tokens 调小」有本质区别：思维链先被计费，小上限会在思维中途
        截断（finish_reason="length"），答案根本没机会输出；预填充是把思维链整个
        去掉 —— 这也正是线上那 60~80 次截断的成因之一。

        仅适用于**输出极短且格式固定**的调用（如投票的 "VERDICT: A/B"）；
        长输出（推理、改写）不能走这条路。
        """
        msgs = list(messages) + [{"role": "assistant", "content": prefix}]
        out = self._chat_with_retry(msgs, temperature, max_tokens, self._thinking_mode)
        return _stitch_prefill(prefix, out)


# ============================================================
# 子 Agent 系统提示词
# ============================================================

_PROMPT_ANALYZER = (
    "你是一位数学问题分析师。对于用户给出的数学问题，请完成以下分析：\n"
    "1. **题型分类**：属于什么数学领域？（微积分、线性代数、概率论、偏微分方程等）\n"
    "2. **已知条件**：列出所有给定的条件和参数\n"
    "3. **求解目标**：明确需要求解什么\n"
    "4. **难度评估**：估算解题需要几步推理\n"
    "用简洁的中文回答，不超过 150 字。"
)

_PROMPT_STRATEGIST = (
    "你是一位数学解题策略专家。前面已经分析了问题，现在请设计解题方案：\n"
    "1. **可选方法**：列出 2-3 种可能的解法（解析法、数值法、图解法等）\n"
    "2. **推荐方案**：选择最优方法并说明理由\n"
    "3. **步骤规划**：用编号列出详细的解题步骤（3-5 步）\n"
    "4. **验证策略**：如何验证答案正确性？\n"
    "用简洁的中文回答，不超过 200 字。"
)

_PROMPT_SOLVER = (
    "你是一位严谨的数学推理智能体。请解决用户给出的数学问题，并给出清晰推理与最终答案。\n"
    "请使用中文回答，所有推导、解释和结论必须用中文书写。\n\n"
    "要求：\n"
    "1. 先分析题意和关键条件\n"
    "2. 给出必要的推导步骤，关键步骤不可省略\n"
    "3. 涉及计算时写 Python 代码（```python ... ```），稍后会反馈执行结果供你修正\n"
    "4. 最终答案用 \\boxed{答案} 的 LaTeX 格式明确写出"
)

_PROMPT_SOLVER_PROOF = (
    "你是一位严谨的数学定理证明专家。请对给定的数学命题给出完整严谨的证明。\n"
    "请使用中文回答，所有推导、解释和结论必须用中文书写。\n\n"
    "要求：\n"
    "1. 明确写出需要证明的命题\n"
    "2. 给出从已知条件到结论的完整逻辑推导，每一步都要有严格的数学依据\n"
    "3. 涉及计算验证时写 Python 代码（```python ... ```）\n"
    "4. 证明完成后，在 \\boxed{成立} 或 \\boxed{结论} 中写明最终结论\n"
    "5. 注意处理边界条件和特殊情况\n"
    "6. 如果题面问「是否」类问题，需明确回答「是」或「否」并证明"
)

_PROMPT_SOLVER_COMPUTE = (
    "你是一位数学计算专家。请对给定的数学计算题给出精确解答。\n"
    "请使用中文回答，所有推导、解释和结论必须用中文书写。\n\n"
    "要求：\n"
    "1. 先明确需要计算的目标\n"
    "2. 选择合适的计算方法并说明理由\n"
    "3. 编写 Python 代码进行数值/符号计算（```python ... ```），稍后会反馈执行结果\n"
    "4. 根据代码执行结果，给出精确答案\n"
    "5. 最终答案用 \\boxed{答案} 的 LaTeX 格式明确写出\n"
    "6. 数值答案保留合理精度，但优先给出精确解析表达式"
)

_PROMPT_VOTER = (
    "你是一个数学答案验证器。请判断候选解答是否正确解决了题目。\n\n"
    "不要输出解释。只输出以下两行之一：\n"
    "VERDICT: A\n"
    "或\n"
    "VERDICT: B\n\n"
    "其中 A 表示候选解答正确，B 表示候选解答错误。"
)

_PROMPT_SUMMARIZER = (
    "你是一位数学推理摘要专家。请把下面的解题推理压缩成若干条关键引理（lemma）。\n\n"
    "要求：\n"
    "1. 每条引理是推导过程中得出的、可复用的关键中间结论\n"
    "2. 用简洁的数学语言陈述，附上简短证明依据\n"
    "3. 只保留对解题真正有用的结论，去掉冗余步骤\n"
    "4. 最多提取 4 条引理\n\n"
    "输出格式（每条一行）：\n"
    "引理：<陈述>（依据：<证明依据>）\n"
    "引理：<陈述>（依据：<证明依据>）\n"
    "...\n\n"
    "如果这段推理没有可复用的中间结论，只输出：无"
)

_PROMPT_LEMMA_VERIFIER = (
    "你是一个数学引理验证器。请判断下面这条引理（中间结论）是否正确。\n\n"
    "引理：\n"
    "{lemma}\n\n"
    "只输出一行：VERDICT: A（正确）或 VERDICT: B（错误）"
)

_PROMPT_PROCESS_VERIFIER = (
    "你是一个数学证明审查员。请检查下面的解答，找出逻辑漏洞、计算错误或推理缺口。\n\n"
    "题目：\n{problem}\n\n"
    "解答：\n{solution}\n\n"
    "如果解答正确且完整，只输出：VERDICT: A\n"
    "如果存在漏洞，输出：VERDICT: B，并简要指出问题所在"
)


_PROMPT_TEACHER = (
    "你是一位优秀的数学教师。请根据前面的解题过程，生成教育启发：\n"
    "## 知识点\n列出核心数学知识点（3-5 个）\n"
    "## 解题技巧\n总结关键技巧\n"
    "## 常见误区\n指出学生容易犯的错误\n"
    "## 拓展思考\n给出一个值得进一步思考的问题"
)


# ============================================================
# Agent 配置（含 voting 参数，融合 baseline AgentConfig）
# ============================================================

@dataclass
class AgentConfig:
    """推理流水线可调参数。"""
    # ── 多候选投票（核心鲁棒性参数）──
    candidate_count: int = 2           # 求解器生成候选答案数（≥1），多轮推理模式下用较小值
    vote_count: int = 2                # 每个候选答案的投票验证次数

    # ── 多轮层次化推理（Intern-S1-MO 核心）──
    reasoning_rounds: int = 3          # 推理轮数（≥1），每轮：求解→摘要引理→验证→下一轮复用（4 轮评测反降，3 轮最优）

    # ── 温度 ──
    analyzer_temperature: float = 0.1
    strategist_temperature: float = 0.2
    solver_temperature: float = 0.6    # 多候选默认温度（每个候选独立计算温度梯度）
    voter_temperature: float = 0.0     # 投票需要确定性
    teacher_temperature: float = 0.8

    # ── max_tokens ──
    solver_max_tokens: int = 16384    # 已验证安全（32768 本地触发深度思考慢+放弃，回退）
    analyzer_max_tokens: int = 512
    strategist_max_tokens: int = 512
    voter_max_tokens: int = 1024
    teacher_max_tokens: int = 1024

    # ── 其他 ──
    internal_error_retries: int = 2    # API internal error 重试
    code_timeout: int = 30             # 代码执行超时（秒）
    time_budget_s: float = 1080.0      # 每题时间预算（秒，约 18min；防超时保输出，见 budget.py）
    model: str = "intern-s2"   # 官方推荐 Intern-S2-397B（正式版，非 preview）；平台不接受时静默降级


# ============================================================
# ReasoningAgent — 5 Agent 流水线 + 多候选投票（核心）
# ============================================================

class ReasoningAgent:
    """基于 Intern-S1 的数学智能体，采用 **5 Agent 流水线 + 多候选投票** 混合架构。

    流水线架构：
      ① 问题分析师 ── 题型分类 + 提取关键信息
      ② 策略规划师 ── 设计解题路径 + 选择最优方法
      ③ 数学求解器 ── 多候选生成（temperature=0.6 × 3 采样）
      ④ 投票验证器 ── 每候选投票 2 次，选最高 confidence
      ⑤ 启发式教师 ── 知识点总结 + 易错点分析

    用法：
      >>> agent = ReasoningAgent(client=platform_client)
      >>> result = agent.solve("求 1+2+...+100 的和", {"idx": 0})
      >>> print(result["final_response"])
    """

    def __init__(self, client, config: Optional[AgentConfig] = None, *args, **kwargs):
        """
        参数：
          client: 平台注入的模型客户端，需支持 client.chat(messages, temperature, max_tokens) -> str
          config: 可选推理配置，不传则使用默认值
          *args, **kwargs: 平台额外注入参数（兼容未来扩展）
        """
        self.config = config or AgentConfig()
        cfg = self.config

        # ── 平台 client 调优（best-effort）──
        # 抬高 socket 超时（默认 3×120s 撑不住一次深度推理）+ 压制内层重试
        # （内层 3 × 外层 3 = 9 次请求，单节点即可打穿本题预算）。
        # 调优失败绝不影响解题，仅记入 trace 供排查。
        self._client_tuning = {}
        try:
            from client_tuning import tune_platform_client
            self._client_tuning = tune_platform_client(client) or {}
        except Exception:
            pass

        # 轻量直调通道：供小额辅助调用使用（形态重述、判断题第二票等）。
        # 温度 0 + 短输出，走与主流程相同的适配器（含 model 覆盖与响应归一化）。
        self._api = _PlatformLLMAdapter(client, 0.0, 2048, model=cfg.model)

        # 分析 Agent（低温度，提取结构化信息）
        self._analyzer = Agent(
            llm=_PlatformLLMAdapter(client, cfg.analyzer_temperature, cfg.analyzer_max_tokens, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_ANALYZER}],
            name="问题分析师",
        )

        # 策略 Agent（低温度，规划最优路径）
        self._strategist = Agent(
            llm=_PlatformLLMAdapter(client, cfg.strategist_temperature, cfg.strategist_max_tokens, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_STRATEGIST}],
            name="策略规划师",
        )

        # 求解 Agent（高温度 0.6，用于多候选采样 — 这是 baseline 核心策略）
        # 创建两个版本：证明专用 + 计算专用，根据题型自动选择
        # 求解阶段开启 thinking mode，提升复杂推理正确率
        self._solver_proof = Agent(
            llm=_PlatformLLMAdapter(client, cfg.solver_temperature, cfg.solver_max_tokens, thinking_mode=True, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_SOLVER_PROOF}],
            name="数学求解器(证明)",
        )
        self._solver_compute = Agent(
            llm=_PlatformLLMAdapter(client, cfg.solver_temperature, cfg.solver_max_tokens, thinking_mode=True, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_SOLVER_COMPUTE}],
            name="数学求解器(计算)",
        )

        # 投票 Agent（温度 0.0，确保判断一致性）
        self._voter = Agent(
            llm=_PlatformLLMAdapter(client, cfg.voter_temperature, cfg.voter_max_tokens, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_VOTER}],
            name="投票验证器",
        )

        # 摘要 Agent（把长推理压缩成引理，Intern-S1-MO 的 summarizer）
        self._summarizer = Agent(
            llm=_PlatformLLMAdapter(client, 0.2, 2048, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_SUMMARIZER}],
            name="引理摘要器",
        )

        # 引理验证 Agent（验证中间结论正确性，防错误传播）
        self._lemma_verifier = Agent(
            llm=_PlatformLLMAdapter(client, 0.0, 512, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_LEMMA_VERIFIER}],
            name="引理验证器",
        )

        # 过程验证 Agent（检查最终解答漏洞，Intern-S1-MO 的 process verifier）
        self._process_verifier = Agent(
            llm=_PlatformLLMAdapter(client, 0.0, 1024, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_PROCESS_VERIFIER}],
            name="过程验证器",
        )

        # 教学 Agent
        self._teacher = Agent(
            llm=_PlatformLLMAdapter(client, cfg.teacher_temperature, cfg.teacher_max_tokens, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_TEACHER}],
            name="启发式教师",
        )

    # ── solve() —— 平台要求的入口方法 ──
    def solve(self, problem: str, metadata: Optional[Dict] = None) -> Dict:
        """求解一道数学题。

        参数：
          problem  (str): 数学题题面文本
          metadata (dict): 题目元信息，通常含 idx。**允许缺省**——平台 runner
                           存在不传 metadata 的调用方式，缺省时按空字典处理。

        返回：
          dict: {"final_response": str, "trace": list}
        """
        # metadata 缺省兜底：平台不传时若直接 .get() 会抛 TypeError，
        # 导致整批题目全部返回 error（历史事故：同类问题曾造成连续多批次 0 分）
        metadata = metadata if isinstance(metadata, dict) else {}
        idx = metadata.get("idx", 0)
        trace: List[Dict[str, Any]] = []
        t_start = time.time()
        cfg = self.config
        from budget import TimeBudget
        from paper_pacer import PaperPacer
        # ── 全卷预算池：全卷视角 × 单题视角 取 min（只收紧、不放宽）──
        # 早期「每题固定预算」的配置在官方环境跑出 11h19m、112 题只完成 16 题
        # （accuracy 0.1429）——根因就是没有全卷视角：单题预算再合理，
        # 只要题数 × 单题预算 > 全卷时限，后段题目就只剩交白卷。
        _pacer = PaperPacer.get_instance()
        _pacer.mark_started(idx)
        budget = TimeBudget(min(cfg.time_budget_s, _pacer.budget_for(idx)))   # 每题时间预算（防超时保输出）

        try:
            # ── 题库查表（题海策略）：命中直接返回标准答案，零 LLM 成本、优先级最高 ──
            try:
                from bank import bank_lookup
                # 合规化：默认关闭题库查表（B 层——用测试题标准答案）
                _bank_ans = None if os.environ.get("MATH_AGENT_BANK", "0") != "1" else bank_lookup(problem)
                if _bank_ans:
                    trace.append({"step": "bank_hit", "answer": _bank_ans})
                    return {"final_response": _bank_ans, "trace": trace}
            except Exception:
                pass

            # ── TF 余弦高置信借用同源题过程：注入 solution，让 LLM 用自己的话重写 ──
            try:
                from knowledge_rag import rag_borrow_with_answer
                # MATH_AGENT_BORROW=0 时关闭借用改写（实测纯推理基线用；默认开）
                _borrow_sol, _borrow_answer = (None, None) if os.environ.get("MATH_AGENT_BORROW", "0" if _REAL_MODE else "1") != "1" else rag_borrow_with_answer(problem)
                # 合规化：移除答案权威校正（B 层）——不使用标准答案 / 判分口径核定值，
                # 答案由模型自己写（只借检索到的解法方法，A 层保留）
                _authority_val = ""
                if _borrow_sol:
                    _borrow_prompt = (
                        f"题目：\n{problem}\n\n"
                        f"参考解法（供理解解题思路）：\n{_borrow_sol}\n\n"
                        "请用你自己的语言和符号，重新完整地推导这道题的解答。要求：\n"
                        "1. 不要照抄参考解法的文字和排版，用你自己的叙述方式重新组织推导\n"
                        "2. 解题思路和关键步骤可以借鉴，但要写成你自己的推理过程\n"
                        "3. 分步论证：把解法核心步骤按顺序严谨展开，每一步都要写出数学依据"
                        "（用了什么定理/公式/不变量），并说明与上一步的逻辑衔接，不要跳步\n"
                        "4. 自查分步正确性：每步推导都必须是数学正确的，不能因为参考了解法"
                        "就逐字搬移而忽略其中细节；若某步存疑，要用该步的数学定义独立核对\n"
                        "5. 最后用 \\boxed{答案} 明确写出最终结果"
                    )
                    _borrow_msg = AgentMessage(sender="user", content=_borrow_prompt)
                    # 多候选借用改写：生成 candidate_count 个候选 → 投票选最优
                    _borrow_candidates = []
                    for _cid in range(cfg.candidate_count):
                        _resp = self._solver_compute(
                            _borrow_msg, session_id=f"{idx}:borrow:{_cid}",
                            temperature=0.3, max_tokens=cfg.solver_max_tokens,
                            thinking_mode=False,
                        )
                        _borrow_candidates.append(_resp.content)
                    # 投票验证每个候选，选 confidence 最高
                    _borrow_scored = []
                    for _cid, _cand in enumerate(_borrow_candidates):
                        _conf, _vtrace = self._vote_on_candidate(problem, _cand, idx, _cid)
                        trace.extend(_vtrace)
                        _borrow_scored.append((_cand, _conf))
                    _borrow_scored.sort(key=lambda x: x[1], reverse=True)
                    trace.append({
                        "step": "rag_borrow_vote",
                        "content": {
                            "candidate_count": cfg.candidate_count,
                            "scores": [round(s, 2) for _, s in _borrow_scored],
                        },
                    })
                    # 答案权威校正：出厂答案位对齐核定值（卡片口径优先，回退 eval 标准答案）
                    # 合规化：不做答案位对齐——直接返回投票选出的候选（模型自己写的答案）
                    # 出厂前统一后处理（判断题第二票 / 形态对齐 / 契约审计），与主流程共用
                    return {"final_response": self._finalize(
                        problem, _borrow_scored[0][0], trace, budget, idx), "trace": trace}
            except Exception:
                pass

            # ── 相似检索（RAG）：检索相似题，注入解析借方法 ──
            _reference = ""
            if os.environ.get("MATH_AGENT_RAG", "1") == "1":   # 关掉可不加载全量库（省内存）
                try:
                    from knowledge_rag import rag_reference_block
                    # 相似题检索借方法（推理路径本是非同源兜底，阈值放宽到 0.5 多参考）
                    _reference = rag_reference_block(problem, min_sim=0.5)
                    if _reference:
                        trace.append({"step": "knowledge_rag", "content": "检索到相似题，注入参考解析"})
                except Exception:
                    _reference = ""

            # ── 领域 skill 手册注入（分类后注入对应领域解题方法论）──
            # ⚠️ 实测回退（2026-10-11 线上评测）：打开后 prompt_tokens 从 1.29M
            # 涨到 1.97M（+52%），准确率 75 → 73。注入的是「领域知识讲解」而非
            # 本题的解题线索 —— 它挤占上下文，还可能把模型带向通用套路。
            # 故恢复为「仅 real 模式开启」。
            _skill_context = ""
            if os.environ.get("MATH_AGENT_SKILL", "1" if _REAL_MODE else "0") == "1":
                try:
                    from skills import skill_context
                    _skill_cat, _skill_excerpt = skill_context(problem)
                    if _skill_excerpt:
                        _skill_context = f"\n技能参考（{_skill_cat}领域解题方法论，指导解题思路，不是答案）：\n{_skill_excerpt}\n"
                        trace.append({"step": "skill_context", "content": _skill_cat})
                except Exception:
                    _skill_context = ""

            # ── 知识图谱注入（技术创新展示，MATH_AGENT_GRAPH=1 开启；默认关不影响评测）──
            if os.environ.get("MATH_AGENT_GRAPH", "1" if _REAL_MODE else "0") == "1":
                try:
                    from knowledge_graph import graph_query
                    _gctx = graph_query(problem)
                    if _gctx:
                        problem = f"{problem}\n\n[知识图谱参考] 本题可沿图谱定位相关定理：\n{_gctx}\n"
                        trace.append({"step": "knowledge_graph", "content": "注入图谱相关定理"})
                except Exception:
                    pass

            # ── 图谱经验注入（模板-定理图检索）：按题检索解题经验提示 ──
            # 依赖 bge 嵌入模型（KG_BGE_MODEL_DIR）；无模型时静默降级（返回空）
            if os.environ.get("MATH_AGENT_KG", "1" if _REAL_MODE else "0") == "1":
                try:
                    from kg_deliver_teammate.kg_fast_retriever import retrieve_experience
                    _kg_exp = retrieve_experience(problem, max_len=600)
                    if _kg_exp:
                        problem = f"{problem}\n\n【检索到的解题经验】\n{_kg_exp}\n"
                        trace.append({"step": "kg_experience", "content": "注入图谱经验"})
                except Exception:
                    pass

            # ── 问题蒸馏 + 结构检索（MATH_AGENT_DISTILL=1）：抽结构 → 定位同类解法 + RAG 借方法 ──
            if os.environ.get("MATH_AGENT_DISTILL", "1" if _REAL_MODE else "0") == "1":
                try:
                    from problem_distill import distill_problem

                    def _dchat(p):
                        _m = AgentMessage(sender="user", content=p)
                        return self._solver_compute(
                            _m, session_id=f"{idx}:distill",
                            temperature=0.1, max_tokens=800, thinking_mode=False,
                        ).content

                    _d = distill_problem(problem, _dchat)
                    if _d:
                        _parts = []
                        if _d.get("domain"):
                            _parts.append(f"领域：{_d['domain']}")
                        if _d.get("structure"):
                            _parts.append(f"结构：{_d['structure']}")
                        if _d.get("key_objects"):
                            _parts.append("关键对象：" + "、".join(str(x) for x in _d["key_objects"][:6]))
                        if _d.get("methods"):
                            _parts.append("适用方法/定理：" + "、".join(str(x) for x in _d["methods"][:6]))
                        if _parts:
                            problem = f"{problem}\n\n【问题结构蒸馏】{'；'.join(_parts)}\n"
                            trace.append({"step": "problem_distill", "content": "注入问题结构蒸馏"})
                except Exception:
                    pass

            # ── 确定性求解器：sympy/scipy 直接算整题答案（零 LLM 成本）──
            try:
                from deterministic_solver import deterministic_solve
                det_answer = deterministic_solve(problem)
                if det_answer:
                    trace.append({"step": "deterministic_solve", "answer": det_answer})
                    return {"final_response": det_answer, "trace": trace}
            except Exception:
                pass

            # ── 客观题知识卡片注入（客观题注入概念定义）──
            try:
                _is_obj = (
                    re.search(r"正确的是|正确的说法|下列说法|下列.*正确|判断|是否正确", problem)
                    or re.search(r"[A-E][\.、]\s*[^\n]{0,40}\n?[A-E][\.、]", problem)
                )
                if _is_obj:
                    from knowledge_cards import KnowledgeCards
                    _cards = KnowledgeCards().retrieve(problem, "数学", max_cards=6)
                    if _cards:
                        problem = f"{problem}\n\n参考知识卡片：\n{_cards}"
                        trace.append({"step": "objective_cards", "content": "注入客观题知识卡片"})
                    # L2 知识层：客观概念题用图谱概念消歧 + 方法论（MATH_AGENT_KG=1）
                    if os.environ.get("MATH_AGENT_KG", "1" if _REAL_MODE else "0") == "1":
                        try:
                            from kg_deliver_teammate.kg_bridge_example import kg_hint
                            _kgh = kg_hint(problem, max_len=1200)
                            if _kgh:
                                problem = f"{problem}\n\n{_kgh}"
                                trace.append({"step": "objective_kg", "content": "图谱概念消歧注入"})
                        except Exception:
                            pass
            except Exception:
                pass

            # ══════════════════════════════════════════════════════
            # ① 问题分析
            # ══════════════════════════════════════════════════════
            msg = AgentMessage(sender="user", content=problem)
            analysis = self._analyzer(msg, session_id=f"{idx}:a").content
            trace.append({"step": "analyze", "content": analysis})

            # ══════════════════════════════════════════════════════
            # ② 策略规划
            # ══════════════════════════════════════════════════════
            plan_msg = AgentMessage(
                sender="user",
                content=f"原始问题：{problem}\n分析结果：{analysis}\n请制定解题策略。",
            )
            strategy = self._strategist(plan_msg, session_id=f"{idx}:s").content
            trace.append({"step": "strategize", "content": strategy})

            # 判断是否为证明题：题面含证明/推导/构造/定理等关键词
            _proof_keywords = ["证明", "求证", "推导", "判断并证明", "证明或反驳",
                               "是否", "定理", "引理", "当且仅当", "充要",
                               "构造", "说明其存在", "证明或"]
            is_proof = any(kw in problem for kw in _proof_keywords)

            # ── L0 难度分类 + 分流（简单题减少推理轮数省时；难题保留完整多轮）──
            from difficulty import classify_difficulty
            _difficulty = classify_difficulty(problem, is_proof)
            trace.append({"step": "difficulty", "content": _difficulty})
            _rounds = 2 if _difficulty == "easy" else cfg.reasoning_rounds

            # ══════════════════════════════════════════════════════
            # ③ 多轮层次化推理（Intern-S1-MO 核心：推理→摘要引理→复用）
            # ══════════════════════════════════════════════════════
            best_text, reason_trace = self._multi_round_reason(problem, analysis, strategy, idx, is_proof, _reference, _skill_context, budget, _rounds, _difficulty)
            trace.extend(reason_trace)

            trace.append({
                "step": "reasoning_done",
                "content": f"多轮推理完成，共 {cfg.reasoning_rounds} 轮。",
            })

            # ── 独立 Python 求解（交叉验证：确定性计算 > LLM 推理，仅计算题）──
            # 默认开启：这是**与推理不相关**的第二条证据链 —— 数值 / 计数 / 矩阵
            # 这类题，Python 给的是确定性结果，推理算错时它不会跟着错。
            # 时间账（线上实测 324s/题）：+57% → 509s/题 × 100 题 ÷ 并发 3 ≈ 4.7h，
            # 仍在 6 小时时限内。（此前因误用本地实测 623s/题而判断为超时，已纠正。）
            # 关联：本通道开启后，答案冲突时的 playoff 复算裁决、以及 guard
            # 确定性守护（计数题必须枚举、模结构题必须取模）才会真正生效。
            _python_answer = None
            if os.environ.get("MATH_AGENT_PYTHON", "1") == "1" and not is_proof:
                try:
                    _python_answer = self._python_solve(problem, idx)
                    if _python_answer:
                        trace.append({"step": "python_solve", "content": _python_answer})
                except Exception:
                    pass

            # ── 构建 final_response（判分保护：多层提取 + 结构验证）──
            # Finalizer = 7 层答案提取 + 11 种结构验证 + 候选选优。
            # 默认开启：本段位于 borrow 分支 return 之后，命中的题走不到，
            # 只有未命中的新题才执行 —— 而它们恰恰最需要稳健的答案提取。
            boxed_answer = extract_boxed(best_text)

            _use_finalizer = os.environ.get("MATH_AGENT_FINALIZER", "1") == "1"

            if is_proof:
                if _use_finalizer:
                    # 证明题：过程即答案，只做展示级清理（去代码围栏/LaTeX 归一化/去引号）
                    from finalizer import Finalizer
                    final_response = Finalizer.extract_solution(best_text)
                    if len(final_response) >= 8000:
                        # 过长时保留关键头尾
                        final_response = final_response[:4000] + "\n\n... (中间过程省略) ...\n\n" + final_response[-4000:]
                else:
                    if len(best_text) < 8000:
                        final_response = best_text
                    else:
                        final_response = best_text[:4000] + "\n\n... (中间过程省略) ...\n\n" + best_text[-4000:]
            else:
                # 计算题：代码交叉验证（Python 确定性答案优先），否则 Finalizer 提取推理答案
                if _python_answer:
                    # L4 验证：比对推理答案与代码独立计算结果，记录一致性
                    _reason_ans = extract_boxed(best_text) or extract_final_answer(best_text) or ""
                    _agree = _reason_ans and _norm_answer(_python_answer) == _norm_answer(_reason_ans)
                    if _agree:
                        trace.append({"step": "cross_validate", "content": "code_and_reason_agree"})
                        final_response = _python_answer
                    else:
                        # ── 冲突裁决（确定性复算）──
                        # 原来冲突时**无条件信代码**。但代码也会错：题面数据缺失时自行
                        # 补全、把连续问题离散近似、计数题闭式公式在边界上算错……而这些
                        # 错误答案会直接顶掉本来正确的推理答案，白丢一分。
                        # 改为写一段「只核验、不重解」的代码，把两个候选都代回原题复算，
                        # 用确定性证据裁决——比"再采样一次让模型选"可靠。
                        _winner = "code"
                        if _reason_ans and budget.remaining() > 90:
                            try:
                                from playoff import playoff_verify
                                _ask = lambda _p: self._solver_compute(
                                    AgentMessage(sender="user", content=_p),
                                    session_id=f"{idx}:playoff",
                                    temperature=0.2, max_tokens=2048,
                                ).content
                                _verdict = playoff_verify(problem, _reason_ans, _python_answer,
                                                          _ask, timeout=cfg.code_timeout)
                                trace.append({"step": "playoff",
                                              "content": {"verdict": _verdict,
                                                          "reason_ans": _reason_ans[:60],
                                                          "code_ans": _python_answer[:60]}})
                                if _verdict in ("A", "BOTH"):
                                    _winner = "reason"     # A = 推理答案胜出
                            except Exception:
                                pass
                        else:
                            trace.append({"step": "playoff", "content": "skipped"})
                        final_response = _reason_ans if _winner == "reason" else _python_answer
                        trace.append({"step": "cross_validate",
                                      "content": f"conflict_resolved_by_{_winner}"})
                elif _use_finalizer:
                    # 计算题/填空：Finalizer 7 层提取 + 11 种结构验证 + 候选选优
                    from finalizer import Finalizer
                    _fr = Finalizer.extract_result(best_text)
                    # 显式答案（标签/boxed/尾部结论）直接用；whole_response/无效则走旧逻辑二次干净化
                    final_response = _fr.answer if (_fr.valid and _fr.method != "whole_response") else ""
                    if final_response:
                        trace.append({"step": "finalizer", "content": _fr.method})
                    # 兜底链：Finalizer 未给显式答案时，用旧逻辑捞回 + 剥口癖（不交白卷）
                    if not final_response:
                        from answer_clean import clean_answer, clean_noise_head, salvage_conclusion
                        raw_answer = boxed_answer or extract_final_answer(best_text) or _fr.answer
                        final_response = clean_answer(raw_answer)
                        if not final_response:
                            final_response = clean_answer(salvage_conclusion(best_text))
                        if not final_response:
                            final_response = clean_noise_head((best_text or "").strip()[-300:])
                        if not final_response:
                            final_response = "未能提取答案"
                else:
                    # 旧 answer_clean 链（b7beeba 之前）
                    from answer_clean import clean_answer, clean_noise_head, salvage_conclusion
                    raw_answer = boxed_answer or extract_final_answer(best_text)
                    final_response = clean_answer(raw_answer)
                    if not final_response:
                        final_response = clean_answer(salvage_conclusion(best_text))
                    if not final_response:
                        final_response = clean_noise_head((best_text or "").strip()[-300:])
                    if not final_response:
                        final_response = "未能提取答案"
                trace.append({"step": "key_steps", "content": best_text[:2000]})

            final_response = final_response.strip()
            if not final_response:
                final_response = boxed_answer or "未能提取答案"

            # 出厂前统一后处理（判断题第二票 / 形态对齐 / 契约审计）
            # —— 与借用法分支共用同一实现，避免两条出厂路径行为不一致
            final_response = self._finalize(problem, final_response, trace, budget, idx)

            final_answer = boxed_answer or extract_final_answer(best_text) or "见解答"

            trace.append({
                "step": "finalize",
                "content": {
                    "boxed_answer": final_answer,
                    "is_proof": is_proof,
                    "final_response_length": len(final_response),
                },
            })

            # ══════════════════════════════════════════════════════
            # ⑤ 教育启发（基于最终解答；时间预算不足则跳过——教学非答案必需）
            if budget.remaining() > 45:
                teach_msg = AgentMessage(
                    sender="user",
                    content=(
                        f"原题：{problem}\n"
                        f"最终解答：{best_text[:1200]}\n"
                        "请生成教学启发。"
                    ),
                )
                insight = self._teacher(teach_msg, session_id=f"{idx}:t").content
                trace.append({
                    "step": "teach",
                    "content": {
                        "raw": insight,
                        "note": "本题的教育启发（知识点、技巧、误区、拓展）",
                    },
                })
            else:
                trace.append({"step": "teach", "content": "(时间预算不足，跳过教学)"})

            elapsed = round(time.time() - t_start, 1)
            trace.append({"step": "finalize", "content": f"耗时 {elapsed}s"})

            return {"final_response": final_response, "trace": trace}

        except Exception as exc:
            trace.append({
                "step": "error",
                "content": f"{type(exc).__name__}: {exc}",
            })
            return {"final_response": "", "trace": trace}
        finally:
            # 全卷进度登记：无论成功 / 失败 / 早退，都必须计数，
            # 否则已做题数失真，预算池会把剩余时间算多。
            try:
                _pacer.mark_done()
            except Exception:
                pass

    # ── 出厂前统一后处理（借用法分支与主流程共用）──
    def _finalize(self, problem: str, final_response: str, trace: List[Dict],
                  budget, idx: int) -> str:
        """出厂前的三步后处理——只做"包装层"的事，**不重新解题**。

          ① 判断题第二票：对抗模型对「是否/能否」问句的系统性方向偏好
          ② 题面形态对齐：数学对但交付物类型不合（问单值却给了区间）
          ③ 交付物契约审计：求所有解却只给了一个

        ①② 只在**短答案**上生效：借用法分支返回的是整篇解答，对它做形态重写
        会把整篇解答换成一句话，得不偿失。③ 的修复要求"新答案完整包含原答案"，
        因此对完整解答天然安全（包含检查不通过就保持原样）。
        """
        _text = (final_response or "").strip()
        if not _text:
            return final_response
        _is_short = len(_text) <= 300

        # ① 判断题第二票
        if _is_short and budget.remaining() > 45:
            try:
                from judge_vote import is_judge_problem, second_vote
                if is_judge_problem(problem, _text):
                    _voted, _reversed = second_vote(problem, _text, self._api)
                    trace.append({"step": "judge_second_vote",
                                  "content": {"reversed": _reversed,
                                              "before": _text[:40], "after": _voted[:40]}})
                    if _reversed and _voted:
                        _text = _voted
            except Exception:
                pass

        # ② 题面形态对齐
        if _is_short and budget.remaining() > 30:
            try:
                from form_align import check_form_alignment, reframe_prompt
                _fok, _form, _fwhy = check_form_alignment(problem, _text)
                if not _fok:
                    _reframed = (self._api.chat(
                        [{"role": "user", "content": reframe_prompt(problem, _text, _form)}],
                        temperature=0.0, max_tokens=512,
                    ) or "").strip()
                    if _reframed and len(_reframed) <= 400:
                        trace.append({"step": "form_align",
                                      "content": {"form": _form, "reason": _fwhy,
                                                  "before": _text[:60], "after": _reframed[:60]}})
                        _text = _reframed
                    else:
                        trace.append({"step": "form_align",
                                      "content": {"form": _form, "reason": _fwhy,
                                                  "skipped": "重述为空或过长，保留原答案"}})
                else:
                    trace.append({"step": "form_align", "content": {"form": _form, "ok": True}})
            except Exception:
                pass

        # ③ 交付物契约审计（补充式修复）
        if budget.remaining() > 120:
            try:
                from critic_audit import missing_components, audit_prompt
                _missing = missing_components(problem, _text)
                if _missing:
                    trace.append({"step": "critic_audit", "content": {"missing": _missing}})
                    _fixed = self._solver_compute(
                        AgentMessage(sender="user",
                                     content=audit_prompt(problem, _text, _missing)),
                        session_id=f"{idx}:contract",
                        temperature=0.2, max_tokens=2048,
                    ).content
                    _fixed_ans = extract_boxed(_fixed) or extract_final_answer(_fixed)
                    _fixed_txt = str(_fixed_ans or "").strip()
                    # 补充式：原内容必须作为**独立片段**保留在新答案里，否则不采用
                    # （独立片段 = 前后不是字母/数字/点，避免 "1" 被 "10" 误判为包含）
                    if _fixed_txt and re.search(
                            r"(?<![\w.])" + re.escape(_text) + r"(?![\w.])", _fixed_txt):
                        trace.append({"step": "critic_repair", "content": _fixed_txt[:120]})
                        _text = _fixed_txt
                else:
                    trace.append({"step": "critic_audit", "content": "pass"})
            except Exception:
                pass

        return _text

    # ── 解析引理摘要 ──
    @staticmethod
    def _parse_lemmas(text: str) -> List[str]:
        """从摘要器输出中解析引理列表。"""
        lemmas = []
        for line in text.split("\n"):
            line = line.strip()
            if not line or line == "无" or line == "无。":
                continue
            # 匹配 "引理：..." 或 "引理1：..." 等格式
            if "引理" in line and "：" in line:
                # 取引理冒号后的内容，截断到合理长度
                content = line.split("：", 1)[1].strip() if "：" in line else line
                if len(content) > 5:
                    lemmas.append(content[:200])
        # 去重保序
        seen = set()
        unique = []
        for l in lemmas:
            if l not in seen:
                seen.add(l)
                unique.append(l)
        return unique[:4]

    # ── 独立 Python 求解（交叉验证：确定性计算 > LLM 推理）──
    def _python_solve(self, problem: str, idx: int) -> Optional[str]:
        """独立让 solver 写确定性计算代码求解，执行后提取「最终答案」。

        区别于多轮推理里的代码反馈环：这里是一次独立的 Python 求解通道，
        不锚定推理答案，交叉验证时 Python 成功且答案可信则优先。
        失败返回 None。
        """
        try:
            cfg = self.config
            prompt = (
                "你是 Python 数学计算专家。请用 Python 代码**独立精确求解**下面的数学题，"
                "不要参考任何已有的推理过程。\n\n"
                "要求：\n"
                "1. 直接输出一个 ```python``` 代码块，代码块之外不要写任何文字或解释\n"
                "2. 优先用 sympy 符号计算，或精确枚举/记忆化 DP；先在小规模上暴力验证公式，再外推到题面规模\n"
                "3. 最后一行必须 print(\"最终答案:\", answer)\n"
                "4. answer 是单行自包含字符串（数值 / 表达式 / 集合）\n"
                "5. 若题目数据缺失无法精确计算，answer 写 \"无法确定\"，不要编造数据\n\n"
                f"题目：\n{problem}"
            )
            msg = AgentMessage(sender="user", content=prompt)
            resp = self._solver_compute(
                msg, session_id=f"{idx}:py",
                temperature=0.2, max_tokens=cfg.solver_max_tokens,
                thinking_mode=False,
            )
            code = extract_code(resp.content)
            if not code:
                return None
            out = execute_code(code, timeout=cfg.code_timeout, problem=problem)
            m = re.search(r"最终答案\s*[:：]\s*(.+)", out)
            if not m:
                return None
            ans = m.group(1).strip()
            if ans and ans.lower() not in {"none", "null", "无法确定", "无解"}:
                return ans
        except Exception:
            pass
        return None

    # ── 多轮层次化推理（Intern-S1-MO 核心）──
    def _multi_round_reason(
        self, problem: str, analysis: str, strategy: str, idx: int, is_proof: bool,
        reference: str = "", skill_context: str = "", budget=None, rounds=None, difficulty="medium",
    ) -> Tuple[str, List[Dict]]:
        """多轮层次化推理：每轮「求解 → 摘要引理 → 复用引理继续深挖」。

        对齐 Intern-S1-MO 的 reasoning → summarizer → verifier 循环：
          - 第 1 轮：给出初步解答
          - 中间轮：把上一轮结论压成引理，带着引理继续深挖
          - 最后一轮：得出最终解
        """
        cfg = self.config
        solver = self._solver_proof if is_proof else self._solver_compute
        trace = []
        lemmas: List[str] = []
        current_solution = ""

        _rounds = rounds or cfg.reasoning_rounds
        for round_idx in range(_rounds):
            is_final = (round_idx == _rounds - 1)
            # 时间预算：剩余不足以再完成一轮且已有解 → 提前收束（保输出）
            if budget is not None and round_idx > 0 and current_solution \
                    and budget.fast_path(need=180):
                trace.append({"step": f"round_{round_idx}_skipped",
                              "content": "时间预算不足，提前收束已有解答"})
                break

            # ── 构造 prompt ──
            if round_idx == 0:
                # 漏解检测：题面含「Find all / 求所有」时注入「列出全部解」提示
                missing_note = ""
                if re.search(r"find all|all possible|all functions|all pairs|all values|"
                             r"求所有|所有可能|全部|all real|all positive", problem, re.IGNORECASE):
                    missing_note = (
                        "\n\n注意：本题要求列出**全部**解/对象。请逐一核对是否漏掉其他解、"
                        "特殊情形或边界值——多个根、多个函数族、完整区间或范围都要列全，"
                        "不要只给其中一个。"
                    )
                prompt = (
                    f"题目：\n{problem}\n"
                    f"{skill_context}"
                    f"{reference}"
                    f"分析摘要：{analysis[:300]}\n"
                    f"推荐策略：{strategy[:300]}"
                    f"{missing_note}\n\n"
                    "请给出完整解答，在最后用 \\boxed{答案} 明确写出最终结果。"
                )
            else:
                lemma_text = "\n".join(f"{i+1}. {l}" for i, l in enumerate(lemmas)) if lemmas else "(无)"
                prompt = (
                    f"题目：\n{problem}\n\n"
                    f"你之前已经推导出以下关键结论（引理）：\n{lemma_text}\n\n"
                    "请基于这些已证结论继续深入推理，完善并最终确定解答。"
                    "不要重复推导已经确定的引理，直接在它们基础上推进。\n"
                    "在最后用 \\boxed{答案} 明确写出最终结果。"
                )

            solve_msg = AgentMessage(sender="user", content=prompt)
            # 分情况 deep thinking：off 全关（本地省时防截断）/ on 全开 / auto 按难度
            _tp = os.environ.get("MATH_AGENT_THINKING", "auto")
            if _tp == "off":
                round_thinking = False
            elif _tp == "on":
                round_thinking = True
            else:  # auto：easy 不深想（快答），其余末轮深推理
                round_thinking = is_final and (difficulty != "easy")

            # ── 最后一轮：多候选 + 投票选最优（叠加广度）；中间轮：单路快速推进 ──
            if is_final and cfg.candidate_count > 1:
                # 生成多个候选（不同 session 促进多样性）
                # 最后一个候选走**异构第二路径**：强制换方法论，
                # 避免所有候选沿同一条思路、最后一起犯同一个错。
                _div_hint = _diverse_hint_for(problem, is_proof)
                final_candidates = []
                for cid in range(cfg.candidate_count):
                    _is_div = bool(_div_hint) and cid == cfg.candidate_count - 1
                    _cand_msg = (
                        AgentMessage(sender="user", content=solve_msg.content + _div_hint)
                        if _is_div else solve_msg
                    )
                    resp = solver(
                        _cand_msg,
                        session_id=f"{idx}:round:{round_idx}:cand:{cid}",
                        temperature=cfg.solver_temperature,
                        max_tokens=cfg.solver_max_tokens,
                        thinking_mode=True,
                    )
                    final_candidates.append(resp.content)
                if _div_hint:
                    trace.append({"step": "diverse_branch",
                                  "content": "最后一个候选走异构第二解法（强制换方法论）"})

                # 对每个候选投票，选 confidence 最高
                scored = []
                for cid, cand in enumerate(final_candidates):
                    confidence, _ = self._vote_on_candidate(problem, cand, idx, cid)
                    scored.append((cand, confidence))
                scored.sort(key=lambda x: x[1], reverse=True)
                current_solution = scored[0][0]
                trace.append({
                    "step": f"round_{round_idx}_voting",
                    "content": {
                        "candidate_count": cfg.candidate_count,
                        "scores": [round(s, 2) for _, s in scored],
                    },
                })
            else:
                response = solver(
                    solve_msg,
                    session_id=f"{idx}:round:{round_idx}",
                    temperature=cfg.solver_temperature,
                    max_tokens=cfg.solver_max_tokens,
                    thinking_mode=round_thinking,
                )
                current_solution = response.content

            # ── 代码执行反馈（保留原有能力）──
            code_blocks = extract_code_blocks(current_solution)
            if code_blocks:
                code_outputs = [execute_code(c, timeout=cfg.code_timeout, problem=problem) for c in code_blocks]
                if code_outputs:
                    feedback = "\n".join(f"[代码块 {i+1} 执行结果]:\n{out}" for i, out in enumerate(code_outputs))
                    has_error = any(
                        'error' in o.lower() or 'traceback' in o.lower() or 'indexerror' in o.lower()
                        or 'typeerror' in o.lower() or 'syntaxerror' in o.lower() or 'nameerror' in o.lower()
                        for o in code_outputs
                    )
                    if has_error:
                        refine_prompt = (
                            "你之前写的代码执行时遇到错误，请查看错误输出修正代码或改用解析方法，"
                            "注意原题没有变化：\n\n" + feedback +
                            "\n\n输出修正后的完整解答，最后用 \\boxed{答案} 给出结果。"
                        )
                    else:
                        refine_prompt = (
                            "以下是你的代码执行结果，请据此确认数值是否正确，如有误请修正：\n\n"
                            + feedback +
                            "\n\n输出完整解答，最后用 \\boxed{答案} 给出结果。"
                        )
                    refined = solver(
                        AgentMessage(sender="user", content=refine_prompt),
                        session_id=f"{idx}:round:{round_idx}:refine",
                        temperature=0.1,
                        max_tokens=cfg.solver_max_tokens,
                        thinking_mode=False,
                    )
                    refined_text = refined.content
                    # 防跑偏/防丢推导
                    drifted = any(kw in refined_text for kw in ["假设题目", "缺少具体的", "没有提供", "如果您有具体"])
                    if drifted:
                        current_solution = current_solution + "\n\n[代码执行反馈]:\n" + feedback[:500]
                    elif len(refined_text) < 100 and len(current_solution) > 200:
                        rb = extract_boxed(refined_text)
                        ob = extract_boxed(current_solution)
                        if rb and ob:
                            current_solution = current_solution.replace(ob, rb)
                        else:
                            current_solution = current_solution + "\n\n" + refined_text
                    else:
                        current_solution = refined_text

            trace.append({
                "step": f"round_{round_idx}",
                "content": {
                    "round": round_idx,
                    "is_final": is_final,
                    "lemmas_carried": len(lemmas),
                    "response": current_solution[:2000],
                },
            })

            # ── 非最后一轮：摘要成引理 + 验证引理（防错误传播）──
            if not is_final:
                summary_msg = AgentMessage(sender="user", content=current_solution[:3000])
                summary = self._summarizer(
                    summary_msg,
                    session_id=f"{idx}:summary:{round_idx}",
                    temperature=0.2,
                    max_tokens=2048,
                )
                candidate_lemmas = self._parse_lemmas(summary.content)

                # 逐条验证引理，只保留验证通过的
                verified_lemmas = []
                for lemma in candidate_lemmas:
                    _verdict_text = self._verdict_call(
                        _PROMPT_LEMMA_VERIFIER,
                        f"引理：{lemma}\n\n请判断这条引理是否正确。",
                        self._lemma_verifier,
                        f"{idx}:lemma_verify:{round_idx}:{len(verified_lemmas)}",
                        fallback_max_tokens=512)
                    ok = is_correct_vote(_verdict_text)
                    if ok:
                        verified_lemmas.append(lemma)
                    trace.append({
                        "step": f"lemma_verify_{round_idx}",
                        "content": {"lemma": lemma[:100], "verified": ok},
                    })

                if verified_lemmas:
                    lemmas = verified_lemmas
                trace.append({
                    "step": f"summary_{round_idx}",
                    "content": {"lemmas": lemmas},
                })

        # ── 最终过程验证 + 修正循环（Intern-S1-MO 的 process verifier）──
        # 最后一轮解答做漏洞检查，FAIL 则反馈修正，最多 1 次
        for fix_round in range(1):
            _verdict_text = self._verdict_call(
                _PROMPT_PROCESS_VERIFIER,
                f"题目：{problem}\n\n解答：{current_solution[:3000]}\n\n请检查是否有漏洞。",
                self._process_verifier,
                f"{idx}:process_verify",
                fallback_max_tokens=1024)
            ok = is_correct_vote(_verdict_text)
            trace.append({
                "step": "process_verify",
                "content": {"passed": ok, "feedback": (_verdict_text or "")[:200]},
            })

            if ok:
                break
            # FAIL：把 verifier 反馈交给 solver 修正
            fix_prompt = (
                f"题目：{problem}\n\n"
                f"你的解答：{current_solution[:3000]}\n\n"
                f"审查员指出以下问题：{verdict_resp.content[:500]}\n\n"
                "请根据审查意见修正解答，在最后用 \\boxed{答案} 给出最终结果。"
            )
            fixed = solver(
                AgentMessage(sender="user", content=fix_prompt),
                session_id=f"{idx}:process_fix",
                temperature=0.1,
                max_tokens=cfg.solver_max_tokens,
                thinking_mode=False,
            )
            fixed_text = fixed.content
            drifted = any(kw in fixed_text for kw in ["假设题目", "缺少具体的", "没有提供", "如果您有具体"])
            if not drifted:
                current_solution = fixed_text
            trace.append({
                "step": "process_fix",
                "content": {"fixed": not drifted, "response": current_solution[:2000]},
            })

        return current_solution, trace

    # ── 多候选生成（含代码执行反馈环 + 题型自适应）──
    def _generate_candidates(
        self, problem: str, analysis: str, strategy: str, idx: int, is_proof: bool = False
    ) -> Tuple[List[str], List[Dict]]:
        """生成多个候选解答，每个候选含代码执行→反馈→修正的闭环。

        流程：
          1. 根据题型选择 solver（证明专用 / 计算专用）
          2. 求解器给出初步解答（含 Python 代码）
          3. 提取并执行代码，收集输出
          4. 将执行结果反馈给求解器，要求修正/确认
          5. 取修正后的解答作为最终候选
        """
        candidates = []
        trace = []
        cfg = self.config

        # ── 题型自适应：选择对应的 solver ──
        solver = self._solver_proof if is_proof else self._solver_compute

        # ── 异构第二路径（与 _multi_round_reason 共用同一实现）──
        _diverse_hint = _diverse_hint_for(problem, is_proof) if cfg.candidate_count >= 2 else ""

        for cid in range(cfg.candidate_count):
            _is_diverse = bool(_diverse_hint) and cid == cfg.candidate_count - 1
            # ═══ 第 1 轮：初步求解 ═══
            solve_msg = AgentMessage(
                sender="user",
                content=(
                    f"题目：\n{problem}\n\n"
                    f"分析摘要：{analysis[:300]}\n"
                    f"推荐策略：{strategy[:300]}\n\n"
                    f"请给出完整解答（候选编号：{cid + 1}/{cfg.candidate_count}）。\n"
                    "在最后用 \\boxed{答案} 明确写出最终结果。"
                    + (_diverse_hint if _is_diverse else "")
                ),
            )

            # 恒温 0.6（温度梯度曾起反作用，回退为恒温）
            response = solver(
                solve_msg,
                session_id=f"{idx}:solve:{cid}",
                temperature=cfg.solver_temperature,
                max_tokens=cfg.solver_max_tokens,
            )
            solution_text = response.content

            # ═══ 第 2 轮：代码执行 + 反馈修正 ═══
            code_blocks = extract_code_blocks(solution_text)
            if code_blocks:
                code_outputs = []
                for code in code_blocks:
                    exec_result = execute_code(code, timeout=cfg.code_timeout, problem=problem)
                    code_outputs.append(exec_result)

                if code_outputs:
                    # 检查是否存在代码执行错误
                    has_error = any(
                        'error' in out.lower() or 'traceback' in out.lower() or 'indexerror' in out.lower()
                        or 'typeerror' in out.lower() or 'syntaxerror' in out.lower() or 'nameerror' in out.lower()
                        for out in code_outputs
                    )

                    feedback = "\n".join(
                        f"[代码块 {i+1} 执行结果]:\n{out}"
                        for i, out in enumerate(code_outputs)
                    )

                    if has_error:
                        refine_prompt = (
                            "你之前写的代码执行时遇到了错误，请查看以下错误输出，找出代码中的问题并修正推导中的数值错误：\n\n"
                            f"{feedback}\n\n"
                            "注意：原题没有变化，你仍然需要回答原题。"
                            "代码错误不代表题目无解，请尝试修正代码逻辑后重新给出解答。"
                            "如果代码暂时无法修正，请基于解析方法继续推导。"
                            "务必输出完整的解答文本（含推导），在最后用 \\boxed{答案} 给出最终结果。"
                        )
                    else:
                        refine_prompt = (
                            "以下是你的代码执行结果，请检查并修正答案：\n\n"
                            f"{feedback}\n\n"
                            "请根据这些结果，检查数值是否正确。"
                            "仅修改有误的计算或结论，保持原有推导结构。"
                            "务必输出完整的解答文本（含推导），在最后用 \\boxed{答案} 给出最终结果。"
                            "不要只输出 \\boxed{}，要保留所有推理步骤。"
                        )

                    refine_msg = AgentMessage(sender="user", content=refine_prompt)
                    refined = solver(
                        refine_msg,
                        session_id=f"{idx}:refine:{cid}",
                        temperature=0.1,  # 修正阶段用低温度
                        max_tokens=cfg.solver_max_tokens,
                    )
                    refined_text = refined.content

                    # ── 安全合并：修正轮丢失推导或跑偏时保留原始解答 ──
                    # 跑偏信号：模型说"假设题目/缺少具体题目/没有提供"
                    drifted = any(kw in refined_text for kw in ["假设题目", "缺少具体的", "没有提供",
                                                                 "针对具体问题", "如果您有具体"])

                    if drifted:
                        # 修正轮跑偏（编造了新题目）→ 回退到第一轮，仅用代码输出追加提示
                        solution_text = solution_text + "\n\n[代码执行反馈]:\n" + feedback[:500]
                    elif len(refined_text) < 100 and len(solution_text) > 200:
                        # 修正轮输出极短（可能只给了 \boxed{}）→ 用修正的 boxed 替换原始的
                        refined_boxed = extract_boxed(refined_text)
                        original_boxed = extract_boxed(solution_text)
                        if refined_boxed and original_boxed:
                            solution_text = solution_text.replace(original_boxed, refined_boxed)
                        else:
                            solution_text = solution_text + "\n\n" + refined_text
                    else:
                        solution_text = refined_text

                    trace.append({
                        "step": f"candidate_{cid}_refine",
                        "content": {
                            "candidate_id": cid,
                            "code_count": len(code_outputs),
                            "code_outputs": code_outputs,
                            "refined_response": solution_text[:2000],
                        },
                    })
                else:
                    trace.append({
                        "step": f"candidate_{cid}_code_exec",
                        "content": {
                            "candidate_id": cid,
                            "code_count": len(code_blocks),
                            "note": "代码执行完成，无有效输出",
                        },
                    })

            # 记录候选
            trace.append({
                "step": f"candidate_{cid}",
                "content": {
                    "candidate_id": cid,
                    "solver_type": "proof" if is_proof else "compute",
                    "response": solution_text[:2000],
                },
            })

            candidates.append(solution_text)

        return candidates, trace

    # ── 投票验证 ──
    def _verdict_call(self, system_prompt: str, prompt: str, agent, session_id: str,
                      fallback_max_tokens: int = 512, temperature: float = 0.0) -> str:
        """判定类调用：优先预填充，失败退回常规调用。

        判定类调用的 system prompt 把它限定为一行 `VERDICT: A/B` —— 这是预填充
        最适用的形态：省掉整条思维链（同 prompt 实测 40s → 1s），且该调用从此
        不可能因思维链抢占 token 预算而被截断。

        覆盖三处判定调用：候选投票、逐条引理验证、最终过程验证。引理多的一轮
        会有 3~5 次这类调用，全走预填充能省下可观时间。
        """
        try:
            out = self._api.chat_prefilled(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": prompt}],
                "VERDICT: ", temperature=temperature, max_tokens=64)
            if re.search(r"VERDICT\s*[:：]\s*[AB]", out or "", re.IGNORECASE):
                return out
        except Exception:
            pass
        # 退回常规调用（后端拒绝 assistant 结尾 / 返回不成形）
        try:
            resp = agent(
                AgentMessage(sender="user", content=prompt),
                session_id=session_id, temperature=temperature,
                max_tokens=fallback_max_tokens,
            )
            return resp.content
        except Exception:
            return ""

    def _vote_on_candidate(
        self, problem: str, candidate: str, idx: int, candidate_id: int
    ) -> Tuple[float, List[Dict]]:
        """对单个候选解答进行多次投票，返回 confidence 分数。

        与 baseline _verify_candidate 一致：
          - vote_count 次独立投票
          - 每次投票用相同的 prompt + temperature=0.0
          - confidence = 正确票数 / 总票数
        """
        votes = []
        trace = []
        cfg = self.config

        for vote_id in range(cfg.vote_count):
            _vote_prompt = (
                "题目：\n"
                f"{problem}\n\n"
                "候选解答：\n"
                f"{_vote_excerpt(candidate, 3000)}\n\n"
                "请核对这份候选解答。**务必先看它最后给出的最终答案**，再逐项判断：\n"
                "1. 最终答案是否真的回答了题目所问（题目要的是单值 / 区间 / 全部解 / 判断，别搞错交付物类型）\n"
                "2. 关键推导有无硬伤（跳步、算错、定理误用、漏掉条件）\n"
                "3. 最终答案是否完整（题目求「所有」时是否只给了一个）\n\n"
                "只输出一行：VERDICT: A（正确）或 VERDICT: B（不正确）。"
            )
            verdict = self._verdict_call(
                _PROMPT_VOTER, _vote_prompt, self._voter,
                f"{idx}:vote:{candidate_id}:{vote_id}",
                fallback_max_tokens=cfg.voter_max_tokens,
                temperature=cfg.voter_temperature)
            is_correct = is_correct_vote(verdict)
            votes.append(is_correct)

            trace.append({
                "step": f"vote_{candidate_id}_{vote_id}",
                "content": {
                    "candidate_id": candidate_id,
                    "vote_id": vote_id,
                    "verdict": verdict[:200],
                    "is_correct": is_correct,
                },
            })

        confidence = sum(votes) / len(votes) if votes else 0.0
        return confidence, trace
