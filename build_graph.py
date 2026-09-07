"""build_graph.py — 从 18 学科 skill 手册构建定理/知识图谱（knowledge_graph.json）。

节点分层：
  学科层（18）：离散数学 / 高等代数 / 复分析 …
  知识点层：各手册的「## N. 模块标题」（如「数论基础：扩展欧几里得算法」）
边：学科 → 知识点（contains）
跨学科关系：后续可人工补充（图谱数据手工可编辑，JSON 格式开放）。
"""
import json
import os
import re
from pathlib import Path

SKILLS = Path(__file__).resolve().parent / "skills_pythonscripts"
OUT = Path(__file__).resolve().parent / "knowledge_graph.json"

# 通用章 / 强工具型模块（非纯数学知识点，不入选图谱节点）
_SKIP_HEAD = re.compile(
    r"领域边界|路由约定|前言|通用解题方法论|习题|索引|模块速查|附录|参考资源|常见错误|"
    r"sympy|验证|工具|目录|使用边界|竞赛拓展|速查表|标准解法|标准策略|通用建模|解题思路索引|"
    r"概述|知识点体系|知识模块|兼容口径|高频错误"
)

# 模块前缀：## 1. / ## 一、/ ### 模块1：/ ## 第一部分： 等
_PREFIX_RE = re.compile(
    r"^(?:模块\s*\d*\s*[：:]\s*|\d+\s*[.)、:：\-]\s*|[一二三四五六七八九十]+\s*[、.)：:\-]\s*|"
    r"第[一二三四五六七八九十]+部分[：:]\s*)"
)


def clean_title(line: str) -> str:
    s = line.rstrip()
    if s.startswith("### "):
        body = s[4:]
    elif s.startswith("## "):
        body = s[3:]
    else:
        return ""
    body = _PREFIX_RE.sub("", body).strip().strip("：:")
    if not body or _SKIP_HEAD.search(body):
        return ""
    return body


def main():
    nodes = []   # 知识点节点（学科为根节点不单独列，edges 指向学科字符串）
    edges = []
    counts = {}
    for disc_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        md = disc_dir / f"{disc_dir.name}skill.md"
        if not md.exists():
            continue
        topics = []
        for line in md.read_text(encoding="utf-8").splitlines():
            title = clean_title(line)
            if not title or _SKIP_HEAD.search(title):
                continue
            topics.append(title)
        # 去重保序
        seen = set()
        uniq = []
        for t in topics:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        for t in uniq:
            nid = f"{disc_dir.name}/{t}"
            nodes.append({"id": nid, "name": t, "discipline": disc_dir.name})
            edges.append({"from": disc_dir.name, "to": nid, "relation": "contains"})
        counts[disc_dir.name] = len(uniq)

    graph = {
        "disciplines": sorted(counts.keys()),
        "nodes": nodes,
        "edges": edges,
        "meta": {"node_count": len(nodes), "edge_count": len(edges), "per_discipline": counts},
    }
    OUT.write_text(json.dumps(graph, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"图谱已生成 -> {OUT}")
    print(f"学科 {len(graph['disciplines'])} 个, 知识点节点 {len(nodes)}, 边 {len(edges)}")
    for d, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {d}: {n} 知识点")


if __name__ == "__main__":
    main()
