# -*- coding: utf-8 -*-
"""知识图谱交付包 · 最小可用示例

无需安装任何第三方库（仅标准库 dataclasses/os/json），把本目录整体复制到你的项目即可。

运行：python usage_example.py
"""
import os
import sys

# 保证能 import 本包内的 knowledge_graph.py（即使 cwd 不在本目录）
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from knowledge_graph import retrieve_kg, get_kg_node, all_kg_domains, kg_stats  # noqa: E402
from theorem_kg import theorem_hint, theorem_stats, find_theorems  # noqa: E402


def main():
    print("=" * 60)
    print("知识图谱交付包 · 快速验证")
    print("=" * 60)

    # 1) 有多少题型、有没有题解缓存
    stats = kg_stats()
    print(f"\n[1] 题型节点: {stats['n_nodes']} 个")
    print(f"    有题解缓存的节点: {stats['n_with_cache']} 个")
    print(f"    覆盖题型: {', '.join(stats['domains'])}")

    # 2) 取一个题型的纯方法论节点（不加载扩展题解）
    node = get_kg_node("number_theory")
    print(f"\n[2] 数论节点示例: 方法{len(node.methods)}条 / 定理{len(node.theorems)}条 / "
          f"流程{len(node.flow)}步 / 陷阱{len(node.pitfalls)}条 / 范式{len(node.examples)}条")

    # 3) 检索"方法论 + 缓存真实题解"的提示文本（这就是用来拼进解题 prompt 的内容）
    print("\n[3] 检索 number_theory（含扩展题解参考）→")
    text = retrieve_kg("number_theory", use_extension=True, max_len=1200)
    print("     (提示文本长度", len(text), "字符)")
    print("     是否含『扩展题解参考(缓存)』:", "扩展题解参考" in text)
    print("\n     前 300 字符预览：")
    print("    " + text[:300].replace("\n", "\n    "))

    # 4) 兜底：题型不在表内 / 空 → 返回空串，不报错
    print("\n[4] 兜底检查:")
    print("    retrieve_kg('other')  →", repr(retrieve_kg("other")))
    print("    retrieve_kg('')       →", repr(retrieve_kg("")))
    print("    retrieve_kg('xyz')    →", repr(retrieve_kg("xyz")))

    # 5) 数学定理知识图谱（独立模块，同名异义消歧）
    tstats = theorem_stats()
    print(f"\n[5] 定理知识图谱: 实体 {tstats['n_theorems']} 个 / 同名根 {tstats['n_ambig_groups']} 个")
    print("    用『柯西不等式』检索 → 应命中柯西-施瓦茨（而非积分定理）:")
    k, th = theorem_hint("柯西不等式", domain="linear_algebra")
    for ln in th.split("\n"):
        if "###" in ln:
            print("      " + ln.strip())
    print("    用『柯西积分定理』检索 → 应命中积分定理:")
    k, th = theorem_hint("柯西积分定理", domain="complex_analysis")
    for ln in th.split("\n"):
        if "###" in ln:
            print("      " + ln.strip())

    print("\n完成。图谱已就绪，可直接被你的解题系统调用 retrieve_kg(domain) 注入提示。")


if __name__ == "__main__":
    main()