"""Select the parts of a skill document that match the problem, not just its head.

The agent nodes cap the skill document at a few thousand characters
(`skill_document[:3000]` in the reasoning branch). That cap is positional, so a
document longer than the cap silently delivers only its opening modules regardless
of what the problem is about.

This became a real defect when 非基础及进阶课程 grew from 7.9k to 8.9k characters:
its number-theory and game-theory modules sit at offsets 3404-8949, entirely past
the 3000-character window, so a game-theory problem received modules on Lebesgue
measure and functional analysis and none of the material written for it.

Selection is by `## 模块` heading, scored on term overlap with the problem
statement. The document's own leading preamble is always kept, and the remaining
budget goes to the best-matching modules in document order. When nothing matches,
the behaviour degrades to the old head-truncation, so a document without module
headings is unaffected.
"""

from __future__ import annotations

import re

#: Module boundary in these documents: the legacy ``## 模块...``/``### 模块...``
#: heading, the numbered ``## 1. ...`` style, or the CJK-numbered ``## 一、...``
#: style used by the core-theory chapters of several manuals.
#:
#: 2026-08-20：漏掉中文序号是一个静默的大洞。高等代数的 ``## 一、多项式理论`` …
#: ``## 十、习题索引`` 十个正文章节都不算边界，于是整册 60% 的正文（15292/25101
#: 字符）全被并进 preamble；preamble 超预算后走头部封顶分支，正文永远只露出开头
#: 1200 字符，真正对口的章节一个字也到不了模型手里。数学分析同理（52%）。
#: idx 6/7/17（高等代数）与 8/27（数学分析）正落在这两册里。
#:
#: 2026-08-22：无 API 全量观测发现 8/18 领域文档把模块写成三级标题 ``### 模块N：``
#: （复分析/常微分方程完全不可见，抽象代数/概率论/泛函分析/线性回归/统计推断/
#: 随机过程部分不可见），``##`` 前缀不再匹配，整册退回 doc[:limit] 头部截断。
#: 模块分支放宽为 ``#{2,3}``；数字/中文序号分支保持 ``##`` 不变——``### 1. 题型识别``
#: 这类三级数字子标题不应成为边界（2026-08-22 复分析文档实测）。
#:
#: 同日再补两种变体：微分几何整册用 ``## 1 曲线弧长``（数字+空格+标题，无标点，
#: 20 个知识模块因此全部不可见，preamble 21663 字符）——新增 ``\d+\s+标题``
#: 分支（含 ``## 3 Frenet标架``/``## 19 Gauss-Bonnet定理`` 这类拉丁开头的标题）；
#: 其余 12 个文档文末的 ``## 通用解题方法论``/``## sympy验证技巧``/``## 习题索引``/
#: ``## 常见错误与陷阱``/``## 关键公式速查表``/``## 参考资源`` 等通用章节被并入最后
#: 一个真模块（复分析模块9 因此膨胀到 24201 字符，其词表成为全集、对所有题霸榜），
#: 文档侧已统一改题为 ``## 模块速查：…``（与离散数学/高等代数惯例一致）。
_MODULE_RE = re.compile(
    r"^(?:#{2,3}\s*模块|##\s*(?:\d+\s*[.)、:：-]|\d+\s+(?:[一-鿿]|[A-Za-z])|"
    r"[一二三四五六七八九十百]+\s*[、.)：:-]))",
    re.MULTILINE,
)
#: Trailing sections that apply to every problem regardless of domain.
_UNIVERSAL_HEADING_RE = re.compile(r"^##\s*(?:跨学科|通用|附录)", re.MULTILINE)
#: CJK runs and latin words; single CJK characters are too common to discriminate.
_TERM_RE = re.compile(r"[一-鿿]{2,}|[A-Za-z][A-Za-z\-]{2,}")

