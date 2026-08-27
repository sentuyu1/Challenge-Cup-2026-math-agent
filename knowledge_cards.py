"""utils/knowledge_cards.py — 知识卡片检索（借鉴折叠桌 card_retriever 思想）。

内置「方法卡片 + 检查清单卡片」（通用解题方法论）+ 从 knowledge/*.txt
加载领域知识卡片，按题目关键词打分，返回相关片段注入 prompt。
零依赖（纯关键词打分，无向量库）。
"""

from __future__ import annotations

import re
from pathlib import Path

# 内置方法卡片（通用解题方法论）
_METHOD_CARDS = [
    "证明时先写清题设与目标；引用定理前核对前提，再给出从条件到结论的关键推导。",
    "计数题先明确对象是否有序、是否允许重复；容斥法必须定义违例事件并检查交集层数。",
    "代数结构题先展开定义，再检查运算、子结构、同态或商结构的必要条件。",
    "分析题使用定理前检查连续、可导、可积、收敛或支配等前提，并单独检查端点。",
    "概率题先明确样本空间和事件定义；条件概率与独立性的前提必须逐条核对。",
]

# 内置检查清单卡片（判分硬性要求）
_CHECK_CARDS = [
    "最终答案必须覆盖题目的全部所求对象；多问题按题目顺序分别作答，不能只给中间量。",
    "方程题必须列出全部根、检查定义域和伪根；离散根不能写成区间。",
    "证明必须具备关键条件、依据、推导链和结论；仅写定理名称或结论不构成证明。",
    "审查全称命题或逆命题时，尝试检查边界情形、反例以及量词方向。",
    "极值题求最小/最大值必须上界推导 + 下界构造双侧夹出，任一侧缺失即未定。",
]


def _tokens(text: str) -> set:
    tokens = set(re.findall(r"[A-Za-z]{2,}|\d+", text.lower()))
    for run in re.findall(r"[一-鿿]+", text):
        for width in (2, 3):
            for i in range(max(0, len(run) - width + 1)):
                tokens.add(run[i:i + width])
    return tokens


class KnowledgeCards:
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.cards = [*_METHOD_CARDS, *_CHECK_CARDS]
        self.cards += self._load(Path(knowledge_dir))

    def _load(self, d: Path) -> list:
        if not d.is_dir():
            return []
        out = []
        for path in sorted(d.glob("*.txt")):
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                text = line.strip()
                if text and not text.startswith("主题："):
                    out.append(text[:400])
        return out

    def retrieve(self, problem: str, category: str, max_cards: int = 5) -> str:
        """按题目关键词打分，返回相关卡片文本（方法+检查清单+领域知识）。"""
        query = _tokens(problem)
        # 方法卡片和检查清单卡片固定高分（通用方法论），领域卡片按关键词打分
        scored = []
        for card in self.cards:
            card_tokens = _tokens(card)
            score = len(query & card_tokens)
            # 检查清单和方法卡片始终保留（通用价值高）
            if card in _CHECK_CARDS:
                score += 2
            elif card in _METHOD_CARDS:
                score += 1
            if score:
                scored.append((score, card))

        scored.sort(key=lambda x: -x[0])
        # 去重选卡片（保留高分 + 多样性）
        selected = []
        for score, card in scored:
            if any(card[:20] == s[1][:20] for s in selected):
                continue
            selected.append((score, card))
            if len(selected) >= max_cards:
                break
        return "\n".join(f"- {card}" for _, card in selected)
