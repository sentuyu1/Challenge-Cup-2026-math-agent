"""P2 验证：复算裁决 / 契约审计 / 反伪造 / 出厂后处理"""
import os
import py_compile
import sys

PROJ = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJ)
sys.path.insert(0, PROJ)

ok = True

for f in ("playoff.py", "critic_audit.py", "guard.py", "user_agent.py", "utils.py"):
    try:
        py_compile.compile(os.path.join(PROJ, f), doraise=True)
        print(f"[0] 语法 OK: {f}")
    except Exception as e:
        ok = False
        print(f"[0] 语法 FAIL: {f} -> {e}")

from critic_audit import audit_prompt, missing_components, required_components
from guard import authenticity_reason, looks_fabricated_verification
from playoff import parse_verdict, playoff_verify
from utils import execute_code

# ── 1) 裁决解析 ──
verdict_cases = [
    ("PLAYOFF_RESULT: A", "A"),
    ("PLAYOFF_RESULT：B", "B"),
    ("...\n候选A核验: PASS\n候选B核验: FAIL", "A"),
    ("候选A核验: PASS\n候选B核验: PASS", "BOTH"),
    ("候选A核验: FAIL\n候选B核验: FAIL", "NEITHER"),
    ("随便什么输出", "INCONCLUSIVE"),
    ("", "INCONCLUSIVE"),
]
for text, want in verdict_cases:
    got = parse_verdict(text)
    c = got == want
    ok &= c
    print(f"[1] {'✅' if c else '❌'} parse_verdict({text[:26]!r}) -> {got}（期望 {want}）")

# ── 2) 复算裁决端到端（假 ask 产出真代码）──
def _ask_a(prompt):
    return "```python\nprint('候选A核验: PASS')\nprint('候选B核验: FAIL')\nprint('PLAYOFF_RESULT: A')\n```"


def _ask_inconclusive(prompt):
    return "无法机械核验，无可执行代码。"


def _ask_boom(prompt):
    raise RuntimeError("模型调用失败")


v1 = playoff_verify("1+1=?", "2", "3", _ask_a, timeout=20)
c = v1 == "A"
ok &= c
print(f"[2] {'✅' if c else '❌'} 端到端裁决 -> {v1}（期望 A）")

v2 = playoff_verify("1+1=?", "2", "3", _ask_inconclusive, timeout=20)
c = v2 == "INCONCLUSIVE"
ok &= c
print(f"[2] {'✅' if c else '❌'} 无代码 -> {v2}（期望 INCONCLUSIVE）")

v3 = playoff_verify("1+1=?", "2", "3", _ask_boom, timeout=20)
c = v3 == "INCONCLUSIVE"
ok &= c
print(f"[2] {'✅' if c else '❌'} ask 抛异常 -> {v3}（期望 INCONCLUSIVE）")

v4 = playoff_verify("", "2", "3", _ask_a, timeout=20)
c = v4 == "INCONCLUSIVE"
ok &= c
print(f"[2] {'✅' if c else '❌'} 空题面 -> {v4}（期望 INCONCLUSIVE）")

# ── 3) 契约审计 ──
comp_cases = [
    ("求所有正整数 n 的值。", ["enumerate_all"]),
    ("求 f(x) 的最大值。", ["extremum_value"]),
    ("计算 1+1。", []),
]
for prob, want in comp_cases:
    got = required_components(prob)
    c = got == want
    ok &= c
    print(f"[3] {'✅' if c else '❌'} required({prob[:16]!r}) -> {got}（期望 {want}）")

miss_cases = [
    ("求所有正整数 n。", "n=1", ["enumerate_all"], "只给一个 → 缺失"),
    ("求所有正整数 n。", "n = 1, 2, 3", [], "列全了 → 齐全"),
    ("求最大值。", "当 x 取最优时", ["extremum_value"], "无最值 → 缺失"),
    ("求最大值。", "最大值为 5，在 x=2 处取得", [], "有最值 → 齐全"),
]
for prob, ans, want, note in miss_cases:
    got = missing_components(prob, ans)
    c = got == want
    ok &= c
    print(f"[3] {'✅' if c else '❌'} {note:<22} -> {got}")

c = bool(audit_prompt("求所有 n", "n=1", ["enumerate_all"]))
ok &= c
print(f"[3] {'✅' if c else '❌'} audit_prompt 可生成")

