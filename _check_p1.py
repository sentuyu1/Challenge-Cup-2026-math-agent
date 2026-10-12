"""P1 验证：形态对齐 / 判断题第二票"""
import os
import py_compile
import sys

PROJ = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJ)
sys.path.insert(0, PROJ)

ok = True

# ── 0) 语法 ──
for f in ("form_align.py", "judge_vote.py", "user_agent.py"):
    try:
        py_compile.compile(os.path.join(PROJ, f), doraise=True)
        print(f"[0] 语法 OK: {f}")
    except Exception as e:
        ok = False
        print(f"[0] 语法 FAIL: {f} -> {e}")

from form_align import check_form_alignment, expected_form
from judge_vote import is_judge_problem, normalize_judge_word, second_vote

# ── 1) 题面形态判定 ──
form_cases = [
    ("是否存在正整数 n 使得 n² 为偶数？", "judge"),
    ("求 f(x)=x²-2x 的最大值。", "single"),
    ("求置信区间的长度的一半。", "single"),        # idx=94 那类
    ("求 θ 的 95% 置信区间。", "interval"),
    ("求所有可能的正整数 n。", "enum"),
    ("计算 1+1 的值。", "unknown"),
]
for prob, want in form_cases:
    got = expected_form(prob)
    c = got == want
    ok &= c
    print(f"[1] {'✅' if c else '❌'} {prob[:22]:<24} -> {got}（期望 {want}）")

# ── 2) 形态错配检测 ──
align_cases = [
    ("求 f(x) 的最大值。", "5", True, "单值题给单值"),
    ("求 f(x) 的最大值。", "[1, 5]", False, "单值题却给区间 ← 要拦"),
    ("求置信区间的长度的一半。", "[0.2, 0.8]", False, "问半长却给区间 ← 要拦"),
    ("θ 的 95% 置信区间是多少？", "[0.2, 0.8]", True, "区间题给区间"),
    ("θ 的 95% 置信区间是多少？", "abc", False, "区间题既无区间也无数值 ← 要拦"),
    ("是否存在这样的 n？", "是", True, "判断题给判断词"),
    ("是否存在这样的 n？", "不一定吧", False, "判断题未以判断词开头 ← 要拦"),
    ("计算 1+1。", "2", True, "无强信号不判错"),
]
for prob, ans, want_ok, note in align_cases:
    got_ok, form, why = check_form_alignment(prob, ans)
    c = got_ok == want_ok
    ok &= c
    print(f"[2] {'✅' if c else '❌'} {note:<28} 形态={form} ok={got_ok}")

# ── 3) 判断词归一化 ──
word_cases = [
    ("结论:是", "是"),
    ("结论：否", "否"),
    ("是，因为…", "是"),
    ("否。反例 x=2。", "否"),
    ("不一定", None),
    ("无法判断", None),
    ("", None),
]
for text, want in word_cases:
    got = normalize_judge_word(text)
    c = got == want
    ok &= c
    print(f"[3] {'✅' if c else '❌'} {text[:16]!r:<20} -> {got!r}（期望 {want!r}）")

# ── 4) 是否触发第二票 ──
trig = [
    ("是否存在正整数 n？", "是", True),
    ("是否存在正整数 n？", "42", False),   # 答案不是判断词
    ("计算 1+1。", "是", False),          # 题面不是判断题
]
for prob, ans, want in trig:
    got = is_judge_problem(prob, ans)
    c = got == want
    ok &= c
    print(f"[4] {'✅' if c else '❌'} is_judge_problem({prob[:12]!r}, {ans!r}) -> {got}（期望 {want}）")


# ── 5) second_vote 分歧处理 ──
class FakeAPI:
    def __init__(self, replies):
        self.replies = list(replies)
        self.n = 0

    def chat(self, messages, **kw):
        r = self.replies[min(self.n, len(self.replies) - 1)]
        self.n += 1
        return r


vote_cases = [
    (["结论:是"], "是", False, "第二票一致 → 维持"),
    (["结论:否", "结论:否"], "是", True, "第二票反向 + 第三票同向 → 反转"),
    (["结论:否", "结论:是"], "是", False, "第二票反向、第三票不同 → 维持原判"),
    (["无法解析", ], "是", False, "第二票解析失败 → 维持"),
]
for replies, first, want_rev, note in vote_cases:
    got_ans, got_rev = second_vote("是否存在这样的 n？", first, FakeAPI(replies))
    c = got_rev == want_rev
    ok &= c
    print(f"[5] {'✅' if c else '❌'} {note:<28} 反转={got_rev} 答案={got_ans!r}")


