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
import json
import os
import re

__all__ = [
    "TheoremNode", "get_theorem", "find_theorems", "theorem_hint",
    "search_theorems", "theorems_by_category", "theorem_stats",
    "disambiguate_roots", "all_theorem_ids", "infer_chain", "infer_paths",
    "theorems_from_text",
]


def theorems_from_text(text: str) -> dict:
    """论文"定理抽取"平替：在文本中统计命中的定理 tid → 次数。

    复用 pipeline.kg_theorem_extract 的合并正则（THEOREM_DATA 中英文名/别名/
    关键词），供模板—定理图谱构建与题解回选使用。模块不可用时返回空 dict，
    绝不抛异常（零依赖设计）。
    """
    try:
        import os
        import sys
        _pipe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline")
        if _pipe not in sys.path:
            sys.path.insert(0, _pipe)
        from kg_theorem_extract import theorems_from_text as _t
        return _t(text) if text else {}
    except Exception:  # noqa: BLE001
        return {}


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
        # 知识推理：追加命中定理的证据链路径（域约束+三标准打分，不超出 max_len）
        infer = _assemble_inference(chosen, max_len, domain, problem)
        if infer and len(text) + len(infer) < max_len:
            text += "\n" + infer
        # 竞赛实证：历史题解提及（可选增强，缺失文件不影响）
        ev = _evidence_section(chosen, 260)
        if ev and len(text) + len(ev) <= max_len:
            text += ev
        return len(chosen), text
    except Exception:  # noqa: BLE001
        return 0, ""


def search_theorems(problem: str, domain: str = "", max_len: int = 1200) -> tuple:
    """便捷封装：theorem_hint(problem=problem, domain=domain)。"""
    return theorem_hint(problem=problem, domain=domain, max_len=max_len)


def theorems_by_category(category: str) -> list:
    _load()
    return [n.tid for n in _THEOREMS.values() if category in n.category]


# ===================== 竞赛实证层（可选增强，产物已随换源移除）=====================
# 由专用脚本生成；文件缺失不影响主流程（纯增益）。

_EVID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theorem_evidence.json")
_EVID_LLM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theorem_evidence_llm.json")
_evid_cache: dict = {}
_evid_llm_cache: dict = {}


def _load_evid() -> dict:
    global _evid_cache
    if not _evid_cache:
        try:
            with open(_EVID_FILE, encoding="utf-8") as f:
                _evid_cache = json.load(f)
        except Exception:  # noqa: BLE001
            _evid_cache = {}
    return _evid_cache


def _load_evid_llm() -> dict:
    global _evid_llm_cache
    if not _evid_llm_cache:
        try:
            with open(_EVID_LLM_FILE, encoding="utf-8") as f:
                _evid_llm_cache = json.load(f)
        except Exception:  # noqa: BLE001
            _evid_llm_cache = {}
    return _evid_llm_cache


def _evidence_section(nodes: list, max_len: int) -> str:
    """给命中定理追加"历史题解提及 + LLM 复核"实证段；无数据返回 ""。"""
    ev = _load_evid()
    llm = _load_evid_llm()
    lines = []
    for n in nodes[:3]:
        rec = ev.get(n.tid)
        if not rec:
            continue
        m = int(rec.get("mentions") or 0)
        if m <= 0:
            continue
        tag = ""
        v = llm.get(n.tid)
        if v is not None:
            tag = "，LLM 复核" + ("确认使用" if v.get("used") == 1 else "未确认")
        ex = (rec.get("examples") or [""])[0][:30]
        lines.append(f"- {n.theorem_cn}：历史题解中 {m} 篇提及{tag}" + (f"（例：{ex}…）" if ex else ""))
    if not lines:
        return ""
    text = "\n\n## 竞赛实证（历史提及，非必用定理）\n" + "\n".join(lines)
    return text[:max_len]


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


