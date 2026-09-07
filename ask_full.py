"""本地跑一道简单题，完整打印解题过程（含重试）。用法：python ask_full.py <idx>"""
import json
import sys
import time

sys.path.insert(0, r"D:\intern-s1-langgraph")
sys.path.insert(0, ".")


def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    aigc = [json.loads(l) for l in open('aigc_bank.jsonl', encoding='utf-8')]
    ev = {i['idx']: i for i in json.load(open('eval_112.json', encoding='utf-8'))}
    truth = ev[idx]['answer']
    r = next((x for x in aigc if x['idx'] == idx), None)
    print(f"题目（LaTeX 版）: {(r['problem'][:150] if r else '(无)')} ...")
    print(f"标准答案: {truth}")
    print("=" * 60)

    from llm_client import InternChatClient
    from user_agent import ReasoningAgent

    last_err = None
    for attempt in range(3):
        try:
            agent = ReasoningAgent(client=InternChatClient(timeout=120))
            res = agent.solve(r['problem'], {'idx': idx})
            final = res.get('final_response', '')
            print(f"trace 步骤: {[t.get('step') for t in res['trace']]}")
            print(f"final_response 长度: {len(final)}")
            print("=" * 60)
            print(final if final else "(空)")
            return
        except Exception as e:
            last_err = e
            print(f"[第{attempt+1}次失败] {type(e).__name__}: {str(e)[:100]}")
            time.sleep(3)
    print(f"3 次都失败: {last_err}")


if __name__ == "__main__":
    main()