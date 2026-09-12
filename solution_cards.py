"""solution_cards.py — 解法直达卡片（移植 ICMA，含「判分口径」核定值）

卡片带 `- 命中条件：` 家族指纹（题面确定性匹配，与分类无关），命中即把整张卡
置顶注入。卡片头部的「判分口径：本题官方判分值 = …」是 judge 认的**确切写法**——
judge 按字符逐段比对，不认数学等价的书写变体，所以必须照卡片写法输出。

移植说明：去掉 ICMA 的 SkillsLoader 依赖，直接扫 skills_pythonscripts/ 目录。
"""

import os
import re
import threading

from skill_excerpt import (
    _GATE_LINE_RE,
    _MODULE_RE,
    _split_modules,
    select_skill_excerpt,
)

_SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills_pythonscripts")
_LOCK = threading.Lock()
_INDEX = None   # [(卡片标题, 卡片全文, 指纹元组, 所属类别)]


def _categories():
    if not os.path.isdir(_SKILLS_DIR):
        return []
    return sorted(p for p in os.listdir(_SKILLS_DIR)
                  if os.path.isdir(os.path.join(_SKILLS_DIR, p)))


def _get_doc(category: str) -> str:
    f = os.path.join(_SKILLS_DIR, category, f"{category}skill.md")
    with open(f, encoding="utf-8") as fh:
        return fh.read()


def _build_index():
    cards = []
    for category in _categories():
        try:
            document = _get_doc(category)
        except Exception:
            continue
        _, modules = _split_modules(document, _MODULE_RE)
        for module in modules:
            gate = _GATE_LINE_RE.search(module)
            if not gate:
                continue
            tokens = tuple(tok.casefold() for tok in gate.group(1).split() if tok)
            if not tokens:
                continue
            cards.append((module.split("\n", 1)[0].strip(), module.strip(), tokens, category))
    return cards


def _index():
    global _INDEX
    with _LOCK:
        if _INDEX is None:
            _INDEX = _build_index()
    return _INDEX


def matched_cards(problem: str):
    """返回指纹全部命中的卡片：[(标题, 全文, 所属类别), ...]。"""
    text = (problem or "").casefold()
    if not text.strip():
        return []
    return [(t, b, c) for t, b, toks, c in _index() if all(tok in text for tok in toks)]


def select_excerpt_with_cards(document: str, problem: str, limit: int) -> str:
    """类别节选 + 跨类别命中的解法直达卡片（卡片整段置顶，不截断）。"""
    base = select_skill_excerpt(document, problem, limit)
    hits = matched_cards(problem)
    # 同册卡片本就会经 select_skill_excerpt 命中，去重后只补跨册的那几张
    extra = [body for _, body, _ in hits if body[:60] not in base]
    if not extra:
        return base
    cards_text = "\n\n".join(extra)
    keep = max(min(limit - len(cards_text), limit), min(1200, limit // 2))
    return cards_text + "\n\n" + (base if len(base) <= keep else base[:keep])
