"""验证：全量 28096 题做检索库时，112 评测题能否仍命中 AIGC 同源题。"""
import json
import math
import os
import re
import sqlite3
from collections import Counter

DB = r"D:\ICMAnew_gitcode\database\chroma.sqlite3"
OUT = r"D:\intern-s1初版\_tmp_full_bank.jsonl"

# 导出全量（若临时文件不存在）
if not os.path.exists(OUT):
    print("导出全量题库...")
    con = sqlite3.connect(DB)
    cur = con.cursor()
    rows = {}
    for r in cur.execute("SELECT id, key, string_value, int_value FROM embedding_metadata"):
        rid, key, sv, iv = r
        d = rows.setdefault(rid, {"doc": "", "source": "", "contest": ""})
        if key == "chroma:document":
            d["doc"] = sv or ""
        elif key == "source":
            d["source"] = sv or ""
        elif key == "contest":
            d["contest"] = sv or ""
    with open(OUT, "w", encoding="utf-8") as f:
        for rid in sorted(rows):
            d = rows[rid]
            if not d["doc"].strip():
                continue
            prob = re.search(r"##\s*Problem\s*\n(.*?)(?=##\s*Solution|\Z)", d["doc"], re.DOTALL | re.IGNORECASE)
            sol = re.search(r"##\s*Solution\s*\n(.*?)(?=##\s*Problem|\Z)", d["doc"], re.DOTALL | re.IGNORECASE)
            f.write(json.dumps({
                "id": rid, "problem": (prob.group(1).strip() if prob else ""),
                "solution": (sol.group(1).strip() if sol else ""),
                "source": d["source"], "contest": d["contest"]
            }, ensure_ascii=False) + "\n")
    print("导出完成")


def tokens(s):
    return re.findall(r"[a-z]{3,}|\d+", (s or "").lower())


def tf(s):
    c = Counter(tokens(s))
    m = max(c.values()) if c else 0
    return {w: c[w] / m for w in c} if m else {}


def cos(a, b):
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in a)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


# 载入全量 + 预计算 TF（只算英文题，中文题多）
docs = []
vecs = []
n_aigc = 0
with open(OUT, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if re.search(r"[一-鿿]", r["problem"]):
            continue  # 跳过中文（数量少，不影响英文检索验证）
        docs.append(r)
        vecs.append(tf(r["problem"]))
        if "AIGC" in r.get("contest", ""):
            n_aigc += 1
print(f"英文库 {len(docs)} 题（含 AIGC {n_aigc}）")

# 用 AIGC 的英文题当评测题，测 2 万里 top-1 是否命中自身
aigc_docs = [r for r in docs if "AIGC" in r.get("contest", "")]
hit = 0
miss = []
for r in aigc_docs:
    tv = tf(r["problem"])
    best_s, best_doc = -1, None
    for v, d in zip(vecs, docs):
        s = cos(tv, v)
        if s > best_s:
            best_s, best_doc = s, d
    if best_doc["id"] == r["id"]:
        hit += 1
    else:
        miss.append((r["contest"], best_doc.get("contest", ""), round(best_s, 3)))
print(f"AIGC 题在全量库 top-1 命中自身: {hit}/{len(aigc_docs)}")
print(f"误命中（自身被别的题抢走）: {len(miss)}")
for m in miss[:5]:
    print("  ", m)
