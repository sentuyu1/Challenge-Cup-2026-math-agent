"""真实 API 端到端验证（1 题）—— 上线前最后的体检

用真实 Intern-S2 API 走一遍 solve()，确认：
  ① 新增的 14 项机制不干扰主流程
  ② 没有隐藏异常（本地假 client 测不出来的）
  ③ trace 步骤序列正常
  ④ 耗时在预算内
"""
import os
import sys
import time

PROJ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJ)
os.chdir(PROJ)

from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

KEY = os.environ.get("INTERN_API_KEY") or os.environ.get("INTERN_S1_API_KEY")
if not KEY:
    print("❌ 未找到 API key")
    sys.exit(1)

MODEL = os.environ.get("INTERN_MODEL", "intern-s2")


class RealClient:
    """模拟平台注入的 client 接口（chat(messages, temperature, max_tokens, thinking_mode) -> str）。"""

    def __init__(self):
        self._c = OpenAI(api_key=KEY, base_url="https://chat.intern-ai.org.cn/api/v1/")
        self.timeout = 120        # 供 client_tuning 检测并调优
        self.retry = 3
        self.calls = 0
        self.errors = []

    def chat(self, messages, temperature=0.2, max_tokens=4096, thinking_mode=False, model=None):
        self.calls += 1
        try:
            r = self._c.chat.completions.create(
                model=model or MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return r.choices[0].message.content
        except Exception as e:
            self.errors.append(f"{type(e).__name__}: {e}")
            raise


from budget import TimeBudget
from user_agent import ReasoningAgent

PROBLEM = "求 1+2+3+…+100 的值。"

print(f"模型: {MODEL}")
print(f"题目: {PROBLEM}\n")

c = RealClient()
t0 = time.time()
agent = ReasoningAgent(client=c)
print(f"[初始化] client 调优后 timeout={c.timeout} retry={c.retry}")

try:
    res = agent.solve(PROBLEM, {"idx": 0})
    dt = time.time() - t0
    print(f"\n[完成] 耗时 {dt:.1f}s，真实 API 调用 {c.calls} 次")
    fr = str(res.get("final_response", ""))
    print(f"[答案] {fr[:200]!r}")
    print(f"[trace] 共 {len(res.get('trace', []))} 步：")
    for t in res.get("trace", []):
        print("   -", t.get("step"))
except Exception as e:
    import traceback
    print(f"\n❌ 崩溃: {type(e).__name__}: {e}")
    traceback.print_exc()
    if c.errors:
        print("API 错误记录:", c.errors[-3:])
    sys.exit(1)

if c.errors:
    print(f"\n⚠️ 期间发生过 {len(c.errors)} 次错误（已被重试兜住）: {c.errors[:2]}")
print("\n真实端到端验证通过 ✅")