#: Topic cues that a module heading alone cannot express. A game-theory problem says
#: 游戏/必胜/策略 and never the word 博弈论, so pure term overlap scored the module that
#: was written for it no higher than an unrelated one. Each entry maps a module-heading
#: keyword to the problem-statement vocabulary that should pull it in.
_TOPIC_CUES = {
    "博弈": ("游戏", "必胜", "策略", "先手", "后手", "轮流", "获胜", "对手", "取石子",
             "双人", "玩家", "甲", "乙",
             # 英文竞赛题面同类线索（term 交集打分吃不到，此处补齐）。
             "game", "player", "players", "opponent", "wins", "winning",
             "turns", "alternately", "strategy"),
    "数论": ("整除", "同余", "素数", "质数", "互素", "模", "gcd", "最大公约", "幂次",
             "正整数", "因子", "倍数",
             # 只收判别力强的英文词——integer/number 之类的泛词会把数论模块
             # 错误地拉进一半的英文题面。
             "prime", "divisible", "divides", "modulo", "coprime"),
}


def _cue_bonus(module: str, problem: str) -> int:
    """Weight a module by domain cues present in the problem statement.

    单模块封顶 9 分：博弈类速查条目共享"博弈"标题，线索加成不封顶时同族条目
    会集体霸榜，把真正对口但标题不带关键词的条目挤出预算（2026-08-09 idx 48）。
    """
    heading = module.split("\n", 1)[0]
    text = (problem or "").casefold()
    bonus = 0
    for key, cues in _TOPIC_CUES.items():
        if key in heading:
            bonus += 3 * sum(1 for cue in cues if cue.casefold() in text)
    return min(bonus, 9)


#: 速查条目携带的显式检索行。中文题面是长 CJK 连续串，_TERM_RE 的"最大连续段"词元
#: 对它几乎必然失配（"概率不超过" ≠ "概率"），所以检索行按**子串**语义单独记分：
#: 行内每个词元（中文或 ≥4 字符拉丁词）在题面中出现即 +2，短拉丁词按词边界匹配。
#: 上限封顶，避免一行通用词把真正的领域模块挤出预算。
_RETRIEVAL_LINE_RE = re.compile(r"^-\s*检索词[：:](.+)$", re.MULTILINE)

#: 检索词行里的虚词一律不计分。这类词在任何英文题面里都存在，一旦混进检索词，
#: 该模块就会对所有英文题目拿满命中分，把真正对口的模块挤掉——2026-08-20 把
#: 「选数禁邻博弈」的检索词误写成自然语言短语（"...to any of those the player has
#: already chosen..."）后，它立刻劫持了 idx 14 这道与博弈毫无关系的分拆题。
#: 护栏放在打分侧而不是靠人写对：检索词行由人手写，迟早会再混进虚词。
_RETRIEVAL_STOPWORDS = frozenset({
    "the", "a", "an", "of", "to", "is", "are", "be", "in", "on", "at", "by",
    "or", "and", "for", "with", "that", "this", "these", "those", "it", "its",
    "as", "if", "then", "than", "so", "such", "any", "all", "each", "every",
    "has", "have", "had", "was", "were", "not", "no", "we", "you", "he", "she",
    "they", "one", "two", "can", "may", "must", "will", "from", "into", "out",
})


def _retrieval_bonus(module: str, problem: str) -> int:
    match = _RETRIEVAL_LINE_RE.search(module)
    if not match:
        return 0
    text = (problem or "").casefold()
    hits = 0
    for token in match.group(1).split():
        tok = token.casefold().strip()
        if len(tok) < 2 or tok in _RETRIEVAL_STOPWORDS:
            continue
        if re.fullmatch(r"[a-z][a-z\-]*", tok):
            if len(tok) >= 4:
                hit = tok in text
            else:
                hit = bool(re.search(rf"(?<![a-z]){re.escape(tok)}(?![a-z])", text))
        else:
            hit = tok in text
        if hit:
            hits += 1
            if hits >= 6:
                break
    # 单词元命中只记 1 分：一个泛词不足以断言主题相关，不得压过正文模块的
    # 实词匹配（同分时文档序在前的正文模块优先）。多词元命中才给满权重。
    return hits if hits < 2 else 2 * hits


def _split_modules(document: str, boundary=_MODULE_RE) -> tuple[str, list[str]]:
    """(preamble, sections). `sections` is empty when no boundary matches."""
    starts = [match.start() for match in boundary.finditer(document)]
    if not starts:
        return document, []
    bounds = starts + [len(document)]
    modules = [document[bounds[i]:bounds[i + 1]] for i in range(len(starts))]
    return document[:starts[0]], modules


def _terms(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TERM_RE.finditer(text or "")}


