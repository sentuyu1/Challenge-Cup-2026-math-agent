"""导出全量题库 bank_full.jsonl（28096 题，含 idx 字段，供 icma_rag 检索库）。"""
import json
import re
import sqlite3

DB = r"D:\ICMAnew_gitcode\database\chroma.sqlite3"
OUT = "bank_full.jsonl"

con = sqlite3.connect(DB)
cur = con.cursor()
rows = {}
for r in cur.execute("SELECT id, key, string_value, int_value FROM embedding_metadata"):
    rid, key, sv, iv = r
    d = rows.setdefault(rid, {"doc": "", "source": "", "contest": "", "idx": None})
    if key == "chroma:document":
        d["doc"] = sv or ""
    elif key == "source":
        d["source"] = sv or ""
    elif key == "contest":
        d["contest"] = sv or ""
    elif key == "idx":
        d["idx"] = iv

n = 0
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
            "source": d["source"], "contest": d["contest"], "idx": d["idx"],
        }, ensure_ascii=False) + "\n")
        n += 1
print(f"导出 {n} 题 -> {OUT}")
