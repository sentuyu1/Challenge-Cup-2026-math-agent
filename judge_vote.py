"""judge_vote.py — 判断题第二票（对抗系统性「否」偏向）

════════════════════════════════════════════════════════
  判断题 + 答案是判断词
        │
   ┌────▼─────────────┐
   │ 温度 0 独立再问一次 │  提示词强调"不要受既有结论影响"
   └────┬─────────────┘
        │
   ┌────▼──────┐
   │ 与首票一致？│
   └──┬─────┬──┘
      │是    │否
      ▼      ▼
    维持   再解一次取第三票 → 少数服从多数
════════════════════════════════════════════════════════

为什么需要：
  模型对「是否/能否/可否」这类问句存在**系统性的方向偏好**——倾向于回答"否"。
  单轮判断在该方向上不可靠，而这类题一旦判反就是 0 分（不存在部分分）。
  独立重采样两次、必要时取第三票，能显著压低方向性错误。

成本：一次温度 0 的小额调用（约 2048 token）；仅判断题触发，不干扰其他题型。
"""

from __future__ import annotations

import re

#: 题面是判断题的信号
_JUDGE_Q_RE = re.compile(
    r"是否|能否|可否|对不对|是否正确|成立吗|真伪|判断.{0,6}(?:对错|真假|正误)|"
    r"true\s+or\s+false|is\s+it\s+true",
    re.IGNORECASE,
)

#: 合法判断词（可归一化为 是 / 否）
_TRUE_WORDS = {"是", "成立", "对", "正确", "能", "可以", "真", "true", "yes", "存在", "有"}
_FALSE_WORDS = {"否", "不成立", "错", "错误", "不能", "不可以", "假", "false", "no", "不存在", "没有"}

#: 从模型输出里抓「结论:是 / 结论:否」
_CONCLUSION_RE = re.compile(r"结论\s*[:：]\s*(是|否|成立|不成立|对|错|正确|错误|能|不能|可以|不可以)")


def normalize_judge_word(text: str):
    """把判断性文字归一化为 "是" / "否"；无法判断返回 None。"""
    t = (text or "").strip().lower()
    # 先看有没有显式「结论:」标记
    m = _CONCLUSION_RE.findall(t)
    if m:
        t = m[-1]
    for w in _TRUE_WORDS:
        if t.startswith(w):
            return "是"
    for w in _FALSE_WORDS:
        if t.startswith(w):
            return "否"
    return None


def is_judge_problem(problem: str, answer: str) -> bool:
    """题面是判断题、且当前答案是合法判断词时才需要第二票。"""
    if not _JUDGE_Q_RE.search(problem or ""):
        return False
    return normalize_judge_word(answer) is not None


def _ask_once(api, problem: str, prompt: str, max_tokens: int = 2048):
    """一次独立调用，返回归一化后的判断词；失败返回 None。"""
    try:
        out = api.chat([{"role": "user", "content": prompt}], temperature=0.0, max_tokens=max_tokens)
    except Exception:
        return None
    return normalize_judge_word(out)


def second_vote(problem: str, first_answer: str, api):
    """判断题第二票。

    返回 (最终答案, 是否发生了反转)。
    任何异常都退化为"维持原答案"。
    """
    first = normalize_judge_word(first_answer)
    if first is None:
        return first_answer, False

    second = _ask_once(
        api, problem,
        f"题目：\n{problem}\n\n"
        "请独立判断该命题是否成立。不要受任何既有结论影响，"
        "只依据题面自己重新推导一次。\n"
        "最后一行单独输出：结论:是  或  结论:否",
    )
    if second is None or second == first:
        return first_answer, False

    # 出现分歧 → 再解一次取第三票（多数决）
    third = _ask_once(
        api, problem,
        f"题目：\n{problem}\n\n"
        "请给出你的最终判断，并简要说明理由（不超过 3 行）。\n"
        "最后一行单独输出：结论:是  或  结论:否",
        max_tokens=4096,
    )
    if third is None:
        return first_answer, False          # 拿不到第三票 → 维持原判（不冒险）
    if third == second:
        return ("是" if second == "是" else "否"), True
    return first_answer, False
