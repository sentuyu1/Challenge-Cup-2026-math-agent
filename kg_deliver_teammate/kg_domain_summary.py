# -*- coding: utf-8 -*-
"""kg_domain_summary.py — 为 kg_cache 各题型生成"领域方法摘要"（TagRAG 摘要融合思想，规则版）。

背景：TagRAG 论文中"领域标签+摘要融合"是关键收益点（消融证明去掉融合掉点最大）。
本项目 18 题型=根域标签，kg_cache 题解=对象标签，已回填的 method 字段=对象标签摘要。
本脚本用**纯规则**（词频统计+高频方法句）把每 domain 的 method 聚合为 5-8 条领域摘要，
写入 `kg_domain_summary.json`，供 retrieve_kg 注入时追加。

说明：这是对论文"摘要融合"思想的**工程化近似**，非论文原方法（论文用 LLM 融合）。

用法：
  python kg_domain_summary.py                # 生成/覆盖 kg_domain_summary.json
  python kg_domain_summary.py --out PATH     # 指定输出路径
"""
import argparse
import glob
import json
import os
import re
from collections import Counter

DEFAULT_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kg_cache")
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kg_domain_summary.json")

# 中文停用词（方法句里无信息量的虚词/助词）
_STOP = set("的了在是与和用一为可则即于上中下对把被将由从向给以这那其之及或并而但所因此因为如果那么当第个")
# 英文停用词（英文题解的常见虚词）
_EN_STOP = set("the that you and let have for can with this from are was were has had will would "
               "should could using use set not then there where which when what because since so to "
               "of in on at by is be or as but if we it its our your their all any each only also "
               "thus hence therefore may might must than into over about these those such more most".split())
# LaTeX 命令/结构词（无独立数学语义，过滤）
_LATEX_STOP = set("frac dfrac sqrt left right begin end align cdot times sum int infty text mathrm "
                  "quad pm mp leq geq neq approx ldots cdots dots displaystyle operatorname bmatrix "
                  "cases a b c d e f g h i j k l m n o p q r s t u v w x y z".split())


def _method_words(method: str) -> list:
    """从 method 中切出有信息量的词：中文 2-gram + 英文单词。"""
    m = str(method or "")
    words = []
    # 英文单词（去停用词与 LaTeX 命令）
    words += [w for w in re.findall(r"[a-zA-Z]{3,}", m.lower())
              if w not in _EN_STOP and w not in _LATEX_STOP]
    # 中文 2-gram（滑窗）
    zh = re.sub(r"[^\u4e00-\u9fff]", "", m)
    words += [zh[i:i + 2] for i in range(len(zh) - 1) if zh[i] not in _STOP and zh[i + 1] not in _STOP]
    return words


def _summary_for_domain(domain: str, items: list, top_k: int = 8) -> list:
    methods = [str(it.get("method") or "") for it in items if (it.get("method") or "").strip()]
    if not methods:
        return []
    # 1) 高频词统计
    cnt = Counter()
    for m in methods:
        cnt.update(_method_words(m))
    top_words = [w for w, _ in cnt.most_common(12) if len(w) >= 2][:10]
    # 2) 高频方法句：优先含中文的 method 开头片段（英文 LaTeX 句信息量低）
    sent_cnt = Counter()
    for m in methods:
        s = re.sub(r"\s+", " ", m).strip()
        if not s:
            continue
        frag = s[:24]
        if not re.search(r"[\u4e00-\u9fff]", frag):
            continue  # 跳过纯英文/LaTeX 开头
        sent_cnt[frag] += 1
    top_sents = [s for s, _ in sent_cnt.most_common(top_k) if len(s) >= 8]
    lines = []
    if top_words:
        lines.append("高频方法词：" + "、".join(top_words))
    for s in top_sents:
        lines.append(f"- {s}…")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.cache_dir, "*.json")))
    out = {"updated_at": "2026-09-09", "method": "规则聚合（TagRAG 摘要融合思想，非论文原方法）",
           "domains": {}}
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
        domain = data.get("domain_en", os.path.basename(fp)[:-5])
        lines = _summary_for_domain(domain, data.get("items", []))
        if lines:
            out["domains"][domain] = lines
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[完成] {len(out['domains'])} 个题型摘要 → {args.out}")
    for d, lines in list(out["domains"].items())[:3]:
        print(f"  {d}: {lines[0][:60]}")


if __name__ == "__main__":
    main()