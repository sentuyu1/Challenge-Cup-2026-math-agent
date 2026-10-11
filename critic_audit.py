"""critic_audit.py — 交付物契约审计

════════════════════════════════════════════════════════
  题面 ──→ 推断「答案必须交付什么」
              │
      ┌───────▼────────┐
      │ 与当前答案比对   │
      └───┬────────┬───┘
          │齐全     │缺
          ▼         ▼
        放行   定向追问一次（补充式修复）
════════════════════════════════════════════════════════

为什么需要：
  「数学对了，但题目要的东西没给全」是常见的失分形态。最典型的是
  **求所有解却只给了一个**——每一步推导都没错，交付物却不完整。

设计原则（保守）：
  - 只在题面给出**明确信号**时才要求对应成分，避免无谓追问；
  - 修复走**补充式**：只有新答案**完整包含**原答案内容时才采用，
    绝不允许追问把已经正确的答案改坏。
"""

from __future__ import annotations

import re

# ── 成分信号 ──

#: 求全部 / 枚举
_ENUM_ALL_RE = re.compile(
    r"求所有|所有可能|全部可能|求出所有|列出全部|写出全部|列举|哪些|"
    r"find\s+all|all\s+possible|list\s+all|determine\s+all",
    re.IGNORECASE,
)

#: 求最值
_EXTREMUM_RE = re.compile(
    r"最大值|最小值|最大值为|最小值为|最值|maximum|minimum",
    re.IGNORECASE,
)

#: 答案里出现「多项」的迹象（逗号 / 顿号 / 或 / 分号分隔）
_MULTI_SEP_RE = re.compile(r"[,，、;；]|\s+or\s+|或")


def required_components(problem: str) -> list:
    """由题面推断答案必须包含哪些成分。"""
    p = problem or ""
    need = []
    if _ENUM_ALL_RE.search(p):
        need.append("enumerate_all")
    if _EXTREMUM_RE.search(p):
        need.append("extremum_value")
    return need


def _has_multiple_items(answer: str) -> bool:
    a = (answer or "").strip()
    if not a:
        return False
    return bool(_MULTI_SEP_RE.search(a))


def _has_value(answer: str) -> bool:
    """答案里是否有可判读的数值 / 表达式。"""
    a = (answer or "").strip()
    if not a:
        return False
    return bool(re.search(r"\d", a) or re.search(r"\\frac|\^|\\sqrt|\w+\s*=", a))


def missing_components(problem: str, answer: str) -> list:
    """返回答案缺失的成分列表（空列表 = 齐全）。"""
    need = required_components(problem)
    missing = []
    a = answer or ""
    if "enumerate_all" in need and not _has_multiple_items(a):
        missing.append("enumerate_all")
    if "extremum_value" in need and not _has_value(a):
        missing.append("extremum_value")
    return missing


_COMPONENT_HINT = {
    "enumerate_all": "题目要求给出**全部**结果，请核对是否遗漏，逐一列出（用逗号或分号分隔）",
    "extremum_value": "题目问最值，答案里必须出现最值本身（数值或表达式），并注明取到它的点",
}


def audit_prompt(problem: str, answer: str, missing: list) -> str:
    """构造补充式追问提示词。"""
    hints = "\n".join(f"- {_COMPONENT_HINT[m]}" for m in missing if m in _COMPONENT_HINT)
    return (
        f"题目：\n{problem}\n\n"
        f"你给出的答案：\n{answer}\n\n"
        "核对发现以下交付物可能不完整：\n"
        f"{hints}\n\n"
        "请重新完整作答：**保留原有正确内容不变**，只补充遗漏的部分。\n"
        "最后用 \\boxed{答案} 给出完整结果。"
    )