# 异常 api 不得抛异常
class BoomAPI:
    def chat(self, *a, **k):
        raise RuntimeError("boom")


try:
    ans, rev = second_vote("是否存在这样的 n？", "是", BoomAPI())
    c = (ans == "是" and rev is False)
    ok &= c
    print(f"[5] {'✅' if c else '❌'} api 抛异常 → 维持原判（{ans!r}）")
except Exception as e:
    ok = False
    print(f"[5] ❌ api 异常未兜住: {e}")

# ── 6) 限流识别与退避 ──
from user_agent import _is_retryable, _retry_delay, _PlatformLLMAdapter

retry_cases = [
    ("429 Too Many Requests", True),
    ("Rate limit exceeded", True),
    ("quota exceeded", True),
    ("Read timed out", True),
    ("Connection reset by peer", True),
    ("ValueError: bad input", False),
    ("TypeError: unexpected keyword", False),
]
for text, want in retry_cases:
    got = _is_retryable(text)
    c = got == want
    ok &= c
    print(f"[6] {'✅' if c else '❌'} retryable({text[:26]!r}) -> {got}（期望 {want}）")

delay_cases = [("429 rate limit", 1, 15.0), ("busy", 2, 20.0), ("timeout", 1, 1.0), ("timeout", 2, 2.0)]
for text, att, want in delay_cases:
    got = _retry_delay(text, att)
    c = abs(got - want) < 0.01
    ok &= c
    print(f"[6] {'✅' if c else '❌'} delay({text!r}, attempt={att}) -> {got}s（期望 {want}）")


# 重试行为（屏蔽真实 sleep）
class _Flaky:
    timeout = 120
    retry = 3

    def __init__(self, fail_times=1, err="429 rate limit"):
        self.n = 0
        self.fail_times = fail_times
        self.err = err

    def chat(self, *a, **k):
        self.n += 1
        if self.n <= self.fail_times:
            raise RuntimeError(self.err)
        return "ok"


import time as _t2

_real_sleep = _t2.sleep
_t2.sleep = lambda s: None
try:
    fc = _Flaky(fail_times=1)
    ad = _PlatformLLMAdapter(fc)
    out = ad.chat([{"role": "user", "content": "x"}])
    c = out == "ok" and fc.n == 2
    ok &= c
    print(f"[6] {'✅' if c else '❌'} 限流失败 1 次后重试成功（调用 {fc.n} 次）")

    pf = _Flaky(fail_times=99)
    ad2 = _PlatformLLMAdapter(pf)
    try:
        ad2.chat([{"role": "user", "content": "x"}])
        ok = False
        print("[6] ❌ 持续失败时未抛出异常")
    except Exception:
        c = pf.n == 2      # 只重试 1 次就放弃
        ok &= c
        print(f"[6] {'✅' if c else '❌'} 持续限流 → 重试 1 次后放弃（调用 {pf.n} 次）")

    lc = _Flaky(fail_times=99, err="ValueError: 逻辑错误")
    ad3 = _PlatformLLMAdapter(lc)
    try:
        ad3.chat([{"role": "user", "content": "x"}])
    except Exception:
        pass
    c = lc.n == 1          # 逻辑错误不重试
    ok &= c
    print(f"[6] {'✅' if c else '❌'} 非瞬时错误 → 不重试（调用 {lc.n} 次）")
finally:
    _t2.sleep = _real_sleep

# ── 7) 软 / 硬预算分离 ──
from budget import TimeBudget

b = TimeBudget(100.0, reserve_s=20.0)
c = (b.remaining_hard() > 99 and b.remaining() < 81)
ok &= c
print(f"[7] {'✅' if c else '❌'} 软=80 / 硬=100（硬={b.remaining_hard():.0f} 软={b.remaining():.0f}）")

c = abs(b.timeout_for(500) - b.remaining_hard()) < 1.0
ok &= c
print(f"[7] {'✅' if c else '❌'} timeout_for(500) 被钳到硬上限 -> {b.timeout_for(500):.0f}s")

