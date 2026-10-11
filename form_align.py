"""form_align.py — 题面期望答案形态对齐

════════════════════════════════════════════════════════
  题面 ──→ 期望形态（判断 / 单值 / 区间 / 枚举）
                │
          ┌─────▼──────┐
          │ 答案形态匹配？│
          └──┬──────┬───┘
            │是     │否
            ▼       ▼
          放行   一次低成本重述
                （温度 0，只吐"符合题面要求的最终答案本身"）
════════════════════════════════════════════════════════

为什么需要：
  「数学上算对了，但不是题目要的那个东西」是常见的失分形态。典型例子：
  题面问「置信区间长度的一半」（要的是**半长，一个单值**），模型却完整地给出了
  区间 [a, b]——计算全对，交付物类型错了，判分拿不到分。

设计原则：**保守**。
  只有题面给出**强信号**、且答案形态**明显错配**时才触发重述。
  宁可漏判，不可误伤——无谓重述会白烧一次模型调用，还可能把对的答案改坏。
"""

from __future__ import annotations

import re

# ── 题面形态信号 ──

#: 判断题：问"是否/能否/对不对"
_JUDGE_RE = re.compile(
    r"是否|能否|可否|对不对|是否正确|成立吗|真伪|判断.{0,6}(?:对错|真假|正误)|"
    r"true\s+or\s+false|is\s+it\s+true",
    re.IGNORECASE,
)

#: 区间题
_INTERVAL_RE = re.compile(r"置信区间|区间|取值范围|范围|interval|range", re.IGNORECASE)

#: 强单值信号（明确问"某一个数"，不是区间）
#: 注意：不收录「是多少 / 为多少」这类泛问法——它们既可问单值也可问区间，
#: 收进来会把「θ 的 95% 置信区间是多少？」误判成单值题。只收**指标明确**的词。
_SINGLE_STRONG_RE = re.compile(
    r"区间.{0,4}长度|长度的一半|半长|多少长|"
    r"最大值|最小值|最大值为|最小值为|"
    r"的概率|概率为|期望为|期望是|方差为|方差是|标准差|"
    r"多少个|多少种|几种",
    re.IGNORECASE,
)

#: 枚举题
_ENUM_RE = re.compile(
    r"求所有|所有可能|全部可能|写出全部|列举|哪些|"
    r"find\s+all|all\s+possible|list\s+all|enumerate",
    re.IGNORECASE,
)

# ── 答案形态特征 ──

#: 看起来像区间：含 [a, b] / (a, b) / a ≤ x ≤ b
_ANS_INTERVAL_RE = re.compile(r"[\[\(]\s*[-+]?[\d.]+\s*,\s*[-+]?[\d.]+\s*[\]\)]")
_ANS_INEQ_RE = re.compile(r"[<>≤≥]\s*[-+]?[\d.]+\s*[<≤]|[-+]?[\d.]+\s*[<≤]\s*\w+\s*[<≤]")

#: 判断词
_TRUE_WORDS = {"是", "成立", "对", "正确", "能", "可以", "真", "true", "yes", "存在"}
_FALSE_WORDS = {"否", "不成立", "错", "错误", "不能", "不可以", "假", "false", "no", "不存在"}


def expected_form(problem: str) -> str:
    """从题面推断期望答案形态：judge | single | interval | enum | unknown。

    优先级：判断 > 单值（强信号）> 区间 > 枚举 > 未知。
    """
    p = problem or ""
    if _JUDGE_RE.search(p):
        return "judge"
    if _SINGLE_STRONG_RE.search(p):
        return "single"
    if _INTERVAL_RE.search(p):
        return "interval"
    if _ENUM_RE.search(p):
        return "enum"
    return "unknown"


def _starts_with_judge_word(answer: str) -> bool:
    a = (answer or "").strip().lower()
    for w in list(_TRUE_WORDS) + list(_FALSE_WORDS):
        if a.startswith(w):
            return True
    return False


def check_form_alignment(problem: str, answer: str):
    """检查答案形态是否匹配题面期望。

    返回 (是否对齐, 期望形态, 说明)。**只在强信号 + 明显错配时判不对齐。**
    """
    form = expected_form(problem)
    a = (answer or "").strip()
    if not a or form == "unknown":
        return True, form, ""

    if form == "judge":
        if not _starts_with_judge_word(a):
            return False, form, "判断题应以「是/否」等判断词开头"
        return True, form, ""

    if form == "single":
        # 强单值题给了区间 → 错配（idx=94 那类：问半长却答区间）
        if _ANS_INTERVAL_RE.search(a) or _ANS_INEQ_RE.search(a):
            return False, form, "题面问单值（长度/最值/概率等），答案却是区间"
        return True, form, ""

    if form == "interval":
        # 区间题既没区间也没任何数值 → 交付物不对
        if not (_ANS_INTERVAL_RE.search(a) or _ANS_INEQ_RE.search(a) or re.search(r"\d", a)):
            return False, form, "题面问区间/范围，答案既无区间也无数值"
        return True, form, ""

    # 枚举题：不主动判错（「所有解」的呈现方式差异太大，误伤成本高）
    return True, form, ""


def reframe_prompt(problem: str, answer: str, form: str) -> str:
    """生成"只改形态、不改数学内容"的重述提示词。"""
    want = {
        "judge": "一个明确的判断（以「是」或「否」开头，可附一句话理由）",
        "single": "一个数值或一个表达式（**不要给区间**）",
        "interval": "一个区间（用 [a, b] 或 (a, b) 形式）或一个数值",
        "enum": "完整的枚举列表（列出全部对象）",
    }.get(form, "题目要求的那个答案本身")

    return (
        f"题目：\n{problem}\n\n"
        f"原始答案：\n{answer}\n\n"
        f"题目要求的交付物是：{want}。\n\n"
        "请只输出**符合题目要求的最终答案本身**，要求：\n"
        "1. 不要改变任何数学内容或数值，只调整呈现形式\n"
        "2. 不要输出解题过程、解释、客套话\n"
        "3. 如果原始答案的数值与题面要求不符，请重新计算后再给出\n"
        "4. 直接给出答案，不要有「答案：」之类的前缀以外的任何内容"
    )
