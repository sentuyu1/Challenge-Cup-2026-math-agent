"""
36 题批量评测 — 使用真实 Intern-S1 API
用法: python run_eval.py
"""
import json, os, sys, time
os.environ['INTERN_API_KEY'] = 'sk-ACi6ZnsFxeh3mfI35efkPZSujFiIyoCbDJmmRXKdjYyiFgIC'

from openai import OpenAI

# 加载题目
with open('eval_36_hard.json', encoding='utf-8') as f:
    problems = json.load(f)

# 创建 OpenAI 兼容客户端
client = OpenAI(
    api_key=os.environ['INTERN_API_KEY'],
    base_url='https://chat.intern-ai.org.cn/api/v1/',
)

SYSTEM_PROMPT = """你是一位顶尖的数学教授。请对给定的数学问题进行严格的求解或证明。

要求：
1. 先分析题目类型和核心难点
2. 给出严谨的数学推导或证明过程
3. 涉及计算时写 Python 代码（```python ... ```）
4. 最终答案用 \\boxed{答案} 格式给出
5. 答案要精确、简洁、正确"""

def solve_one(problem: str, idx: int) -> dict:
    """调用 API 解一道题"""
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model='intern-s2-preview',
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': problem},
                ],
                temperature=0.2,
                max_tokens=8192,
            )
            text = resp.choices[0].message.content

            # 提取 \\boxed{}
            m = re.search(r'\\boxed\{(.+?)\}', text)
            if m:
                answer = m.group(1).strip()
            else:
                # 取最后非空行
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                answer = lines[-1][:300] if lines else ''

            return {'success': True, 'answer': answer, 'full': text[:2000], 'tokens': resp.usage.total_tokens if resp.usage else 0}

        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                return {'success': False, 'answer': '', 'full': str(e), 'tokens': 0}

import re

results = []
total_tokens = 0

for i, item in enumerate(problems):
    pid = item['id']
    subject = item['subject']
    problem = item['problem']

    print(f'\n{"="*50}')
    print(f'[{i+1}/36] {pid} [{subject}]')
    print(f'{problem[:120]}...')
    print('='*50)

    t0 = time.time()
    r = solve_one(problem, i)
    elapsed = time.time() - t0
    total_tokens += r['tokens']

    record = {
        'idx': i,
        'id': pid,
        'subject': subject,
        'problem': problem[:200],
        'answer': r['answer'][:500],
        'success': r['success'],
        'elapsed': round(elapsed, 1),
        'tokens': r['tokens'],
    }
    results.append(record)

    with open('eval_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    status = 'OK' if r['success'] else 'FAIL'
    print(f'[{status}] 答案: {r["answer"][:120]}')
    print(f'耗时: {elapsed:.1f}s | tokens: {r["tokens"]} | 累计tokens: {total_tokens}')

    # 限速: 30 RPM → 每 2 秒
    if i < len(problems) - 1:
        time.sleep(2.5)

print(f'\n{"="*50}')
print(f'全部完成! 成功: {sum(1 for r in results if r["success"])}/36')
print(f'总 tokens: {total_tokens}')
print(f'结果: eval_results.json')
