"""
重跑 3 道跑偏题目（idx=2,3,6），验证修复效果
"""
import json, os, time
from dotenv import load_dotenv
load_dotenv()

from user_agent import ReasoningAgent, AgentConfig

class _EC:
    def __init__(self):
        from openai import OpenAI
        api_key = os.environ.get('INTERN_API_KEY') or os.environ.get('INTERN_S1_API_KEY', '')
        self._c = OpenAI(api_key=api_key, base_url='https://chat.intern-ai.org.cn/api/v1/')
    def chat(self, messages, temperature=0.2, max_tokens=4096, thinking_mode=False):
        kwargs = dict(model='intern-s2-preview', messages=messages,
                      temperature=temperature, max_tokens=max_tokens, timeout=300)
        if thinking_mode:
            kwargs['extra_body'] = {'thinking': {'type': 'enabled'}}
        return self._c.chat.completions.create(**kwargs).choices[0].message.content

with open('eval_36_hard.json', encoding='utf-8') as f:
    problems = json.load(f)

config = AgentConfig(candidate_count=3, vote_count=2)
agent = ReasoningAgent(client=_EC(), config=config)

results = json.load(open('eval_results_v2.json', encoding='utf-8'))

for idx in [2, 3, 6]:
    item = problems[idx]
    print(f"\n{'='*50}")
    print(f"重跑 [{idx}] {item['id']} [{item['subject']}]")
    print(f"题目: {item['problem'][:100]}")
    print('='*50)
    t0 = time.time()
    result = agent.solve(item['problem'], {'idx': idx})
    elapsed = time.time() - t0
    fr = result['final_response']
    print(f"耗时: {elapsed:.0f}s | final_response: {len(fr)} 字符")
    # 检查是否跑偏
    drifted = any(kw in fr for kw in ['假设题目', '缺少具体的', '没有提供', '如果您有具体'])
    print(f"跑偏检查: {'❌ 仍跑偏' if drifted else '✅ 正常'}")
    print(f"内容预览: {fr[:250]}...")

    for r in results:
        if r['idx'] == idx:
            r['final_response'] = fr[:500]
            r['elapsed'] = round(elapsed, 1)
            r['trace_steps'] = len(result.get('trace', []))
            break

with open('eval_results_v2.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('\n已保存')
