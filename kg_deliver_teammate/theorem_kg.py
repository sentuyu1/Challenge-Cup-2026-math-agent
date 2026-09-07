"""theorem_kg.py — 数学定理知识图谱（独立模块，与 knowledge_graph.py 并行）。

用途：统一管理 "种类繁多" 的数学定理，供 user_agent 在题目检索到相关定理后注入
该定理的表述/前置条件/结论/证明思路，指导解题。与题型图谱互补：
  - knowledge_graph.py：按题型给方法论（18 类）
  - theorem_kg.py：按定理名/题目给单条定理知识（~87 个实体 + 同名异义消歧）

设计原则：
  - 纯标准库（dataclasses/typing/os/json/re），零依赖，可随文件迁移。
  - 数据在 theorem_data.py（THEOREM_DATA + DISAMBIG_MAP），本模块惰性加载。
  - 全程 try/except，异常返回 (0,"")，绝不打断主流程。
  - 同名异义优先：Cauchy/Cayley/Euler/Lagrange/Fourier/Sturm/Heine 等在同一
    裸名下分不同实体，按 domain + 触发词评分消歧。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import os
import re

__all__ = [
    "TheoremNode", "get_theorem", "find_theorems", "theorem_hint",
    "search_theorems", "theorems_by_category", "theorem_stats",
    "disambiguate_roots", "all_theorem_ids", "infer_chain",
]


# ===================== 数据结构 =====================

@dataclass
class TheoremNode:
    tid: str
    theorem_en: str
    theorem_cn: str
    aliases: list = field(default_factory=list)
    domains: list = field(default_factory=list)
    category: list = field(default_factory=list)
    statement: str = ""
    preconditions: list = field(default_factory=list)
    conclusion: str = ""
    proof_idea: str = ""
    related_theorems: list = field(default_factory=list)
    disambiguation: str = ""
    keywords: list = field(default_factory=list)
    source_domain: str = ""


# ===================== 数据装载 =====================
_THEOREMS: dict = {}
_LOADED = False

# 同名根 -> 覆盖题型（用于无问题context时的领域提示）
_DOMAIN_CN = {
    "algebra": "代数", "linear_algebra": "线性代数", "calculus": "微积分",
    "complex_analysis": "复分析", "geometry": "几何", "number_theory": "数论",
    "combinatorics": "组合数学", "graph_theory": "图论", "probability": "概率论",
    "differential_equations": "微分方程", "partial_differential_equations": "偏微分方程",
    "topology": "拓扑学", "real_analysis": "实分析", "functional_analysis": "泛函分析",
    "abstract_algebra": "抽象代数", "operations_research": "运筹学",
    "numerical_analysis": "数值分析", "mathematical_physics": "数学物理方法",
}


def _load() -> None:
    global _THEOREMS, _LOADED
    if _LOADED:
        return
    from theorem_data import THEOREM_DATA, DISAMBIG_MAP as _DM  # noqa: F401
    _THEOREMS = {tid: TheoremNode(**d) for tid, d in THEOREM_DATA.items()}
    _LOADED = True


def _dm() -> dict:
    from theorem_data import DISAMBIG_MAP
    return DISAMBIG_MAP


# ===================== 检索基础 =====================

def all_theorem_ids() -> list:
    _load()
    return sorted(_THEOREMS.keys())


def get_theorem(tid: str) -> Optional[TheoremNode]:
    _load()
    return _THEOREMS.get(tid)


def _dl(d: dict, k, default=None):
    v = d.get(k)
    return default if v is None else v


def _build_node(tid: str) -> Optional[TheoremNode]:
    _load()
    d = _THEOREMS.get(tid)
    return d


# ===================== 同名异义根匹配 =====================

def _contains_any(text: str, probes) -> int:
    tl = (text or "").lower()
    return sum(1 for p in (probes or []) if p and p.lower() in tl)


def disambiguate_roots(text: str, domain: str = "") -> list:
    """在文本中检测出现的同名异义根，返回 [(root, 选出的tid 或 None=需多候选)]"""
    _load()
    text = text or ""
    tl = text.lower()
    found = []
    for root, cfg in _dm().items():
        root_l = root.lower()
        # 检查根是否出现在文本（英文根或中文名）
        hit = (root_l in tl) or (cfg.get("name_cn") and cfg["name_cn"] in text)
        if not hit:
            # 也检查 group tid 的别名是否命中
            for g in cfg.get("groups", []):
                node = _build_node(g["tid"])
                if node and any(a.lower() in tl for a in node.aliases if a):
                    hit = True
                    break
        if not hit:
            continue
        # 消歧：有 domain 先用 domain，再用 probe 评分
        groups = cfg.get("groups", [])
        best_tid, best_score = None, 0
        for i, g in enumerate(groups):
            score = 0
            if domain and domain in g.get("domains", []):
                score += 100
            score += _contains_any(text, g.get("probe", []))
            if score > best_score:
                best_tid, best_score = g["tid"], score
        if best_tid:
            found.append((root, best_tid, best_score))
        else:
            found.append((root, None, 0))
    return found


# ===================== 精确/别名检索 =====================

def find_theorems(name: str, domain: str = "") -> list:
    """按定理名/别名/中文名匹配，返回匹配节点（限定 domain 时过滤）。"""
    _load()
    if not name:
        return []
    name_l = (name or "").strip().lower()
    # 先查同名根
    for root, cfg in _dm().items():
        root_l = root.lower()
        if name_l in (root_l, str(cfg.get("name_cn", "")).lower()):
            # 返回该根全部候选（附带 disambiguation）
            out = []
            for g in cfg.get("groups", []):
                n = _build_node(g["tid"])
                if n and (not domain or domain in n.domains):
                    out.append(n)
            return out
    # 精确/别名匹配
    results = []
    for n in _THEOREMS.values():
        if domain and domain not in n.domains:
            continue
        en_l = n.theorem_en.lower()
        cn_l = n.theorem_cn.lower()
        if name_l == en_l or name_l == cn_l or name_l in (a.lower() for a in n.aliases):
            results.append(n)
            continue
        # 子串包含（定理名完整出现）
        if name_l and (name_l in en_l or name_l in cn_l or (n.theorem_en and n.theorem_en.lower() in name_l)):
            results.append(n)
    return results


# ===================== 关键词评分检索 =====================

def _score_problem(problem: str, node: TheoremNode) -> int:
    pl = (problem or "").lower()
    score = 0
    score += _contains_any(pl, node.keywords) * 2
    score += 1 if node.theorem_cn and node.theorem_cn.lower() in pl else 0
    score += _contains_any(pl, node.aliases)
    score += 1 if node.statement and any(len(w) > 1 and w.lower() in pl for w in re.findall(r"[a-zA-Z]{2,}", node.statement)[:6]) else 0
    return score


# ===================== 主入口 =====================

def _assemble(nodes: list, max_len: int) -> str:
    lines = ["\n\n## 定理知识图谱"]
    for i, n in enumerate(nodes, 1):
        domain_names = "、".join(_DOMAIN_CN.get(d, d) for d in n.domains if _DOMAIN_CN.get(d))
        lines.append(f"\n### {i}. {n.theorem_cn} ({n.theorem_en}) [{'/'.join(n.domains)}]")
        lines.append(f"- 表述：{n.statement}")
        if n.preconditions:
            lines.append("- 前置条件：" + "；".join(n.preconditions))
        if n.conclusion:
            lines.append(f"- 主要结论/用法：{n.conclusion}")
        if n.proof_idea:
            lines.append(f"- 证明思路：{n.proof_idea}")
        if n.disambiguation:
            lines.append(f"- 同名区分：{n.disambiguation}")
    text = "\n".join(lines)
    if len(text) > max_len:
        text = text[:max_len] + "\n…(已截断)"
    return text


def theorem_hint(keyword: str = "", problem: str = "", domain: str = "",
                 max_len: int = 1200) -> tuple:
    """主入口：按定理名/题目/题型检索相关定理，返回 (命中实体数, 提示文本)。

    检索优先级：同名根消歧 → 精确/别名 → 关键词评分 top。
    无法/异常返回 (0, "")。
    """
    try:
        _load()
        if not any([keyword, problem]):
            return 0, ""
        text = keyword or problem or ""
        # 1) 同名根消歧
        roots = disambiguate_roots(text, domain)
        chosen = []
        for (_root, tid, _score) in roots:
            if tid:
                n = _build_node(tid)
                if n and n not in chosen:
                    chosen.append(n)
        # 2&3) 若非根命中，做精确/关键词检索
        if not chosen:
            if keyword:
                chosen = find_theorems(keyword, domain)
            else:
                best_score, best_nodes = 0, []
                for n in _THEOREMS.values():
                    if domain and domain not in n.domains:
                        continue
                    s = _score_problem(problem, n)
                    if s > best_score:
                        best_score, best_nodes = s, [n]
                    elif s == best_score:
                        best_nodes.append(n)
                if best_score > 0:
                    chosen = best_nodes[:3]
        if not chosen:
            return 0, ""
        text = _assemble(chosen, max_len=max_len)
        # 知识推理：追加命中定理的可推导关联（不超出 max_len）
        infer = _assemble_inference(chosen, max_len)
        if infer and len(text) + len(infer) < max_len:
            text += "\n" + infer
        return len(chosen), text
    except Exception:  # noqa: BLE001
        return 0, ""


def search_theorems(problem: str, domain: str = "", max_len: int = 1200) -> tuple:
    """便捷封装：theorem_hint(problem=problem, domain=domain)。"""
    return theorem_hint(problem=problem, domain=domain, max_len=max_len)


def theorems_by_category(category: str) -> list:
    _load()
    return [n.tid for n in _THEOREMS.values() if category in n.category]


# ===================== 统计 =====================

def theorem_stats() -> dict:
    _load()
    by_cat: dict = {}
    by_dom: dict = {}
    for n in _THEOREMS.values():
        for c in n.category:
            by_cat[c] = by_cat.get(c, 0) + 1
        for d in n.domains:
            by_dom[d] = by_dom.get(d, 0) + 1
    return {
        "n_theorems": len(_THEOREMS),
        "n_ambig_groups": len(_dm()),
        "extracted_raw": getattr(__import__("theorem_data"), "EXTRACTED_RAW", 77),
        "by_category": dict(sorted(by_cat.items(), key=lambda x: -x[1])),
        "by_domain": dict(sorted(by_dom.items(), key=lambda x: -x[1])),
    }


# ===================== 知识推理层（知识加工·推理）=====================
# 综述「知识加工」含知识推理：由既有知识关系推出隐含关联，拓展现有知识。
# 实现：基于 related_theorems 建关联图，BFS 挖掘"命中定理 → 关联定理 → 间接推导"路径。

_REL_GRAPH: dict = {}


def _build_graph() -> dict:
    global _REL_GRAPH
    if _REL_GRAPH:
        return _REL_GRAPH
    _load()
    g = {tid: [] for tid in _THEOREMS}
    for tid, n in _THEOREMS.items():
        for ref in n.related_theorems:
            if ref in _THEOREMS:
                g[tid].append(ref)
                # 无向化（对称），便于反向推导
                g.setdefault(ref, []).append(tid)
    _REL_GRAPH = g
    return g


def infer_chain(tid: str, depth: int = 2, max_nodes: int = 5) -> list:
    """从 tid 出发 BFS，返回与之相关的定理链（关联/间接推导路径）。

    返回 [(tid, hop)]：hop=0 自身（不含）、1 直接关联、2 间接关联。按 hop 升序、去重。
    """
    try:
        _load()
        _build_graph()
        if tid not in _REL_GRAPH:
            return []
        seen = {tid}
        frontier = [(tid, 0)]
        results = []
        while frontier:
            cur, hop = frontier.pop(0)
            if hop >= depth:
                continue
            for nb in _REL_GRAPH.get(cur, []):
                if nb in seen:
                    continue
                seen.add(nb)
                results.append((nb, hop + 1))
                if hop + 1 < depth and len(results) < max_nodes:
                    frontier.append((nb, hop + 1))
        results.sort(key=lambda x: x[1])
        return results[:max_nodes]
    except Exception:  # noqa: BLE001
        return []


def _assemble_inference(nodes: list, max_len: int) -> str:
    """组装推理提示：每个命中定理附带其关联/推导路径。"""
    lines = []
    for n in nodes:
        chain = infer_chain(n.tid, depth=2, max_nodes=4)
        if not chain:
            continue
        rels = [(tid, hop) for tid, hop in chain if tid != n.tid]
        if not rels:
            continue
        hop1 = [_THEOREMS[t].theorem_cn for t, h in rels if h == 1][:3]
        hop2 = [_THEOREMS[t].theorem_cn for t, h in rels if h == 2][:2]
        parts = []
        if hop1:
            parts.append("直接关联：" + "、".join(hop1))
        if hop2:
            parts.append("可间接推导/" + "、".join(hop2))
        if parts:
            lines.append(f"- 知识推理：{n.theorem_cn} ↔ " + " ｜ ".join(parts))
    if not lines:
        return ""
    return "\n".join(lines)


# ===================== 自检 =====================
if __name__ == "__main__":
    st = theorem_stats()
    print("定理实体:", st["n_theorems"], "| 抽取原始:", st["extracted_raw"],
          "| 同名根:", st["n_ambig_groups"])

    # 同名消歧断言
    print("\n=== find_theorems('Cauchy','complex_analysis') ===")
    for n in find_theorems("Cauchy", "complex_analysis")[:6]:
        print("  ", n.tid, n.theorem_cn)
    print("\n=== theorem_hint('柯西不等式') 应命中内积子项（cauchy-schwarz）===")
    k, t = theorem_hint("柯西不等式", domain="linear_algebra")
    print("  hits=", k)
    for ln in t.split("\n"):
        if "###" in ln:
            print("  ", ln.strip())
    print("\n=== theorem_hint('柯西积分定理') 应命中积分子项 ===")
    k, t = theorem_hint("柯西积分定理", domain="complex_analysis")
    print("  hits=", k)
    for ln in t.split("\n"):
        if "###" in ln:
            print("  ", ln.strip())
    print("\n=== 兜底：未知 → (0,'') ===")
    print("  ", theorem_hint("")
)