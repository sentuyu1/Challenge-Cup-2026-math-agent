# -*- coding: utf-8 -*-
"""kg_fast_retriever.py — 高效"解题模板—定理图谱"检索器入口（供系统按题型调经验）。

定位：系统完成题型识别（kg_bridge 定域）后，调用本模块在"模板—定理图谱"上
快速检索最相关的解题经验（模板步骤 + 定理 + 定理表 + 回选模板），注入推理 prompt。

用法：
  from kg_fast_retriever import retrieve_experience, warmup, retriever_stats
  hint = retrieve_experience(problem, domain="number_theory")
  # -> 返回检索到的"经验"提示文本；无命中返回 ""

特性（相对旧版优化）：
  - 预构建索引（域→行号 / id→行号 / 模板↔定理邻接表 / 模板文本），一次加载 O(1) 查询
  - 题型域预过滤：只在识别出的 domain 子集内点积（全量 1211→几十），节省排序与内存
  - 首次调用会自动 warmup（加载模型+索引）；服务启动可显式 warmup() 预载，避免首次 13s 卡顿
  - 纯 numpy 零第三方依赖、零 API；全程 try/except 绝对不抛异常
"""
from __future__ import annotations

import os
import sys

__all__ = ["retrieve_experience", "warmup", "retriever_stats"]


def _pipe():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline")
    if p not in sys.path:
        sys.path.insert(0, p)


def warmup(force: bool = False) -> bool:
    """预热（加载图+嵌入+索引+模型）。返回是否就绪。建议服务启动时调用一次。"""
    _pipe()
    from kg_runtime_graph import warmup as _w
    return _w(force=force)


def retrieve_experience(problem: str, domain: str = "", max_len: int = 600) -> str:
    """按题目（+已识别题型 domain）检索"经验"提示段。失败返回 ""。"""
    if not problem:
        return ""
    try:
        _pipe()
        from kg_runtime_graph import graph_retrieve_block
        return graph_retrieve_block(problem, max_len=max_len, domain=domain or "")
    except Exception:  # noqa: BLE001
        return ""


def retriever_stats() -> dict:
    """返回索引状态（向量数/域数/邻接表大小）。"""
    try:
        _pipe()
        from kg_runtime_graph import index_stats
        return index_stats()
    except Exception:  # noqa: BLE001
        return {"available": False}


if __name__ == "__main__":
    import time
    print("索引:", retriever_stats())
    print("预热: warmup() =", warmup())
    qs = [
        ("求 2^2023 除以 7 的余数", "number_theory"),
        ("Find all primes p such that p^2+2 is prime.", "algebra"),
        ("求矩阵 [[2,1],[1,2]] 的特征值与特征向量", "linear_algebra"),
    ]
    for q, d in qs:
        t0 = time.perf_counter()
        h = retrieve_experience(q, domain=d)
        dt = (time.perf_counter() - t0) * 1000
        print(f"\n[题] {q[:40]} (domain={d})  检索耗时 {dt:.0f}ms")
        print(h[:220].replace("\n", " | "))