def infer_chain(tid: str, depth: int = 2, max_nodes: int = 5, domain: str = "") -> list:
    """从 tid 出发 BFS，返回与之相关的定理链（关联/间接推导路径）。

    返回 [(tid, hop)]：hop=0 自身（不含）、1 直接关联、2 间接关联。按 hop 升序、去重。

    domain 非空时启用域约束预过滤（Faico 思想）：扩展时只走"两端点任一 domain 匹配"
    的边，过滤掉跨域误关联（如线代的 Cayley-Hamilton ↔ 群论的 Cayley 定理），
    默认空 = 现行为（不约束，向后兼容）。
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
                if domain and not _domain_compatible(nb, domain):
                    continue
                seen.add(nb)
                results.append((nb, hop + 1))
                if hop + 1 < depth and len(results) < max_nodes:
                    frontier.append((nb, hop + 1))
        results.sort(key=lambda x: x[1])
        return results[:max_nodes]
    except Exception:  # noqa: BLE001
        return []


def _domain_compatible(tid: str, domain: str) -> bool:
    """定理 tid 是否与 domain 兼容（tid 的 domains 含该 domain，或该 domain 为超类提示）。"""
    try:
        n = _build_node(tid)
        if n is None:
            return False
        d = n.domains or []
        return domain in d
    except Exception:  # noqa: BLE001
        return False


def _path_score(tid: str, problem: str, domain: str) -> int:
    """证据链候选三标准打分（CoR 三标准的规则近似，非论文算法）：
    - 逻辑一致性：domain 匹配（已有过滤，此处 +2 巩固）
    - 语义对齐：keywords/aliases 与题干重叠
    - 目标邻近：conclusion 含题干关键词
    """
    try:
        n = _build_node(tid)
        if n is None:
            return 0
        pl = (problem or "").lower()
        score = 0
        if domain and domain in (n.domains or []):
            score += 2
        if pl:
            score += min(3, _contains_any(pl, n.keywords))
            score += min(2, _contains_any(pl, n.aliases))
            concl = (n.conclusion or "").lower()
            if concl and pl:
                overlap = sum(1 for w in re.findall(r"[a-zA-Z]{3,}", pl)[:10] if w in concl)
                score += min(2, overlap)
        return score
    except Exception:  # noqa: BLE001
        return 0


def infer_paths(tid: str, domain: str = "", max_len: int = 280, problem: str = "") -> str:
    """返回从 tid 出发的证据链路径文本（形如 A → B → C，CoR 关系链思想）。

    按"三标准打分"对候选排序（top-3 剪枝），优先输出本域内高相关路径；
    无路径返回 ""。
    """
    try:
        _load()
        _build_graph()
        if tid not in _REL_GRAPH:
            return ""
        chain = infer_chain(tid, depth=2, max_nodes=6, domain=domain)
        if not chain:
            return ""
        # 三标准打分排序（top-3）
        scored = [(_path_score(nb, problem, domain), nb, hop) for nb, hop in chain]
        scored.sort(key=lambda x: (-x[0], x[2]))
        scored = scored[:3]
        names = []
        for _s, nb, _hop in scored:
            node = _build_node(nb)
            if node is None:
                continue
            names.append(node.theorem_cn or nb)
        if not names:
            return ""
        head = _build_node(tid)
        text = " → ".join([head.theorem_cn if head else tid] + names)
        return text[:max_len]
    except Exception:  # noqa: BLE001
        return ""


def _assemble_inference(nodes: list, max_len: int, domain: str = "", problem: str = "") -> str:
    """组装推理提示：每个命中定理输出其证据链路径（CoR 关系链思想，域约束+三标准打分）。

    domain 非空时只保留该题型内的推导链；problem 非空时按三标准打分排序证据链。
    """
    lines = []
    for n in nodes:
        # 证据链路径：A → B → C（本域优先，三标准打分）
        path = infer_paths(n.tid, domain=domain, max_len=min(200, max_len), problem=problem)
        if path:
            lines.append(f"- 推导链：{path}")
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