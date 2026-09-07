"""eval_37.py — 跑前 37 题（idx 0-36）评测，为错题驱动迭代提供错题数据。

用法：INTERN_API_KEY=xxx python -u eval_37.py
每题输出：答案 vs 标准 + 耗时，实时写盘 eval_37_progress.json（断点续跑）。
"""
import json
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, r"D:\intern-s1-langgraph")  # 供 llm_client 等（不覆盖 user_agent）
sys.path.insert(0, ".")  # Lagent 版优先（user_agent 从这里加载）

from llm_client import InternChatClient
from user_agent import ReasoningAgent
from utils import extract_final_answer

_judge_client = None


def judge(our, truth):
    global _judge_client
    our = (our or "").strip()
    t = (truth or "").strip()
    if not our or not t:
        return False

    def _norm(s):
        return s.replace(" ", "").replace("$", "").replace("\\", "").strip("。.")
    if _norm(our) == _norm(t):
        return True
    if _judge_client is None:
        _judge_client = InternChatClient(timeout=60)
    prompt = (
        "你是数学答案判分器。判断下面两个答案在数学上是否等价（相同）。\n"
        f"标准答案：{t}\n"
        f"模型答案：{our}\n"
        "只输出一个字：是 或 否"
    )
    try:
        resp = _judge_client.chat([{"role": "user", "content": prompt}], temperature=0.0, max_tokens=16)
        return "是" in resp and "否" not in resp
    except Exception:
        return False


PROGRESS = "eval_37_progress.json"


def main():
    data = json.load(open(r"D:\intern-s1-langgraph\eval_112.json", encoding="utf-8"))
    items = [i for i in data[:37] if i.get("answer") and i.get("problem")]

    progress = {}
    if os.path.exists(PROGRESS):
        try:
            progress = json.load(open(PROGRESS, encoding="utf-8"))
        except Exception:
            progress = {}
    todo = [i for i in items if str(i["idx"]) not in progress]
    print(f"待跑 {len(todo)} 题（共 {len(items)} 题）", flush=True)

    agents = threading.local()

    def get_agent():
        if not hasattr(agents, "agent"):
            agents.agent = ReasoningAgent(client=InternChatClient(timeout=60))
        return agents.agent

    def solve_one(item):
        idx = item["idx"]
        t0 = time.time()
        try:
            result = get_agent().solve(item["problem"], {"idx": idx})
            final = result.get("final_response", "")
            our = extract_final_answer(final) or final
        except Exception as e:
            our = f"ERROR: {e}"
        dt = time.time() - t0
        ok = judge(our, item["answer"])
        return {"idx": idx, "ok": ok, "our": our[:200], "truth": item["answer"], "elapsed": round(dt, 1)}

    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(solve_one, item): item for item in todo}
        for fut in as_completed(futs):
            r = fut.result()
            with lock:
                progress[str(r["idx"])] = r
                json.dump(progress, open(PROGRESS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            correct = sum(1 for x in progress.values() if x.get("ok"))
            print(f"[{r['idx']:>3}] {'✅' if r['ok'] else '❌'} 答案={r['our'][:50]!r} 标准={r['truth'][:40]!r} {r['elapsed']:.0f}s ({len(progress)}/{len(items)} 对{correct})", flush=True)

    total = len(progress)
    correct = sum(1 for r in progress.values() if r["ok"])
    print(f"\n=== 前 37 题判分：{correct}/{total} = {correct/total*100:.1f}% ===", flush=True)
    wrong = sorted(r["idx"] for r in progress.values() if not r["ok"])
    print(f"错题：{wrong}", flush=True)


if __name__ == "__main__":
    main()
