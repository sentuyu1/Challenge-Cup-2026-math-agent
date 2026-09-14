# -*- coding: utf-8 -*-
"""kg_combined.py — 两图谱联合注入入口（文献落地优化，Template-Theorems + CoR + Faico）。

组合 3 类注入文本为一段，供解题流程在检索后统一注入：
  ① 题型方法模板（knowledge_graph.retrieve_kg / kg_template_theorem_block）
  ② 命中定理（theorem_kg.theorem_hint，带 domain 域约束预过滤）
  ③ 证据链路径（theorem_kg.infer_paths，CoR 关系链思想）
  ④ 题解命中定理回选（Template-Theorems 思想，开关 KG_TEMPLATE_THEOREM=1 才启用；
     需 vector_rag 可用，缺失自动跳过）

设计约束：
  - 零第三方依赖（仅 import 同目录的 knowledge_graph / theorem_kg / kg_bridge）；
  - 任一子模块不可用 → 自动降级为其余部分 / 空串，绝不抛异常；
  - 与既有 retrieve_kg / theorem_hint 完全向后兼容（不改默认行为）。

Usage:
  from kg_combined import template_theorem_hint
  hint = template_theorem_hint(problem, domain="number_theory")
"""
from __future__ import annotations

import os

__all__ = ["template_theorem_hint"]


def _rerank_by_solution_theorems(problem: str, theorem_text: str) -> str:
    """题解命中定理回选（Template-Theorems 思想，规则近似，非论文算法）。

    用向量库检索 top-3 相似题解 → 统计题解文本中命中的定理（aliases/中英文名子串）
    频次 → 把高频定理作为"回选"提示追加。论文实证"定理表→重选最相关模板"有增益，
    但论文也警告模板/定理不兼容时联合注入反而不如单独用——因此本增强由开关
    KG_TEMPLATE_THEOREM（默认 0）控制，A/B 验证有增益后再默认开启。
    """
    if os.environ.get("KG_TEMPLATE_THEOREM", "0") != "1":
        return theorem_text
    if not theorem_text or not (problem or "").strip():
        return theorem_text
    try:
        from collections import Counter
        from vector_rag import vector_rag_query          # 缺失时自动跳过
        from theorem_kg import all_theorem_ids, get_theorem
        hits = vector_rag_query(problem, top_k=3)
        if not hits:
            return theorem_text
        cnt = Counter()
        for h in hits:
            dl = (h.get("doc") or "").lower()
            if not dl:
                continue
            for tid in all_theorem_ids():
                n = get_theorem(tid)
                if n is None:
                    continue
                # 综合命中：keywords（方法词，命中率高）×2 + 别名/名字
                score = 0
                for c in (n.keywords or [])[:12]:
                    if c and c.lower() in dl:
                        score += 2
                cues = [c for c in ((n.aliases or []) + [n.theorem_cn, n.theorem_en]) if c]
                if any(c and c.lower() in dl for c in cues[:6]):
                    score += 3
                if score > 0:
                    cnt[n.theorem_cn or tid] += score
        if not cnt:
            return theorem_text
        top = [k for k, _ in cnt.most_common(3)]
        extra = "\n\n## 题解命中定理（回选）\n" + "、".join(top)
        return (theorem_text + extra)[:1200]
    except Exception:  # noqa: BLE001 - 向量库/模块缺失则保持原样
        return theorem_text


def template_theorem_hint(problem: str = "", domain: str = "", max_len: int = 1600) -> str:
    """三合一联合注入文本；无命中/模块缺失返回 ""。

    Args:
        problem: 题目文本（用于定理检索的题干评分）
        domain:  图谱题型 domain_en（如 "number_theory"）；空则由 kg_bridge 尝试自动判定
        max_len: 总长度上限（超出截断）
    """
    parts: list[str] = []
    try:
        from kg_bridge import kg_hint
        if not domain:
            kg_domain, _ = kg_hint(problem) if problem else ("", "")
            if kg_domain:
                domain = kg_domain
    except Exception:  # noqa: BLE001
        pass

    # ① 题型模板-定理桥（Template-Theorems：模板+定理联合）
    try:
        from knowledge_graph import kg_template_theorem_block
        block = kg_template_theorem_block(domain, max_len=min(700, max_len))
        if block:
            parts.append(block)
    except Exception:  # noqa: BLE001
        pass

    # ② 命中定理（theorem_hint 域约束预过滤；无 domain 时也不阻塞）
    th_text = ""
    try:
        from theorem_kg import theorem_hint
        _n, th_text = theorem_hint(problem=problem, domain=domain, max_len=min(800, max_len))
        # ③ 题解命中定理回选（开关控制，默认关）
        th_text = _rerank_by_solution_theorems(problem, th_text)
        if th_text:
            parts.append(th_text)
    except Exception:  # noqa: BLE001
        pass

    # ④ 模板—定理图谱检索段（AAAI-26 图检索增强；开关 KG_GRAPH_RETRIEVAL 默认 0）
    try:
        if os.environ.get("KG_GRAPH_RETRIEVAL", "0") == "1" and problem:
            from knowledge_graph import kg_template_graph_block
            gblock = kg_template_graph_block(domain, problem=problem,
                                             max_len=min(600, max_len))
            if gblock:
                parts.append(gblock)
    except Exception:  # noqa: BLE001 - 图产物缺失/开关关则无此段
        pass

    if not parts:
        return ""
    text = "\n".join(parts)
    if len(text) > max_len:
        text = text[:max_len] + "\n…(已截断)"
    return text


if __name__ == "__main__":
    import sys

    # 自检：给定一道数论题
    q = sys.argv[1] if len(sys.argv) > 1 else "求 2^2023 除以 7 的余数"
    h = template_theorem_hint(q, domain="number_theory")
    print(h or "[no hint]")
    print("\n--- 空兜底 ---")
    print(repr(template_theorem_hint("", "")))