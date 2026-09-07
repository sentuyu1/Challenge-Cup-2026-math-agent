"""ask.py — 本地一键查看某道题的答案。

用法：
    python ask.py 61          # 看 idx 61（用 LaTeX 版题目，走真实评测路径）
    python ask.py 61 --eval   # 用 eval_112 的 Unicode 原文（可能命中 bank）
    python ask.py 0 43 48     # 多题

输出：标准答案 / 系统 final_response / 对错。
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, r"D:\intern-s1-langgraph")
sys.path.insert(0, ".")


def norm(s):
    return re.sub(r'[\s,$\\{}]', '', str(s or '')).strip('。.，')


def judge(our, truth):
    a, b = norm(our), norm(truth)
    if not a or not b:
        return False
    return a == b or (len(a) >= 3 and len(b) >= 3 and (a in b or b in a))


def extract_boxed(text):
    m = re.search(r'\\boxed\{([^}]+)\}', str(text or ''))
    return m.group(1).strip() if m else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    use_eval = '--eval' in sys.argv
    if not args:
        print("用法: python ask.py <idx> 或 python ask.py <idx> --eval")
        return

    aigc = {r['idx']: r for r in (json.loads(l) for l in open('aigc_bank.jsonl', encoding='utf-8'))}
    ev = {i['idx']: i for i in json.load(open('eval_112.json', encoding='utf-8'))}

    from llm_client import InternChatClient
    from user_agent import ReasoningAgent
    agent = ReasoningAgent(client=InternChatClient(timeout=120))

    for idx_str in args:
        idx = int(idx_str)
        truth = ev.get(idx, {}).get('answer', '(无)')
        problem = ev[idx]['problem'] if use_eval else aigc.get(idx, {}).get('problem', '')
        if not problem:
            print(f"idx {idx}: 找不到题目")
            continue
        t0 = time.time()
        try:
            res = agent.solve(problem, {'idx': idx})
            final = res.get('final_response', '')
        except Exception as e:
            final = f"ERROR: {e}"
        dt = time.time() - t0
        ok = judge(final, truth)
        boxed = extract_boxed(final)
        print("=" * 60)
        print(f"idx {idx}  {'✓' if ok else '✗'}  耗时 {dt:.0f}s  (路径: {use_eval and 'eval' or 'aigc-LaTeX'})")
        print(f"标准答案 : {truth}")
        print(f"系统输出 : {final[:200]}")
        print(f"boxed    : {boxed}")
        if len(final) > 200:
            print(f"    …(共 {len(final)} 字符，完整见 final_response)")


if __name__ == "__main__":
    main()