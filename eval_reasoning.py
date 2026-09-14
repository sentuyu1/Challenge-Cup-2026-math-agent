"""eval_reasoning.py — 实测「真实推理」能力基线（关题海 bank/borrow/权威校正）。

用法：MATH_AGENT_BORROW=0 python eval_reasoning.py [--limit N] [--start IDX]
判分：aigc(LaTeX) 题走完整推理 → 提取 boxed → 宽松等价 vs eval_112 标准答案。
断点续跑存 progress 文件。默认关 deterministic 之外的题海。
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.environ.get("AUX_PATH", "."))
sys.path.insert(0, ".")

os.environ["MATH_AGENT_BORROW"] = "0"   # 关题库查表 + 借用改写（测真实推理）
os.environ["MATH_AGENT_RAG"] = "0"      # 关相似题检索（不加载全量库，省内存）
os.environ["MATH_AGENT_THINKING"] = "off"  # 本地关 deep thinking（防 397B 长思考截断成空答案）
# 真实能力全开：skill 手册 + 知识图谱 + Python 验证 + Finalizer 判分保护
os.environ["MATH_AGENT_SKILL"] = "1"
os.environ["MATH_AGENT_GRAPH"] = "1"
os.environ["MATH_AGENT_PYTHON"] = "1"
os.environ["MATH_AGENT_FINALIZER"] = "1"
# deterministic_solver 是「确定性代码解」，属真实能力资产，保留

PROGRESS = "eval_reasoning_progress.json"


def norm(s):
    return re.sub(r'[\s,$\\{}]', '', str(s or '')).strip('。.，')


def extract_boxed(text):
    m = re.search(r'\\boxed\{([^{}]+)\}', str(text or ''))
    return m.group(1).strip() if m else None


def judge(our, truth):
    boxed = extract_boxed(our) or our
    a, b = norm(boxed), norm(truth)
    if not a or not b:
        return False
    return a == b or (len(a) >= 3 and len(b) >= 3 and (a in b or b in a))


def main():
    limit = None
    idxs = None
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            limit = int(a.split("=")[1])
        elif a.startswith("--idx="):
            idxs = [int(x) for x in a.split("=")[1].split(",")]

    aigc = [json.loads(l) for l in open('knowledge_bank.jsonl', encoding='utf-8')]
    ev = {i['idx']: i for i in json.load(open('reference_answers.json', encoding='utf-8'))}
    if idxs:
        items = [r for r in aigc if r['idx'] in idxs]
    elif limit:
        items = aigc[:limit]
    else:
        items = aigc

    progress = {}
    if os.path.exists(PROGRESS):
        try:
            progress = json.load(open(PROGRESS, encoding='utf-8'))
        except Exception:
            progress = {}
    todo = [r for r in items if str(r['idx']) not in progress]
    print(f"待跑 {len(todo)} 题（共 {len(items)}）", flush=True)

    from llm_client import InternChatClient
    from user_agent import ReasoningAgent

    agent = ReasoningAgent(client=InternChatClient(timeout=180))

    def solve_one(r, idx):
        last = None
        for attempt in range(2):  # 本地网络不稳，重试 2 次
            try:
                res = agent.solve(r['problem'], {'idx': idx})
                return res.get('final_response', '')
            except Exception as e:
                last = e
                time.sleep(3)
        return f"ERROR: {last}"

    t_start = time.time()
    for i, r in enumerate(todo):
        idx = r['idx']
        t0 = time.time()
        final = solve_one(r, idx)
        truth = ev[idx]['answer']
        ok = judge(final, truth) if not final.startswith("ERROR") else False
        dt = time.time() - t0
        progress[str(idx)] = {"ok": ok, "our": final[:150], "truth": truth, "elapsed": round(dt, 1)}
        json.dump(progress, open(PROGRESS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        corr = sum(1 for x in progress.values() if x.get("ok"))
        print(f"[{idx:>3}] {'✓' if ok else '✗'} boxed={extract_boxed(final)!r} truth={truth!r} {dt:.0f}s ({len(progress)}/{len(items)} 对{corr})", flush=True)

    total = len(progress)
    corr = sum(1 for x in progress.values() if x["ok"])
    print(f"\n=== 纯推理基线（关题海）：{corr}/{total} = {corr/total*100:.1f}% ===", flush=True)


if __name__ == "__main__":
    main()
