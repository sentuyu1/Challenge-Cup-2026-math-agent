"""answer_clean.py — 判分保护：答案干净化（移植自 ICMA 的判分保护机制）。

官方 judge 只认 final_response 里的答案，且要「清晰可独立判分」。故：
  - 剥掉「最终答案：/结论：」标签包装
  - 检测「无法确定」这类声明式失败（必判 0 分）
  - 剥离思维流尾巴 / 口癖（"1/2 works." → "1/2"）
纯规则，零 LLM 成本。
"""

from __future__ import annotations

import re

# 「无法确定」声明式非答案：这类文本满足非空，却必判 0。
_NO_ANSWER_DECLARATION_RE = re.compile(
    r"^(?:无法(?:确定|给出|得出|求出|算出|计算|判断|完成|回答)|"
    r"暂(?:时)?无法\S{0,6}|不能确定|尚(?:不|未)能?确定|未能(?:得出|求出|给出)|"
    r"没有(?:得到|求出|给出)\S{0,6}|无(?:法|从)\S{0,6})"
    r"[^\n]{0,12}[。．.！!]?$"
)

# 答案行最前端的标签包装（"最终答案：1" / "结论：x"）
_ANSWER_LABEL_RE = re.compile(r"^\s*(?:最终答案|结论)\s*[：:]\s*")

# 占位/无效答案
_PLACEHOLDERS = {"", "见解答", "未能提取答案", "无法生成", "无法生成完整答案", "无解"}


def strip_answer_label(text: str) -> str:
    """去掉答案文本最前端的标签包装；非标签开头原样返回。"""
    return _ANSWER_LABEL_RE.sub("", text or "", count=1).strip()


def declares_no_answer(text: str) -> bool:
    """答案是否是"无法确定"这类声明式失败。"""
    return bool(_NO_ANSWER_DECLARATION_RE.match((text or "").strip()))


def is_placeholder_answer(text: str) -> bool:
    """占位 / 空 / 无效答案。"""
    t = (text or "").strip()
    return not t or t in _PLACEHOLDERS


def clean_noise_head(text: str) -> str:
    """噪声答案行截取句首的干净结论头（剥离思维流尾巴与口癖）。

    例："1/2 works." → "1/2"；"3/4. Do we have 5/6 or 3/4?" → "3/4"
    """
    t = (text or "").strip()
    if not t:
        return t
    # 口癖剥离："1/2 works." / "x holds"（先去掉末尾标点再匹配）
    t = re.sub(
        r"(?i)\s+(?:works?|holds?|fails?|seems|is\s+possible|is\s+enough|suffices)\s*[.。!！]?\s*$",
        "", t,
    ).strip()
    # 思维流尾巴：取第一个完整句子
    head = re.split(r"(?<=[.。!?！？])\s+", t, maxsplit=1)[0].strip().rstrip("。.")
    if head and re.search(r"[\dA-Za-z\\一-鿿]", head):
        return head
    return t


def clean_answer(text: str) -> str:
    """答案干净化：剥标签 → 检测失败声明/占位 → 去噪声头。

    返回干净答案；若答案是「无法确定」/占位/噪声，返回空串（触发上游兜底）。
    """
    t = strip_answer_label(text or "")
    if declares_no_answer(t):
        return ""
    if is_placeholder_answer(t):
        return ""
    return clean_noise_head(t)
