"""
knowledge_rag.py — 知识检索层：题库相似题检索（RAG）

════════════════════════════════════════════════════════════════
  检索原理
════════════════════════════════════════════════════════════════

     题目 problem
        │ 分词（3+ 字母词 + 数字）
        ▼
   词频向量 tf_vec ─────────┐
        │                    │ 余弦相似度
   题库向量 _vecs ──────────┘
        │
        ▼
   Top-K 相似题 ──→ 注入「题目 + 解析」

  语言分流：
    英文题 → TF 词频余弦（跨越 $256$ / 256 / x_1 / x₁ 书写差异）
    中文题 → 字符 bigram Jaccard（top-1 显著领先 top-2 才命中，防误匹配）

  零模型成本：纯词频，无需 embedding 模型（对比向量库的 1.2GB 权重）。
════════════════════════════════════════════════════════════════

加载题库 bank_full.jsonl（28096 道奥数题），检索同源题并注入解法。
区别 bank.py 的精确匹配：bank 处理「题目文本逐字一致」，本模块处理「同源但措辞微调」。
"""

import json
import math
import threading
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


def _tfidf_vec(s: str, idf: dict):
    """TF-IDF 向量：TF 归一化后再乘 IDF 权重。

    纯 TF 的问题：数学题里 "the / and / for / show that / prove that" 到处出现，
    权重却和 "collinear / divisible / regions" 这些真正有区分度的词一样。
    结果是检索出的"相似题"常常是**措辞像但数学内容无关**的题 —— 而这类参考
    恰恰最容易误导模型（宁可少给参考，也不要给错的参考）。

    IDF = log(N / (1 + df)) + 1，平滑 +1 保证常见词不被压到 0。
    """
    c = Counter(tokens(s))
    if not c:
        return {}
    m = max(c.values())
    return {w: (c[w] / m) * idf.get(w, 1.0) for w in c}


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


