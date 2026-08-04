"""
36 题评测 — 使用 ReasoningAgent（5 Agent + 多候选投票 + 代码反馈环 + thinking mode）

用法: python run_eval_v2.py
"""
import json, os, sys, time

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from user_agent import ReasoningAgent, AgentConfig


# ── 创建模拟平台 client，内部对接 OpenAI 兼容接口 ──
class _EvalClient:
    """仿真平台 client，把 OpenAI 兼容 API 包装成 platform_client.chat() 接口。"""

    def __init__(self):
        from openai import OpenAI
        api_key = os.environ.get('INTERN_API_KEY') or os.environ.get('INTERN_S1_API_KEY', '')
        if not api_key:
            raise RuntimeError('请设置 INTERN_API_KEY 或 INTERN_S1_API_KEY 环境变量')
        self._openai = OpenAI(
            api_key=api_key,
            base_url='https://chat.intern-ai.org.cn/api/v1/',
        )

    def chat(self, messages, temperature=0.2, max_tokens=4096, thinking_mode=False):
        kwargs = dict(
            model='intern-s2-preview',
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=300,  # thinking mode 下可能需要 90+ 秒
        )
        if thinking_mode:
            kwargs['extra_body'] = {'thinking': {'type': 'enabled'}}
        resp = self._openai.chat.completions.create(**kwargs)
        return resp.choices[0].message.content


# ── 加载题目 ──
with open('eval_36_hard.json', encoding='utf-8') as f:
    problems = json.load(f)

# ── 创建 Agent（评测用轻量配置：3 候选 × 2 投票，保证每题 ≤ 15min）──
client = _EvalClient()
config = AgentConfig(
    candidate_count=3,   # 评测用适中的候选数
    vote_count=2,        # 评测用适中的投票数
)
agent = ReasoningAgent(client=client, config=config)

print(f'配置: {config.candidate_count} 候选 × {config.vote_count} 投票, solver temp={config.solver_temperature}')
estimated_calls = config.candidate_count * 2 + config.candidate_count * config.vote_count
estimated_minutes = estimated_calls * 2 / 60
print(f'预估: 每道题 {estimated_calls} 次调用，约 {estimated_minutes:.0f} 分钟/题，总计约 {36 * estimated_minutes / 60:.1f} 小时')
print()

# ── 加载已有结果（断点续跑）──
results = []
if os.path.exists('eval_results_v2.json'):
    try:
        with open('eval_results_v2.json', encoding='utf-8') as f:
            results = json.load(f)
        print(f'已加载 {len(results)} 条已有结果，将从第 {len(results)+1} 题续跑')
    except:
        pass

completed_idx = {r['idx'] for r in results}
total_tokens = 0

for i, item in enumerate(problems):
    if i in completed_idx:
        print(f"\n[跳过] [{i+1}/36] {item['id']} [{item['subject']}] — 已完成")
        continue
    pid = item['id']
    subject = item['subject']
    problem = item['problem']

    print(f'\n{"="*50}')
    print(f'[{i+1}/36] {pid} [{subject}]')
    print(f'{problem[:120]}...')
    print('='*50)

    t0 = time.time()
    try:
        result = agent.solve(problem, {'idx': i})
        elapsed = time.time() - t0

        final_response = result.get('final_response', '')
        trace_steps = len(result.get('trace', []))

        print(f'[OK] 耗时: {elapsed:.1f}s | trace 步骤: {trace_steps}')
        print(f'final_response ({len(final_response)} 字符): {final_response[:200]}...')
    except Exception as e:
        elapsed = time.time() - t0
        final_response = ''
        trace_steps = 0
        print(f'[FAIL] {e}')

    record = {
        'idx': i,
        'id': pid,
        'subject': subject,
        'problem': problem[:200],
        'final_response': final_response[:500],
        'success': bool(final_response),
        'elapsed': round(elapsed, 1),
        'trace_steps': trace_steps,
    }
    results.append(record)

    # 每题后保存
    with open('eval_results_v2.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 限速
    if i < len(problems) - 1:
        time.sleep(2.5)

print(f'\n{"="*50}')
success_count = sum(1 for r in results if r['success'])
print(f'全部完成! 成功: {success_count}/36')
print(f'结果: eval_results_v2.json')
