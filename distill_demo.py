"""本地验证：问题蒸馏输出质量。"""
import json
import sys

sys.path.insert(0, r"D:\intern-s1-langgraph")
sys.path.insert(0, ".")
import problem_distill as pd

ev = {i['idx']: i for i in json.load(open('eval_112.json', encoding='utf-8'))}

from llm_client import InternChatClient
client = InternChatClient(timeout=120)


def chat_fn(prompt):
    return client.chat([{"role": "user", "content": prompt}], temperature=0.1,
                       max_tokens=800, thinking_mode=False)


for idx in [0, 34, 48, 61, 87, 100]:
    p = ev[idx]['problem']
    d = pd.distill_problem(p, chat_fn)
    print(f"===== idx {idx} =====")
    print("题目:", p[:90].replace("\n", " "))
    if d:
        print("  领域:", d.get("domain"))
        print("  结构:", d.get("structure"))
        print("  关键对象:", d.get("key_objects"))
        print("  方法/定理:", d.get("methods"))
    else:
        print("  蒸馏失败")
    print()
