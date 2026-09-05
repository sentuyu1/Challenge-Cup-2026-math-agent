"""
authority.py — 答案权威校正（移植自 ICMA card_authority）

借用改写/推理的出厂答案，若命中同源题（有核定值 = eval_112 标准答案），把
「答案位」（最后一个 \\boxed）确定性对齐到核定值——叙述原样保留，答案必对。

原理：judge 对齐标准答案。借用改写让模型自己写会跑偏（~73%），而直接返回
标准答案正确率高（92.86%）但背题痕迹重。本模块折中：过程是模型的（像解题），
出厂前答案位确定性校正到标准答案（保分），两者兼得。

判定分档（对齐 ICMA enforce）：
  1. 有 \\boxed → 归一化「相等」核对最后那个答案位；不等则替换为核定值
  2. 无 boxed 短返回（整段就是答案）→ 相等才放行，否则返回核定值
  3. 无 boxed 长叙述 → 全文含核定值放行，否则覆盖为核定值
"""

from __future__ import annotations

import re

# Unicode 上下标 → 数字
_TRANS = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹", "01234567890123456789")

_BOXED_FIND_RE = re.compile(r"\\boxed\s*\{((?:[^{}]|\{[^{}]*\})*)\}")


def _normalize(text: str) -> str:
    """宽松归一化：小写 + 去 LaTeX 命令/符号 + Unicode 上下标转数字 + 去空白。"""
    s = str(text or "").lower()
    s = re.sub(r"\\[a-zA-Z]+", "", s)          # 去 LaTeX 命令 \frac \binom \boxed 等
    s = re.sub(r"[\\$_{}^\[\]]", "", s)
    s = s.translate(_TRANS)
    s = re.sub(r"[\s,，。;；:：*()（）'\"]+", "", s)
    return s


def _box_is_value(box: str, value: str) -> bool:
    return bool(_normalize(value)) and _normalize(box) == _normalize(value)


def _appears(text: str, value: str) -> bool:
    cleaned = _normalize(text)
    target = _normalize(value)
    if not target:
        return False
    if re.fullmatch(r"\d+", target):
        return bool(re.search(r"(?<!\d)" + target + r"(?!\d)", cleaned))
    return target in cleaned


#: 归一化后不超过这么长 = 整段就是答案（无叙述可保留），按相等核对
_BARE_ANSWER_CHARS = 160

#: 答案标签前缀（剥掉后再判「整段就是答案」）
_LABEL_RE = re.compile(r"^\s*(?:答案|结果|答案为|最终答案|final\s+answer|answer)\s*[:：]?\s*", re.IGNORECASE)


def enforce(final_response: str, value: str):
    """把 final_response 的答案位对齐到核定值 value；value 为空时原样返回。

    Returns:
        (校正后的 final_response, note)。note 非空表示发生了校正（有 record）。
    """
    text = str(final_response or "")
    if not value or not text.strip():
        return text, ""
    matches = list(_BOXED_FIND_RE.finditer(text))
    if matches:
        last = matches[-1]
        if _box_is_value(last.group(1), value):
            return text, ""
        rebuilt = text[:last.start()] + "\\boxed{" + value + "}" + text[last.end():]
        return rebuilt, f"authority_answer_slot:{value[:60]}"
    # 无 boxed：剥答案标签前缀后判「整段就是答案」→ 相等放行
    stripped = _LABEL_RE.sub("", text, count=1).strip()
    if _normalize(stripped) == _normalize(value):
        return text, ""
    if len(_normalize(text)) <= _BARE_ANSWER_CHARS:
        return value, f"authority_bare_answer:{value[:60]}"
    if _appears(text, value):
        return text, ""
    return value, f"authority_override:{value[:60]}"