c = abs(b.timeout_for(10) - 10.0) < 0.5
ok &= c
print(f"[7] {'✅' if c else '❌'} timeout_for(10) 不放大 -> {b.timeout_for(10):.0f}s")

b2 = TimeBudget(100.0, reserve_s=20.0)
b2.t0 = _t2.time() - 90
# 已用 90s：硬剩 10s、软剩 -10s（reserve 已用光）
c = (b2.expired(margin=5) and b2.expired(margin=15)
     and not b2.expired(margin=-15) and b2.remaining_hard() > 9)
ok &= c
print(f"[7] {'✅' if c else '❌'} 软硬阈值边界（硬={b2.remaining_hard():.0f} 软={b2.remaining():.0f}）")

# ── 8) 确定性守护（计数 / 模结构）──
from guard import (code_complies_modular, code_has_enumeration, guard_reason,
                   needs_enumeration_guard, needs_modular_guard)
from utils import execute_code

COUNT_Q = "从 5 个球中取 3 个，共有多少种取法？"
CLOSED_CODE = "from math import comb\nprint('最终答案:', comb(5, 3))"
ENUM_CODE = "cnt = 0\nfor i in range(4):\n    cnt += 1\nprint('最终答案:', cnt)"

g_cases = [
    ("计数题识别", needs_enumeration_guard(COUNT_Q), True),
    ("非计数题不识别", needs_enumeration_guard("求 f(x) 的最大值。"), False),
    ("闭式代码无枚举", code_has_enumeration(CLOSED_CODE), False),
    ("循环代码有枚举", code_has_enumeration(ENUM_CODE), True),
    ("itertools 也算枚举", code_has_enumeration("import itertools\nfor c in itertools.combinations(x,2): pass"), True),
    ("模结构+聚合 → 触发", needs_modular_guard("设 f: Q → F_2，求所有 f(x) 之和。"), True),
    ("只有结构无聚合 → 不触发", needs_modular_guard("证明该映射是 F_2 线性的。"), False),
    ("未取模 → 不合规", code_complies_modular("total = sum(vals)"), False),
    ("显式 %2 → 合规", code_complies_modular("total = sum(vals) % 2"), True),
]
for note, got, want in g_cases:
    c = got == want
    ok &= c
    print(f"[8] {'✅' if c else '❌'} {note:<24} -> {got}（期望 {want}）")

r_bad = guard_reason(COUNT_Q, CLOSED_CODE)
r_good = guard_reason(COUNT_Q, ENUM_CODE)
c = bool(r_bad) and not r_good
ok &= c
print(f"[8] {'✅' if c else '❌'} guard_reason：闭式拦截 / 枚举放行")

# 端到端：execute_code 是否真的拦下不合规代码
r1 = execute_code(CLOSED_CODE, timeout=20, problem=COUNT_Q)
c = r1.startswith("[守护拦截]")
ok &= c
print(f"[8] {'✅' if c else '❌'} execute_code 拦下闭式代码 -> {r1[:40]}...")

r2 = execute_code(ENUM_CODE, timeout=20, problem=COUNT_Q)
c = "最终答案" in r2 and not r2.startswith("[守护拦截]")
ok &= c
print(f"[8] {'✅' if c else '❌'} execute_code 放行枚举代码 -> {r2.strip()[:40]}")

r3 = execute_code(CLOSED_CODE, timeout=20)   # 不传 problem → 向后兼容
c = "最终答案" in r3 and not r3.startswith("[守护拦截]")
ok &= c
print(f"[8] {'✅' if c else '❌'} 不传 problem 向后兼容 -> {r3.strip()[:40]}")

# ── 9) 截断检测与续写 ──
from user_agent import _looks_truncated

trunc_cases = [
    ("短文本", "答案 42", 2048, False),
    ("完整长文（以 } 结尾）", "推导" * 200 + "\\boxed{42}", 2048, False),
    ("花括号未闭合", "推导" * 200 + "\\boxed{42", 2048, True),
    ("代码围栏未闭合", "推导" * 200 + "```python\nprint(1)", 2048, True),
    ("顶到上限且无结尾符", "推导" * 400 + "因此我们得到", 512, True),
    ("完整句号结尾", "推导" * 400 + "因此得证。", 512, False),
]
for note, text, mt, want in trunc_cases:
    got = _looks_truncated(text, mt)
    c = got == want
    ok &= c
    print(f"[9] {'✅' if c else '❌'} {note:<20} -> {got}（期望 {want}）")