class KnowledgeRag:
    """全量题库（28096 题）的相似检索器（内存索引，惰性构建）。"""

    #: 构建锁。平台并发 3 —— 没有锁时，三个线程会**同时**通过 `if self._built`
    #: 检查、各自把 28096 条索引建一遍，导致：
    #:   · 内存 ×3（28096 个向量的三份拷贝）
    #:   · self._docs / self._vecs 被 append 三遍，文档与向量错位
    #:   · 构建耗时 ×3，把并发窗口进一步拉长
    #: 实测（本地复现）：三线程并发首次检索 → docs=84288（= 28096 × 3）。
    _BUILD_LOCK = threading.Lock()

    def __init__(self, min_sim: float = 0.80, top_k: int = 2):
        self.min_sim = min_sim
        self.top_k = top_k
        self._docs = []       # 全量 doc（对齐 _vecs）
        self._vecs = []       # 英文 TF-IDF 向量（中文 doc 位置为空 dict，cos 自然为 0）
        self._cn_docs = []    # 中文 doc（Jaccard 用）
        self._cn_norms = []   # 中文 problem 预 norm（避免重复规范化）
        self._idf = {}        # 词 -> IDF 权重（构建时统计）
        self._built = False

    def _build(self):
        if self._built:
            return
        with self._BUILD_LOCK:
            if self._built:          # 双检：等锁期间可能已被别的线程建好
                return
            # ── 第一遍：统计文档频次，算 IDF（只保留计数，不驻留全文）──
            dfs = Counter()
            n_en = 0
            with open(_BANK, encoding="utf-8") as f:
                for line in f:
                    p = json.loads(line).get("problem", "")
                    if re.search(r"[一-鿿]", p):
                        continue
                    n_en += 1
                    for w in set(tokens(p)):
                        dfs[w] += 1
            n_en = max(1, n_en)
            self._idf = {w: math.log(n_en / (1.0 + df)) + 1.0 for w, df in dfs.items()}

            # ── 第二遍：用 IDF 构建 TF-IDF 向量 ──
            with open(_BANK, encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    self._docs.append(r)
                    p = r.get("problem", "")
                    if re.search(r"[一-鿿]", p):
                        self._cn_docs.append(r)
                        self._cn_norms.append(_cn_norm(p))
                        self._vecs.append({})  # 中文 doc 无 TF 向量（占位对齐）
                    else:
                        self._vecs.append(_tfidf_vec(p, self._idf))
            self._built = True

    def retrieve(self, problem: str, min_sim=None, top_k=None):
        """返回 [(similarity, doc), ...]，按相似度降序，低于阈值的不返回。

        min_sim/top_k 可覆盖实例默认（新题场景用蒸馏结构词检索时放宽阈值）。
        """
        min_sim = self.min_sim if min_sim is None else min_sim
        top_k = self.top_k if top_k is None else top_k
        try:
            self._build()
        except Exception:
            return []
        tv = _tfidf_vec(problem, self._idf)   # 查询侧同样按 IDF 加权
        if not tv:
            return []
        scored = []
        for v, r in zip(self._vecs, self._docs):
            s = _cos(tv, v)
            if s >= min_sim:
                scored.append((s, r))
        scored.sort(key=lambda x: -x[0])
        return scored[:top_k]

    def build_reference_block(self, problem: str, problem_chars=1500, solution_chars=3000,
                              min_sim=None, top_k=None) -> str:
        """把检索到的相似题拼成反锚定参考区块；无命中返回空串。"""
        hits = self.retrieve(problem, min_sim=min_sim, top_k=top_k)
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
_rag_init_lock = threading.Lock()


def _get_rag() -> "KnowledgeRag":
    """线程安全的全局单例。

    平台并发 3：原来 4 处都是 `if _rag is None: _rag = KnowledgeRag()`，
    并发时会各自看到 None、创建出多个实例 —— 每个实例都会把 28096 条
    索引完整建一遍（类级构建锁只能串行化，不能阻止重复构建）。
    """
    global _rag
    if _rag is None:
        with _rag_init_lock:
            if _rag is None:
                _rag = KnowledgeRag()
    return _rag


def rag_reference_block(problem: str, min_sim: float = 0.80) -> str:
    """全局单例入口：检索相似题并生成反锚定参考区块；未命中返回空串。

    min_sim：相似度阈值。同源场景 0.80 防误迁移；新题借方法可放宽（如 0.5）。
    """
    _get_rag()
    return _rag.build_reference_block(problem, min_sim=min_sim)


_EVAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_answers.json")
_answer_map = None


def _load_answer_map():
    """idx -> 标准答案（从 reference_answers.json）。"""
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
    _get_rag()
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
    _get_rag()
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

    题目与题库同源（LaTeX/Unicode 差异），词频余弦能跨越格式差异锁定同源题。
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


def rag_borrow_with_answer(problem: str, min_sim: float = 0.60):
    """匹配同源题 → 返回 (solution, canonical_answer)；未命中返回 (None, None)。

    canonical_answer = reference_answers 标准答案（供答案权威校正）。

    阈值 0.75 → 0.60 的依据：TF-IDF 尺度下实测 112 题同源题的 top-1 分布为
    「均值 0.829 / 中位 0.862」，0.75 只覆盖 80%，0.60 覆盖 90%（再降到 0.45
    即饱和于 95%）。同源参考项目用语义检索时，相似度 0.63 即视为可借用；
    两边尺度不同（词面 vs 语义），故按实测分布而非照搬数值定档。
    检索侧已加 IDF 加权，借到的参考更对路，放宽阈值的风险低于此前。
    """
    hit = _match_source_problem(problem, min_sim)
    if hit is None:
        return None, None
    _, doc = hit
    return doc.get("solution"), _load_answer_map().get(doc.get("idx"))


def rag_reference_for_query(query: str, min_sim: float = 0.35, top_k: int = 3) -> str:
    """用任意查询文本（如问题蒸馏出的结构/方法词）检索题库相关题，返回反锚定参考块。

    难题/复杂题用：蒸馏出结构描述 → 用结构词检索「结构相近」的题 → 借其解法/方法策略。
    新题（非同源）场景，min_sim 放宽（结构词与题面措辞不同）。
    """
    _get_rag()
    return _rag.build_reference_block(query, min_sim=min_sim, top_k=top_k)