# ── 4) 反伪造判定 ──
fab_cases = [
    ("print('验证状态: PASS')", True),
    ("print('验证通过')", True),
    ("assert True", True),
    ("import sympy as sp\nx=sp.Symbol('x')\nprint('验证状态:', 'PASS' if sp.solve(x-1,x)==[1] else 'FAIL')", False),
    ("for i in range(3):\n    assert i < 3\nprint('验证状态: PASS')", False),
    ("print(1+1)", False),
]
for code, want in fab_cases:
    got = looks_fabricated_verification(code)
    c = got == want
    ok &= c
    print(f"[4] {'✅' if c else '❌'} fabricated({code[:34]!r}) -> {got}（期望 {want}）")

# ── 5) execute_code 反伪造拦截 ──
r1 = execute_code("print('验证状态: PASS')", timeout=10)
c = r1.startswith("[反伪造]")
ok &= c
print(f"[5] {'✅' if c else '❌'} 假验证被拦 -> {r1[:36]}...")

GOOD_CODE = ("import sympy as sp\nx=sp.Symbol('x')\n"
             "print('验证状态:', 'PASS' if sp.solve(x-1,x)==[1] else 'FAIL')")
r2 = execute_code(GOOD_CODE, timeout=20)
c = not r2.startswith("[反伪造]") and "PASS" in r2
ok &= c
print(f"[5] {'✅' if c else '❌'} 真验证被放行 -> {r2.strip()[:36]}")

# ── 6) 出厂后处理 _finalize（借用法分支与主流程共用）──
from budget import TimeBudget
from user_agent import ReasoningAgent


class _C:
    timeout = 120
    retry = 3

    def chat(self, *a, **k):
        return "是"


a = ReasoningAgent(client=_C())
tr = []
out = a._finalize("是否存在正整数 n 使得 n² 为偶数？", "是", tr, TimeBudget(500), 0)
steps = [t["step"] for t in tr]
c = out == "是" and "judge_second_vote" in steps and "form_align" in steps
ok &= c
print(f"[6] {'✅' if c else '❌'} 判断题走完三步后处理 -> {out!r} steps={steps}")

tr2 = []
out2 = a._finalize("计算 1+1 的值。", "2", tr2, TimeBudget(500), 1)
steps2 = [t["step"] for t in tr2]
c = out2 == "2" and "critic_audit" in steps2
ok &= c
print(f"[6] {'✅' if c else '❌'} 普通题不误改 -> {out2!r} steps={steps2}")

tr3 = []
out3 = a._finalize("求所有正整数 n 的值。", "n=1", tr3, TimeBudget(500), 2)
c = any(t["step"] == "critic_audit" and t.get("content") == {"missing": ["enumerate_all"]} for t in tr3)
ok &= c
print(f"[6] {'✅' if c else '❌'} 求所有解但只给一个 → 审计报缺 <- {out3!r}")

# ── 7) 异构第二路径（必须挂在真实生效的推理路径上）──
from user_agent import _diverse_hint_for
from utils import execute_code as _ec  # noqa: F401

_h_hard = _diverse_hint_for("求所有正整数 n 的值。")
_h_easy = _diverse_hint_for("计算 1+1。")
c = bool(_h_hard) and "独立第二解法" in _h_hard and _h_easy == ""
ok &= c
print(f"[7] {'✅' if c else '❌'} 异构提示：难题给提示({len(_h_hard)}字) / 简单题不给")

# ── 8) 投票摘录：必须保住末尾的最终答案（原来会被 :3000 砍掉）──
from user_agent import AgentConfig, _vote_excerpt

_short = "推导过程\n\\boxed{7}"
c = _vote_excerpt(_short, 3000) == _short
ok &= c
print(f"[8] {'✅' if c else '❌'} 短解答原样返回")

_long = "A" * 2500 + "中间分析" + "B" * 1000 + "\\boxed{42}"
_exc = _vote_excerpt(_long, 3000)
_has_tail = "\\boxed{42}" in _exc
_has_head = _exc.startswith("A" * 100)
_reasonable = len(_exc) <= 3100
c = _has_tail and _has_head and _reasonable
ok &= c
print(f"[8] {'✅' if c else '❌'} 长解答保留末尾答案（长度 {len(_long)} → {len(_exc)}，末尾仍在={_has_tail}）")

# 对照：原来的 :3000 会丢掉末尾答案
_old = _long[:3000]
c = "\\boxed{42}" not in _old
ok &= c
print(f"[8] {'✅' if c else '❌'} 对照：旧写法确实丢答案（旧摘录含答案={('\\boxed{42}' in _old)}）")

c = AgentConfig().candidate_count == 2
ok &= c
print(f"[8] {'✅' if c else '❌'} candidate_count = {AgentConfig().candidate_count}（期望 2）")

print("\n" + ("P2 验证全部通过 ✅" if ok else "P2 有失败项 ❌"))
sys.exit(0 if ok else 1)