class _TruncClient:
    """第一次返回被截断的文本（花括号未闭合），第二次返回续写。"""
    timeout = 120
    retry = 3

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.n = 0

    def chat(self, messages, **kw):
        r = self.chunks[min(self.n, len(self.chunks) - 1)]
        self.n += 1
        return r


def _mk(chunks):
    from user_agent import _PlatformLLMAdapter as A
    return A(_TruncClient(chunks))


# 截断 → 触发续写，两段拼接
ad = _mk(["推导" * 200 + "\\boxed{42", "} 这里是续写补上的剩余内容。"])
out = ad.chat([{"role": "user", "content": "题"}], max_tokens=2048)
c = ad._client.n == 2 and out.count("{") == out.count("}")
ok &= c
print(f"[9] {'✅' if c else '❌'} 截断触发续写并拼接（调用 {ad._client.n} 次）")

# 不截断 → 不续写
ad2 = _mk(["推导" * 200 + "\\boxed{42}"])
out2 = ad2.chat([{"role": "user", "content": "题"}], max_tokens=2048)
c = ad2._client.n == 1
ok &= c
print(f"[9] {'✅' if c else '❌'} 完整输出不续写（调用 {ad2._client.n} 次）")

# 短输出（投票场景）不续写
ad3 = _mk(["VERDICT: A"])
out3 = ad3.chat([{"role": "user", "content": "题"}], max_tokens=1024)
c = ad3._client.n == 1 and out3 == "VERDICT: A"
ok &= c
print(f"[9] {'✅' if c else '❌'} 短输出不续写（调用 {ad3._client.n} 次）")

# 续写失败不影响主流程
class _BoomSecond(_TruncClient):
    def chat(self, messages, **kw):
        self.n += 1
        if self.n == 1:
            return "推导" * 200 + "\\boxed{42"
        raise RuntimeError("续写失败")


from user_agent import _PlatformLLMAdapter as _A2
ad4 = _A2(_BoomSecond([]))
out4 = ad4.chat([{"role": "user", "content": "题"}], max_tokens=2048)
c = ad4._client.n == 2 and out4.endswith("\\boxed{42")
ok &= c
print(f"[9] {'✅' if c else '❌'} 续写失败静默降级（调用 {ad4._client.n} 次，原样返回）")

# ── 10) 预填充（省时 + 杜绝该类调用被截断）──
from user_agent import _stitch_prefill
from utils import is_correct_vote

stitch_cases = [
    ("续写", "VERDICT: ", "A", "VERDICT: A"),
    ("回显", "VERDICT: ", "VERDICT: B", "VERDICT: B"),
    ("回显带前置空白", "VERDICT: ", "\nVERDICT: A", "VERDICT: A"),
    ("空种子", "", "任意内容", "任意内容"),
]
for note, seed, comp, want in stitch_cases:
    got = _stitch_prefill(seed, comp)
    c = got == want
    ok &= c
    print(f"[10] {'✅' if c else '❌'} stitch {note:<14} -> {got!r}（期望 {want!r}）")


class _PreClient:
    def __init__(self, reply):
        self.reply = reply
        self.n = 0
        self.last_msgs = None

    def chat(self, messages, **kw):
        self.n += 1
        self.last_msgs = messages
        return self.reply


from user_agent import _PlatformLLMAdapter as _A3

pc = _PreClient("A")
adp = _A3(pc)
out = adp.chat_prefilled([{"role": "user", "content": "判断"}], "VERDICT: ")
c = out == "VERDICT: A" and pc.n == 1
ok &= c
print(f"[10] {'✅' if c else '❌'} chat_prefilled 续写拼接 -> {out!r}（调用 {pc.n} 次）")

c = isinstance(pc.last_msgs, list) and pc.last_msgs[-1] == {"role": "assistant", "content": "VERDICT: "}
ok &= c
print(f"[10] {'✅' if c else '❌'} 末尾确实追加了 assistant 种子消息")

c = is_correct_vote(out) is True
ok &= c
print(f"[10] {'✅' if c else '❌'} 预填充结果可被投票解析 -> {is_correct_vote(out)}")

print("\n" + ("P1 验证全部通过 ✅" if ok else "P1 有失败项 ❌"))
sys.exit(0 if ok else 1)
