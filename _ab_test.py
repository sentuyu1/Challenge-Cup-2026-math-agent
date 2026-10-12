"""_ab_test.py — 小规模 A/B 对照实验

目的：在**同一批题**上对比两份代码的准确率，回答"这批改动到底有没有用"。

用法（分两次运行，两个独立进程，避免模块缓存串味）：
    python _ab_test.py --tag new                 # 在项目根目录跑当前代码
    python _ab_test.py --tag base --project D:/intern-s1初版_backup_20261011

然后汇总：
    python _ab_test.py --compare                 # 读 _ab_new.json / _ab_base.json 对比

输出：_ab_<tag>.json  {idx: {"answer":..., "correct":bool, "elapsed":float}}
断点续跑：已完成的题不重跑。
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── 固定选题：两组必须完全一致 ──
# 本地并发会互相限流（3 并发实测 3615s/题），故用小样本 + 单并发跑。
PICKS = [18, 36]


def _load_env(project):
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(project, ".env"))
        load_dotenv()
    except Exception:
        pass


def _mk_client():
    from openai import OpenAI
    key = os.environ.get("INTERN_API_KEY") or os.environ.get("INTERN_S1_API_KEY")
    if not key:
        raise RuntimeError("缺少 API key")

    class _Client:
        timeout = 120
        retry = 3

        def __init__(self):
            self._o = OpenAI(api_key=key,
                             base_url="https://chat.intern-ai.org.cn/api/v1/")

        def chat(self, messages, temperature=0.2, max_tokens=4096,
                 thinking_mode=False, model=None):
            r = self._o.chat.completions.create(
                model=model or "intern-s2", messages=messages,
                temperature=temperature, max_tokens=max_tokens)
            return r.choices[0].message.content

    return _Client()


def _norm(s):
    return (s or "").replace(" ", "").replace("$", "").replace("\\", "").strip("。.")


def _judge(client, our, truth):
    """先精确匹配；不等价时用 LLM 判数学等价。"""
    our, truth = (our or "").strip(), (truth or "").strip()
    if not our or not truth:
        return False
    if _norm(our) == _norm(truth):
        return True
    try:
        r = client.chat([{"role": "user", "content": (
            "你是数学答案判分器。判断下面两个答案在数学上是否等价（相同）。\n"
            f"标准答案：{truth}\n模型答案：{our}\n只输出一个字：是 或 否")}],
            temperature=0.0, max_tokens=16)
        return "是" in r and "否" not in r
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="")
    ap.add_argument("--project", default=".")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    # ── 汇总模式 ──
    if args.compare:
        base_p, new_p = "_ab_base.json", "_ab_new.json"
        if not (os.path.exists(base_p) and os.path.exists(new_p)):
            print("缺少 _ab_base.json 或 _ab_new.json")
            return
        b = json.load(open(base_p, encoding="utf-8"))
        n = json.load(open(new_p, encoding="utf-8"))
        idxs = sorted(set(b) & set(n), key=int)
        bo = [i for i in idxs if b[i]["correct"]]
        no = [i for i in idxs if n[i]["correct"]]
        print(f"{'idx':>5} {'base':>6} {'new':>6}   变化")
        for i in idxs:
            bc, nc = b[i]["correct"], n[i]["correct"]
            mark = "  =" if bc == nc else ("  ↑" if nc else "  ↓")
            print(f"{i:>5} {str(bc):>6} {str(nc):>6}{mark}")
        tb, tn = sum(b[i]["elapsed"] for i in idxs), sum(n[i]["elapsed"] for i in idxs)
        print(f"\nbase 正确 {len(bo)}/{len(idxs)}   平均 {tb/len(idxs):.0f}s/题")
        print(f"new  正确 {len(no)}/{len(idxs)}   平均 {tn/len(idxs):.0f}s/题")
        print(f"净变化 {len(no)-len(bo):+d} 题")
        return

    # ── 跑题模式 ──
    project = os.path.abspath(args.project)
    out_path = os.path.abspath(f"_ab_{args.tag}.json")
    os.chdir(project)
    sys.path.insert(0, project)
    _load_env(project)

    data = {i["idx"]: i for i in json.load(open("reference_answers.json", encoding="utf-8"))}
    items = [(i, data[i]) for i in PICKS if i in data and data[i].get("answer")]

    done = {}
    if os.path.exists(out_path):
        try:
            done = json.load(open(out_path, encoding="utf-8"))
        except Exception:
            done = {}
    todo = [(i, d) for i, d in items if str(i) not in done]

    print(f"[{args.tag}] 项目: {project}")
    print(f"[{args.tag}] 共 {len(items)} 题，已完成 {len(items)-len(todo)}，本次跑 {len(todo)}")

    if todo:
        from user_agent import ReasoningAgent
        client = _mk_client()
        agent = ReasoningAgent(client=client)
        lock = __import__("threading").Lock()

        def _one(item):
            i, d = item
            t0 = time.time()
            try:
                r = agent.solve(d["problem"], {"idx": i})
                ans = str(r.get("final_response", ""))
            except Exception as e:
                ans = f"[error] {type(e).__name__}: {e}"
            ok = _judge(client, ans, d["answer"])
            return i, {"answer": ans[:500], "correct": bool(ok),
                       "elapsed": round(time.time() - t0, 1)}

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(_one, it): it[0] for it in todo}
            for f in as_completed(futs):
                i, rec = f.result()
                with lock:
                    done[str(i)] = rec
                    json.dump(done, open(out_path, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=1)
                print(f"  [{args.tag}] idx={i:<4} {'✅' if rec['correct'] else '❌'} "
                      f"{rec['elapsed']:.0f}s", flush=True)

    got = [done[str(i)] for i, _ in items if str(i) in done]
    print(f"\n[{args.tag}] 正确 {sum(1 for g in got if g['correct'])}/{len(got)}"
          f"   平均 {sum(g['elapsed'] for g in got)/max(1,len(got)):.0f}s/题")
    print(f"[{args.tag}] 结果 -> {out_path}")


if __name__ == "__main__":
    main()
