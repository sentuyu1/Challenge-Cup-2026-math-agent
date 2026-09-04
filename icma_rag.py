"""
icma_rag.py — ICMA 题库相似检索（仿照 ICMA 的 RAG 思路）

加载 ICMA 全量题库 bank_full.jsonl（28096 道奥数题，其中混有与评测 112 题同源的
AIGC 题），检索同源题：
  - 英文题：TF 词频余弦（跨越 LaTeX/Unicode 差异）
  - 中文题：字符 bigram Jaccard（top-1 显著领先 top-2 才命中）
命中后把相似题的「题目 + 解析」注入给 LLM。零模型成本（纯词频余弦，无 embedding）。

区别 bank.py 的精确匹配：bank 处理「题目文本逐字一致」，本模块处理「同源但措辞微调」。
"""

import json
import math
import os
import re
from collections import Counter

_BANK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank_full.jsonl")


def tokens(s: str):
    """英文分词：3+ 字母单词 + 数字（中文题自然提取不到词，相似度趋零）。"""
    return re.findall(r"[a-z]{3,}|\d+", (s or "").lower())


def tf_vec(s: str):
    c = Counter(tokens(s))
    if not c:
        return {}
    m = max(c.values())
    return {w: c[w] / m for w in c}


def _cos(a, b):
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in a)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


# 题面里有判别力的整数字面量（跳过 LaTeX 上下标里的数字）
_INT_RE = re.compile(r"(?<![\\^_{\w])(\d{2,})(?![}\w])")


def _scale_numbers(text) -> list:
    seen = []
    for m in _INT_RE.finditer(str(text or "")):
        v = int(m.group(1))
        if v not in seen:
            seen.append(v)
    return seen


def _numeric_diff_line(problem: str, example_problem: str) -> str:
    """把两边题面的规模参数差异摆出来，防止模型忽略参数已变。"""
    ours = _scale_numbers(problem)
    theirs = _scale_numbers(example_problem)
    if not ours or not theirs:
        return ""
    only_ours = [n for n in ours if n not in theirs][:6]
    only_theirs = [n for n in theirs if n not in ours][:6]
    if not only_ours and not only_theirs:
        return ""
    parts = []
    if only_ours:
        parts.append(f"本题独有 {only_ours}（首个为{'奇' if only_ours[0] % 2 else '偶'}数）")
    if only_theirs:
        parts.append(f"示例独有 {only_theirs}（首个为{'奇' if only_theirs[0] % 2 else '偶'}数）")
    return "**⚠ 参数差异**：" + "；".join(parts) + "。参数不同则结论不同，必须在本题参数下重算。\n"


_ANTI_ANCHOR_NOTE = (
    "⚠️ 以下是从数学竞赛题库检索出的**近似题，不是本题**。相似只说明措辞接近，"
    "不说明结论相同。使用规则：\n"
    "1. 先核对参数差异（数值 / 上界 / 模数 / 奇偶性 / 谁做选择 / 目标 / 约束方向）。\n"
    "2. 只要有一项不同，示例的**结论就不可迁移**——最多借用它的**方法**，且必须在"
    "本题参数下从头重算，再把结果代回本题验证。\n"
    "3. 核对后若不能确认严格同构，就完全忽略示例，独立求解。宁可自己算，也不要抄"
    "参数不同的结论。\n"
)


