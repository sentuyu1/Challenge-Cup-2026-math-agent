# -*- coding: utf-8 -*-
"""kg_theorem_extract.py — 论文"定理抽取/匹配"平替：合并正则命中 THEOREM_DATA 定理实体。

对应 AAAI-26 论文 §3.1 基础生成第②步"无约束生成解题过程中调用的定理集合"、
四重验证④"定理匹配"（对照权威定理库）。平替：以 theorem_data.py 的 THEOREM_DATA
（121 条人工校验定理实体）充当"权威定理库"，用 aliases + 中英文名 + keywords
合并构建正则，在题解文本中统计命中，作为"模板↔定理"边的依据。

设计：纯标准库、模块级懒加载、编译一次；异常返回空，绝不抛。
"""
from __future__ import annotations

import os
import re
import sys

__all__ = ["theorems_from_text", "theorem_regex", "THEOREM_LIBRARY_SIZE"]

_THEREG = None
_THE_TID_BY_NAME = {}


def _load() -> None:
    global _THEREG, _THE_TID_BY_NAME
    if _THEREG is not None:
        return
    try:
        # theorem_data 位于 kg_deliver 根目录
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)
        from theorem_data import THEOREM_DATA  # noqa: F401
    except Exception:  # noqa: BLE001
        _THEREG = re.compile(r"(?!)")  # 永不匹配
        _THE_TID_BY_NAME = {}
        return
    # 每个实体合并：别名 + 中英文名 + 关键词（截前 12 个，控正则大小）
    tokens: dict[str, str] = {}  # token(小写) -> tid
    for tid, d in THEOREM_DATA.items():
        names = [d.get("theorem_en", ""), d.get("theorem_cn", "")]
        names += [a for a in (d.get("aliases") or []) if isinstance(a, str)]
        names += [k for k in (d.get("keywords") or []) if isinstance(k, str)][:12]
        for n in names:
            n = (n or "").strip()
            if len(n) >= 2:
                tokens[n.lower()] = tid
    # 长词优先（避免 "Cauchy" 被 "Cauchy-Schwarz" 前缀误伤：先匹配长 token）
    ordered = sorted(tokens.keys(), key=len, reverse=True)
    pat = "|".join(re.escape(t) for t in ordered[:2000])  # 防超长失控
    _THEREG = re.compile(r"(" + pat + r")", re.IGNORECASE)
    _THE_TID_BY_NAME = tokens
    # 预计算 tid 集合规模供统计
    globals()["THEOREM_LIBRARY_SIZE"] = len(THEOREM_DATA)


THEOREM_LIBRARY_SIZE = 0


def theorem_regex():
    """返回合并后的定理匹配正则（懒加载）。"""
    _load()
    return _THEREG


def theorems_from_text(text: str) -> dict[str, int]:
    """在文本中统计命中的定理 tid → 次数。输入为题解/题干全文。"""
    _load()
    if not text:
        return {}
    counts: dict[str, int] = {}
    try:
        for m in _THEREG.finditer(text):
            token = m.group(1).lower()
            tid = _THE_TID_BY_NAME.get(token)
            if tid:
                counts[tid] = counts.get(tid, 0) + 1
    except Exception:  # noqa: BLE001
        return {}
    return counts


if __name__ == "__main__":
    _load()
    print("定理库规模:", THEOREM_LIBRARY_SIZE)
    sample = ("Use Cauchy-Schwarz inequality and Fermat's little theorem to solve "
              "the congruence, then apply the Chinese remainder theorem.")
    hit = theorems_from_text(sample)
    print("样例命中:", {k: v for k, v in sorted(hit.items())})