def _score(module: str, problem_terms: set[str]) -> int:
    """Overlap between a module's vocabulary and the problem's.

    The heading counts double: a module titled 博弈论 is a stronger signal for a game
    problem than one incidental mention of 博弈 deep inside another module.
    """
    heading = module.split("\n", 1)[0]
    module_terms = _terms(module)
    heading_terms = _terms(heading)
    return len(module_terms & problem_terms) + 2 * len(heading_terms & problem_terms)


#: Validation examples are prompt documents despite their historical ``.py`` names.
#: Their knowledge-point headings are the primary boundaries; the old banner form is
#: retained so repositories with older prompt assets still receive useful excerpts.
_SCRIPT_SECTION_RE = re.compile(r"^(?:##\s+|#\s*(?:=====|-----))", re.MULTILINE)


def select_script_excerpt(script: str, problem: str, limit: int) -> str:
    """`select_skill_excerpt` for prompt-style validation references.

    A bare ``[:2000]`` can still hide the relevant knowledge point in a long domain
    prompt, so choose the sections whose vocabulary matches the problem instead.
    """
    return _select(script, problem, limit, _SCRIPT_SECTION_RE)


def select_skill_excerpt(document: str, problem: str, limit: int) -> str:
    """At most `limit` characters of `document`, biased toward `problem`'s topic.

    Falls back to `document[:limit]` when the document has no module structure or
    nothing scores, so this can replace a bare slice without changing that case.
    """
    return _select(document, problem, limit, _MODULE_RE)


def _select(document: str, problem: str, limit: int, boundary) -> str:
    text = document or ""
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text

    preamble, modules = _split_modules(text, boundary)
    if not modules:
        return text[:limit]

    problem_terms = _terms(problem)
    scored = [(index, _score(module, problem_terms) + _cue_bonus(module, problem)
               + _retrieval_bonus(module, problem))
              for index, module in enumerate(modules)]
    if not any(score for _, score in scored):
        return text[:limit]

    # Universal sections (跨学科通用方法论) apply to every problem, so they compete on
    # equal footing rather than being crowded out by domain scoring alone.
    for index, module in enumerate(modules):
        if _UNIVERSAL_HEADING_RE.match(module):
            scored[index] = (index, scored[index][1] + 1)

    ranked = [pair for pair in sorted(scored, key=lambda pair: (-pair[1], pair[0]))
              if pair[1] > 0]
    # 整册无模块结构、仅在文末追加了速查条目的手册：preamble 是全部正文，本身就
    # 超过预算。此时头部（手册的总纲与核心方法）与命中的速查模块平分预算，谁都
    # 不独占。有模块结构的手册 preamble 均远小于预算，走不进这个分支。
    if len(preamble) >= limit:
        # 头部封顶 1200：整册头部再长，也要给命中的第 2、3 名条目留全量空间
        # （2026-08-09：排序配对条目曾差 9 字符被挤出）。
        head = preamble[: min(limit // 2, 1200)]
        pieces, room = [], limit - len(head)
        for rank_pos, (index, _) in enumerate(ranked):
            if room <= 60:
                break
            module = modules[index]
            if len(module) > room:
                # 只有榜首允许截断；次名截断会剪掉条目尾部的收尾配方，宁可跳过
                # 换一个能整条放下的。
                if rank_pos == 0:
                    pieces.append((index, module[:room]))
                    room = 0
                continue
            pieces.append((index, module))
            room -= len(module)
        return head + "".join(piece for _, piece in sorted(pieces))
    # The top-scoring module gets the budget first, even if it must be truncated to
    # fit. Filling greedily by document order instead would seat two small unrelated
    # modules and leave no room for the one actually written for this problem — which
    # is the failure this whole module exists to prevent.
    best = ranked[0][0]
    room = max(0, limit - len(preamble))
    if len(modules[best]) > room:
        return (preamble + modules[best][:room]) if room else modules[best][:limit]

    kept = [best]
    used = len(preamble) + len(modules[best])
    for index, _ in ranked[1:]:
        length = len(modules[index])
        if used + length > limit:
            continue
        kept.append(index)
        used += length

    parts = [preamble] + [modules[index] for index in sorted(kept)]
    excerpt = "".join(parts)
    return excerpt if len(excerpt) <= limit else excerpt[:limit]
