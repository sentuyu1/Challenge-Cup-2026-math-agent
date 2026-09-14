# -*- coding: utf-8 -*-
"""kg_runtime_graph.py — 高效版"模板—定理图谱"图检索增强生成（AAAI-26 Graph-RAG 平替）。

相对旧版的三项核心优化（针对"系统已识别题型→快速检索经验"场景）：
  1) 预构建索引（首次加载建好，之后 O(1)）：
     - _DOM_OFFSETS : domain -> npy 行号数组（域预过滤，候选从全量 1211 缩到几十）
     - _ID_POS      : template_id -> 矩阵行号
     - _ADJ         : template_id -> [(theorem_id, weight)]（模板↔定理邻接表）
     - _TPL_TEXT    : template_id -> 模板文本（不再线性遍历 JSON 找文本）
  2) 域预过滤检索：graph_retrieve(problem, domain=...) 只在该域子矩阵上点积，
     命中后经 Algorithm 1（top_k + 阈值 m）返回；无 domain 时回退全量（向后兼容）。
  3) 一次加载缓存：图 JSON + 嵌入矩阵 + 索引首次全部加载，重复查询不再重扫。

对外接口（向后兼容）：
  graph_retrieve(problem, top_k=5, m=0.45, domain="") -> [(id, sim, dom)]
  theorem_table(problem, top_k, m, limit, domain="")  -> [(theorem_id, score)]
  rerank_template(problem, theorem_ids, ..., domain="")
  graph_retrieve_block(problem, max_len, domain="")   -> str 提示段
  graph_stats()                                        -> dict
零第三方依赖（numpy 即可）；全程 try/except 返回空/降级，绝不抛异常。
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

__all__ = ["graph_retrieve", "theorem_table", "rerank_template",
           "graph_retrieve_block", "graph_stats", "export_template_embeddings",
           "warmup", "index_stats"]

PIPE_DIR = os.path.dirname(os.path.abspath(__file__))
ART_DIR = os.path.join(PIPE_DIR, "artifacts")
GRAPH_OUT = os.path.join(ART_DIR, "template_theorem_graph.json")
EMB_NPY = os.path.join(ART_DIR, "templates_emb.npy")

# ---- 嵌入模型路径（队友迁移环境：设环境变量 KG_BGE_MODEL_DIR 指向本机 bge-small-zh-v1.5；
#      模型缺失时图检索自动降级为仅模板/定理，不影响其余图谱）----
MODEL_DIR = os.environ.get("KG_BGE_MODEL_DIR", "")

# 检索默认参数（论文 Algorithm 1：top_k + 阈值 m）
TOP_K = 5
THRESHOLD_M = 0.45

# ---------------- 运行时缓存 ----------------
_GRAPH = None      # 完整图谱 JSON
_MODEL = None      # bge 模型
_EMB = None        # float16 嵌入矩阵 (N,512)
_IDS = None        # [template_id] 与矩阵行对齐
_ID_POS = None     # {template_id: 行号}
_DOM_OFFSETS = None  # {domain: np.ndarray(行号)}
_ADJ = None        # {template_id: [(theorem_id, weight)]}
_TPL_TEXT = None   # {template_id: text}
_TPL_DOM = None    # {template_id: domain}
_WARM = False


def _get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        torch.set_num_threads(4)
        if not MODEL_DIR or not os.path.isdir(MODEL_DIR):
            print("[warn] 未找到 bge 模型目录：%s；请修改 kg_runtime_graph.py 的 "
                  "MODEL_DIR 或设置环境变量 KG_BGE_MODEL_DIR" % MODEL_DIR,
                  file=sys.stderr)
            _MODEL = None
            return None
        _MODEL = SentenceTransformer(MODEL_DIR, device="cpu")
    except Exception:  # noqa: BLE001
        _MODEL = None
    return _MODEL


def _load_graph():
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH
    if not os.path.exists(GRAPH_OUT):
        return None
    try:
        with open(GRAPH_OUT, encoding="utf-8") as f:
            _GRAPH = json.load(f)
    except Exception:  # noqa: BLE001
        _GRAPH = None
    return _GRAPH


def _embed(text: str) -> np.ndarray:
    m = _get_model()
    if m is None or not text:
        return np.zeros((1, 512), np.float32)
    v = m.encode([text[:800]], normalize_embeddings=True, show_progress_bar=False,
                 convert_to_numpy=True)
    return v.astype(np.float32)


def export_template_embeddings() -> int:
    """构建期导出 problem/derived 模板嵌入到 npy（float16）。幂等。"""
    global _EMB, _IDS
    graph = _load_graph()
    if not graph:
        return 0
    items = [t for t in graph.get("templates", [])
             if t.get("type") in ("problem", "derived") and t.get("text")]
    if not items:
        return 0
    if os.path.exists(EMB_NPY):
        try:
            old = np.load(EMB_NPY, allow_pickle=False)
            if old.shape[0] == len(items):
                _EMB = old
                _IDS = [t["id"] for t in items]
                return len(items)
        except Exception:  # noqa: BLE001
            pass
    m = _get_model()
    if m is None:
        return 0
    texts = [t["text"][:800] for t in items]
    vecs = []
    for i in range(0, len(texts), 24):
        v = m.encode(texts[i:i + 24], normalize_embeddings=True,
                     show_progress_bar=False, convert_to_numpy=True)
        vecs.append(v.astype(np.float32))
    mat = np.vstack(vecs).astype(np.float16)
    np.save(EMB_NPY, mat)
    _EMB = mat
    _IDS = [t["id"] for t in items]
    print(f"[runtime] 已导出 {len(items)} 条模板嵌入 -> {EMB_NPY}")
    return len(items)


def warmup(force: bool = False) -> bool:
    """预热：加载图 + 嵌入 + 预构建索引（供服务启动时调用一次）。返回是否就绪。"""
    global _EMB, _IDS, _ID_POS, _DOM_OFFSETS, _ADJ, _TPL_TEXT, _TPL_DOM, _WARM
    if _WARM and not force:
        return True
    graph = _load_graph()
    if not graph:
        return False
    # 嵌入
    if _EMB is None:
        if os.path.exists(EMB_NPY):
            try:
                _EMB = np.load(EMB_NPY, allow_pickle=False)
            except Exception:  # noqa: BLE001
                _EMB = None
        if _EMB is None:
            export_template_embeddings()
    if _EMB is None:
        return False
    # 行对齐
    items = [t for t in graph.get("templates", [])
             if t.get("type") in ("problem", "derived") and t.get("text")]
    _IDS = [t["id"] for t in items]
    if len(_IDS) != _EMB.shape[0]:
        _EMB = None
        export_template_embeddings()
        _IDS = [t["id"] for t in items]
    _ID_POS = {tid: i for i, tid in enumerate(_IDS)}
    # 域 -> 行号索引
    dom_rows: dict[str, list[int]] = {}
    for i, t in enumerate(items):
        dom_rows.setdefault(t.get("domain", "") or "other", []).append(i)
    _DOM_OFFSETS = {d: np.asarray(v, dtype=np.int64) for d, v in dom_rows.items()}
    # 模板文本 / 域
    _TPL_TEXT = {t["id"]: t.get("text", "") for t in items}
    _TPL_DOM = {t["id"]: t.get("domain", "") for t in items}
    # 模板↔定理邻接表（替代每次线性遍历 edges_t2t）
    adj: dict[str, list] = {}
    for e in graph.get("edges_t2t", []):
        tw = (e.get("theorem"), e.get("weight", 1))
        k = e.get("template")
        if k:
            adj.setdefault(k, []).append(tw)
    _ADJ = adj
    _WARM = True
    return True


def _ensure_ready():
    if not _WARM:
        warmup()
    return _EMB is not None


# ===================== 检索 =====================

def _row_slice(domain: str):
    """返回 (行号数组 or None, 命中说明)。None=全量。"""
    if not domain:
        return None
    rows = _DOM_OFFSETS.get(domain)
    return rows  # 可能为 None（该域无 problem 模板）→ 按全量兜底


def graph_retrieve(problem: str, top_k: int = TOP_K, m: float = THRESHOLD_M,
                   domain: str = ""):
    """Algorithm 1 平替：对查询题嵌入；domain 非空时仅在该域模板子集内点积
    （"识别题型→快速检索经验"场景），无 domain 回退全量。
    返回 [(template_id, sim, dom)]（sim 降序，低于 m 即 break）。
    """
    if not problem:
        return []
    if not _ensure_ready():
        return []
    q = _embed(problem)
    if q is None:
        return []
    qv = q[0].astype(np.float32)
    emb32 = _EMB.astype(np.float32)

    rows = _row_slice(domain)
    if rows is not None and len(rows):
        sub = emb32[rows]
        sims = sub @ qv
        order = rows[np.argsort(-sims)]
        sim_map = dict(zip(rows, sims))
    else:
        sims = emb32 @ qv
        order = np.argsort(-sims)
        sim_map = dict(zip(np.arange(len(sims)), sims))

    out = []
    for pos in order[:top_k]:
        fi = int(pos)
        s = float(sim_map[pos])
        if s < m:
            break  # Algorithm 1：遇到低于阈值即终止返回
        tid = _IDS[fi]
        out.append((tid, round(s, 4), _TPL_DOM.get(tid, "")))
    # 域过滤安全兜底：定域漏检（域内模板都不超阈值）时自动回退全量，
    # 避免"系统定域偏差"导致检索空（如矩阵题被定到相邻域而非最相似域）。
    if not out and rows is not None and len(rows):
        return graph_retrieve(problem, top_k=top_k, m=m, domain="")
    return out


def theorem_table(problem: str, top_k: int = TOP_K, m: float = THRESHOLD_M,
                  limit: int = 5, domain: str = ""):
    """定理表生成：检索 top-k 模板 → 聚合其关联定理，按 sim×边权排序取前 limit。
    返回 [(theorem_id, score)]。"""
    hits = graph_retrieve(problem, top_k=top_k, m=m, domain=domain)
    if not hits:
        return []
    sim_by_tid = {t: s for t, s, _ in hits}
    score = {}
    for tid, s0 in sim_by_tid.items():
        for th, w in _ADJ.get(tid, []):
            s = s0 * w
            if th not in score or s > score[th]:
                score[th] = s
    ranked = sorted(score.items(), key=lambda x: -x[1])
    return ranked[:limit]


def rerank_template(problem: str, theorem_ids: list[str], top_k: int = TOP_K,
                    m: float = THRESHOLD_M, need_overlap: int = 2, domain: str = ""):
    """按定理表回选模板（论文第四步）：候选模板的关联定理 ∩ 定理表 ≥ need_overlap
    才判定"兼容"，返回该模板 id；否则返回 ""（退回单用）。"""
    if not theorem_ids:
        return ""
    hits = graph_retrieve(problem, top_k=top_k, m=m, domain=domain)
    if not hits:
        return ""
    th_set = set(theorem_ids)
    for tid, _s, _dom in hits:
        related = {th for th, _w in _ADJ.get(tid, [])}
        if len(related & th_set) >= need_overlap:
            return tid
    return ""


def graph_retrieve_block(problem: str, max_len: int = 600, domain: str = "") -> str:
    """组装"模板+定理表"联合提示段（供 kg_combined 尾部追加）。失败返回 ""。"""
    try:
        if not problem:
            return ""
        hits = graph_retrieve(problem, domain=domain)
        if not hits:
            return ""
        lines = ["\n\n【模板—定理图谱检索（AAAI-26 图检索增强）】"]
        for i, (tid, sim, dom) in enumerate(hits[:3], 1):
            lines.append(f"{i}. 模板 {tid}（{dom}，相似度 {sim}）：")
            lines.append(_template_text(tid))
        ttab = theorem_table(problem, domain=domain)
        if ttab:
            names = [t for t, _ in ttab]
            lines.append("定理表：" + "、".join(names))
            rt = rerank_template(problem, [t for t, _ in ttab], domain=domain)
            if rt:
                lines.append(f"按定理表回选模板：{rt}")
            else:
                lines.append("模板与定理不兼容 → 回退单用（论文结论）")
        text = "\n".join(lines)
        return text[:max_len]
    except Exception:  # noqa: BLE001
        return ""


def _template_text(tid: str) -> str:
    txt = _TPL_TEXT.get(tid, "")
    if not txt:
        return ""
    graph = _load_graph()
    for t in graph.get("templates", []):
        if t.get("id") == tid:
            steps = t.get("steps")
            if steps:
                txt += "；步骤：" + " → ".join(steps[:5])
            break
    return txt[:200]


def index_stats() -> dict:
    g = _load_graph()
    return {
        "available": g is not None and _ensure_ready(),
        "n_templates_vectors": _EMB.shape[0] if _EMB is not None else 0,
        "n_domains": len(_DOM_OFFSETS) if _DOM_OFFSETS else 0,
        "n_adj": len(_ADJ) if _ADJ else 0,
    }


def graph_stats() -> dict:
    g = _load_graph()
    if not g:
        return {"available": False}
    return {"available": True, **g.get("stats", {})}


if __name__ == "__main__":
    print("索引统计:", index_stats())
    warmup()
    print("预热后:", index_stats())
    for q in ["Find all primes p such that p^2 + 2 is prime.",
              "求 2^2023 除以 7 的余数",
              "求矩阵 [[2,1],[1,2]] 的特征值与特征向量"]:
        print("\n查询:", q[:50])
        print("  全量命中:", graph_retrieve(q)[:3])
        dom = _TPL_DOM.get(graph_retrieve(q)[0][0]) if graph_retrieve(q) else ""
        print("  top1 域:", dom, "| 域过滤命中:", graph_retrieve(q, domain=dom)[:3])