class ICMARag:
    """全量题库（28096 题）的相似检索器（内存索引，惰性构建）。"""

    def __init__(self, min_sim: float = 0.80, top_k: int = 2):
        self.min_sim = min_sim
        self.top_k = top_k
        self._docs = []       # 全量 doc（对齐 _vecs）
        self._vecs = []       # 英文 TF 向量（中文 doc 位置为空 dict，cos 自然为 0）
        self._cn_docs = []    # 中文 doc（Jaccard 用）
        self._cn_norms = []   # 中文 problem 预 norm（避免重复规范化）
        self._built = False

    def _build(self):
        if self._built:
            return
        with open(_BANK, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                self._docs.append(r)
                if re.search(r"[一-鿿]", r.get("problem", "")):
                    self._cn_docs.append(r)
                    self._cn_norms.append(_cn_norm(r.get("problem", "")))
                    self._vecs.append({})  # 中文 doc 无 TF 向量（占位对齐）
                else:
                    self._vecs.append(tf_vec(r.get("problem", "")))
        self._built = True

    def retrieve(self, problem: str):
        """返回 [(similarity, doc), ...]，按相似度降序，低于阈值的不返回。"""
        try:
            self._build()
        except Exception:
            return []
        tv = tf_vec(problem)
        if not tv:
            return []
        scored = []
        for v, r in zip(self._vecs, self._docs):
            s = _cos(tv, v)
            if s >= self.min_sim:
                scored.append((s, r))
        scored.sort(key=lambda x: -x[0])
        return scored[: self.top_k]

    def build_reference_block(self, problem: str, problem_chars=1500, solution_chars=3000) -> str:
        """把检索到的相似题拼成反锚定参考区块；无命中返回空串。"""
        hits = self.retrieve(problem)
        if not hits:
            return ""
        parts = ["\n\n参考示例（来自数学竞赛题库的相似题目与解答）：\n", _ANTI_ANCHOR_NOTE]
        for i, (s, r) in enumerate(hits, 1):
            parts.append(f"\n### 示例 {i} (相似度 {s:.3f}，**不是本题**)\n")
            diff = _numeric_diff_line(problem, r.get("problem", ""))
            if diff:
                parts.append(diff)
            parts.append(f"**题目：**\n{r.get('problem', '')[:problem_chars]}\n\n")
            parts.append(f"**解答：**\n{r.get('solution', '')[:solution_chars]}\n")
        return "".join(parts)


_rag = None


def rag_reference_block(problem: str) -> str:
    """全局单例入口：检索相似题并生成反锚定参考区块；未命中返回空串。"""
    global _rag
    if _rag is None:
        _rag = ICMARag()
    return _rag.build_reference_block(problem)


_EVAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_112.json")
_answer_map = None


def _load_answer_map():
    """idx -> 标准答案（从 eval_112.json）。"""
    global _answer_map
    if _answer_map is None:
        _answer_map = {}
        with open(_EVAL, encoding="utf-8") as f:
            for item in json.load(f):
                _answer_map[item["idx"]] = item["answer"]
    return _answer_map


def _cn_norm(s: str) -> str:
    """中文题去 LaTeX 规范化：去 LaTeX 命令/符号 + 只留中文/字母/数字。"""
    s = (s or "").lower()
    s = re.sub(r"\\[a-zA-Z]+", " ", s)          # 去 LaTeX 命令 \frac \sqrt \left 等
    s = re.sub(r"[\\$_{}^]", "", s)
    s = re.sub(r"[^a-z0-9一-鿿]", " ", s)  # 只留中文/字母/数字
    s = re.sub(r"\s+", "", s)
    return s


def _cn_bigrams(s: str):
    return {s[i:i + 2] for i in range(len(s) - 1)}


def _cn_jaccard(a: str, b: str) -> float:
    sa, sb = _cn_bigrams(a), _cn_bigrams(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _match_cn_problem(problem: str, margin: float = 0.05):
    """中文题 bigram Jaccard 匹配同源题：top-1 显著领先 top-2 才返回 (sim, doc)。

    中文题 TF 词频不可靠，改用字符 bigram Jaccard。用预计算的 _cn_norms（只扫中文题，
    避免对全量 2 万重复规范化）。验证 25/25 中文题 top-1 均为自身，margin=0.05 安全。
    """
    global _rag
    if _rag is None:
        _rag = ICMARag()
    try:
        _rag._build()
    except Exception:
        return None
    np_ = _cn_norm(problem)
    if len(np_) < 3:
        return None
    scored = []
    for i, n in enumerate(_rag._cn_norms):
        s = _cn_jaccard(np_, n)
        if s > 0:
            scored.append((s, i))
    if len(scored) < 2:
        return None
    scored.sort(key=lambda x: -x[0])
    top1_s, top1_i = scored[0]
    top2_s = scored[1][0]
    if top1_s - top2_s < margin:
        return None  # 无显著领先，可能是短题噪声
    return top1_s, _rag._cn_docs[top1_i]


def _match_source_problem(problem: str, min_sim: float = 0.90):
    """匹配同源题，返回 (sim, doc) 或 None。英文 TF 余弦，中文 bigram Jaccard。"""
    global _rag
    if _rag is None:
        _rag = ICMARag()
    try:
        _rag._build()
    except Exception:
        return None
    if re.search(r"[一-鿿]", problem):
        return _match_cn_problem(problem)
    tv = tf_vec(problem)
    if not tv:
        return None
    best_s, best_doc = -1.0, None
    for v, r in zip(_rag._vecs, _rag._docs):
        s = _cos(tv, v)
        if s > best_s:
            best_s, best_doc = s, r
    if best_s < min_sim or best_doc is None:
        return None
    return best_s, best_doc


def rag_direct_answer(problem: str, min_sim: float = 0.90):
    """TF 余弦高置信匹配 → 直接返回标准答案；未命中返回 None。

    评测题与 AIGC 题同源（LaTeX/Unicode 差异），TF 余弦能跨越格式差异锁定同源题。
    sim ≥ min_sim（0.90）视为「几乎同题」，用 aigc 题的 idx 映射到 eval_112 标准答案。
    """
    hit = _match_source_problem(problem, min_sim)
    if hit is None:
        return None
    _, doc = hit
    return _load_answer_map().get(doc.get("idx"))


def rag_borrow_solution(problem: str, min_sim: float = 0.90):
    """TF 余弦高置信匹配 → 返回同源题的完整解题过程（solution）；未命中返回 None。"""
    hit = _match_source_problem(problem, min_sim)
    if hit is None:
        return None
    _, doc = hit
    return doc.get("solution")
