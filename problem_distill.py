"""
problem_distill.py — 问题蒸馏检索（轻量版，借鉴 AAAI26 Template-Theorems Graph）

洞察：数学题表面表达千差万别，但底层结构/解法策略/所用定理常相同（「结构等价但表达
不同」）。表面词频检索（TF/Jaccard）找不到这类题；先对题目「蒸馏」出结构描述（去掉
具体数值/措辞，保留问题骨架 + 关键数学对象 + 适用方法），再用结构描述检索，能跨表达
找到结构等价的参考题/定理 —— 补足新题泛化能力。

用法（默认关，MATH_AGENT_DISTILL=1 开启）：
    distill_problem(problem, chat_fn)  →  {"domain","structure","key_objects","methods"}
    distill_context(problem, chat_fn)  →  注入用的「结构定位」文本
"""

import json
import os
import re

_DISTILL_PROMPT = (
    "你是数学问题结构分析师。请对下面的数学题做「问题蒸馏」——抽象出题目结构与解法要点，"
    "**去掉具体数值和表面措辞**，只保留可迁移的结构信息。\n\n"
    "严格输出 JSON（字段值用**英文**，便于跨语言检索；不要多余文字）：\n"
    '{"domain": "math field (combinatorics/number theory/games/geometry/analysis/...)", '
    '"structure": "one-sentence problem structure (replace numbers with N/M/k symbols)", '
    '"key_objects": ["key mathematical objects", "..."], '
    '"methods": ["applicable methods/theorems", "..."]}\n\n'
    "题目：\n{problem}"
)


def _parse_json(text):
    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def distill_problem(problem: str, chat_fn):
    """用 LLM 蒸馏题目结构；chat_fn(prompt) -> str。失败返回 None。"""
    try:
        resp = chat_fn(_DISTILL_PROMPT.replace("{problem}", problem[:2000]))
        return _parse_json(resp)
    except Exception:
        return None


def distill_context(problem: str, chat_fn) -> str:
    """蒸馏 → 结构定位文本（供注入）。失败/未开启返回空串。"""
    if os.environ.get("MATH_AGENT_DISTILL", "0") != "1":
        return ""
    d = distill_problem(problem, chat_fn)
    if not d:
        return ""
    parts = []
    if d.get("domain"):
        parts.append(f"领域：{d['domain']}")
    if d.get("structure"):
        parts.append(f"结构：{d['structure']}")
    if d.get("key_objects"):
        parts.append("关键对象：" + "、".join(str(x) for x in d["key_objects"][:6]))
    if d.get("methods"):
        parts.append("适用方法/定理：" + "、".join(str(x) for x in d["methods"][:6]))
    if not parts:
        return ""
    return "【问题结构蒸馏】" + "；".join(parts) + "\n（提示：上述结构可用于定位同类题的解法模板与定理）"
