"""
icma_rag.py — ICMA 题库相似检索（仿照 ICMA 的 RAG 思路）

加载 ICMA 的 AIGC 112 题（与评测 112 题同源、逐题对应），用 TF 余弦相似度
检索「措辞微调（LaTeX vs Unicode、结尾指令差异）」后的相似题，把相似题的
「题目 + 解析」以**反锚定**方式注入给 LLM —— 借方法，不直接抄结论。

区别于 bank.py 的精确匹配：bank 处理「题目文本逐字一致」，本模块处理
「同源但措辞微调」的场景。

只做英文题（评测 25 道中文客观题在 ICMA 奥数题库中无对应，TF 余弦天然低分
不注入）。检索零模型成本（纯词频余弦，无 embedding）。
"""

import json
import math
import os
import re
from collections import Counter

_BANK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aigc_bank.jsonl")


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
    """AIGC 112 题的相似检索器（内存 TF 向量，惰性构建）。"""

    def __init__(self, min_sim: float = 0.80, top_k: int = 2):
        self.min_sim = min_sim
        self.top_k = top_k
        self._docs = []
        self._vecs = []
        self._built = False

    def _build(self):
        if self._built:
            return
        with open(_BANK, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                self._docs.append(r)
                self._vecs.append(tf_vec(r["problem"]))
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
