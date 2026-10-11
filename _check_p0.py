"""P0 改造验证：语法 / 平台 exec 加载 / client 调优 / solve 签名"""
import inspect
import os
import py_compile
import sys

PROJ = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJ)
sys.path.insert(0, PROJ)

ok = True

# ── 1) 语法检查 ──
for f in ("user_agent.py", "client_tuning.py"):
    try:
        py_compile.compile(os.path.join(PROJ, f), doraise=True)
        print(f"[1] 语法 OK: {f}")
    except Exception as e:
        ok = False
        print(f"[1] 语法 FAIL: {f} -> {e}")

# ── 2) 模拟平台 exec() 加载（关键：不设 __file__）──
src = open(os.path.join(PROJ, "user_agent.py"), encoding="utf-8").read()
g = {"__name__": "__platform__"}          # 刻意不放 __file__
try:
    exec(compile(src, "<platform>", "exec"), g)
    print("[2] exec 无 __file__ 加载成功 ✅")
except NameError as e:
    ok = False
    print(f"[2] ❌ NameError（平台加载会整批 invalid）: {e}")
except Exception as e:
    print(f"[2] ⚠️  其它异常 {type(e).__name__}: {e}")

# ── 3) solve 签名默认值 ──
cls = g.get("ReasoningAgent")
if cls is None:
    ok = False
    print("[3] ❌ 未取到 ReasoningAgent")
else:
    p = inspect.signature(cls.solve).parameters
    d = p["metadata"].default
    if d is None:
        print("[3] solve metadata 默认值 = None ✅")
    else:
        ok = False
        print(f"[3] ❌ metadata 默认值异常: {d!r}")

# ── 4) client 调优 ──
from client_tuning import tune_platform_client


class FakeClient:
    def __init__(self):
        self.timeout = 120
        self.retry = 3


class ReadOnlyClient:
    @property
    def timeout(self):
        return 120

    @property
    def retry(self):
        return 3


class NoAttrClient:
    pass


c = FakeClient()
r = tune_platform_client(c)
expect = c.timeout == 780 and c.retry == 1
print(f"[4a] FakeClient(120/3) -> timeout={c.timeout} retry={c.retry} {'✅' if expect else '❌'}  report={r}")
ok &= expect

# 只读属性不能抛异常，且不能改坏
try:
    rc = ReadOnlyClient()
    tune_platform_client(rc)
    print("[4b] 只读属性 client 未抛异常 ✅")
except Exception as e:
    ok = False
    print(f"[4b] ❌ 只读属性 client 抛了异常: {e}")

try:
    tune_platform_client(NoAttrClient())
    tune_platform_client(None)
    print("[4c] 无属性 client / None 未抛异常 ✅")
except Exception as e:
    ok = False
    print(f"[4c] ❌ 抛了异常: {e}")

# 幂等：第二次调用不应把值改坏
tune_platform_client(c)
idem = c.timeout == 780 and c.retry == 1
print(f"[4d] 幂等（重复调优）{'✅' if idem else '❌'} timeout={c.timeout} retry={c.retry}")
ok &= idem

# ── 5) 响应归一化（平台 client 各种返回形态）──
from user_agent import _normalize_chat_response as N


class _ObjResp:
    def __init__(self, content):
        self.content = content


cases = [
    ("str 原样", "hello", "hello"),
    ("OpenAI 兼容", {"choices": [{"message": {"content": "hi"}}]}, "hi"),
    ("choices 无 message", {"choices": [{"content": "direct"}]}, "direct"),
    ("content blocks", {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}, "ab"),
    ("纯 content str", {"content": "hi"}, "hi"),
    ("顶层 list blocks", [{"type": "text", "text": "x"}], "x"),
    ("对象 .content", _ObjResp("obj"), "obj"),
    ("None", None, ""),
    ("数字", 123, "123"),
    ("空 dict", {}, ""),
]

for name, inp, want in cases:
    try:
        got = N(inp)
        okc = got == want
        ok &= okc
        print(f"[5] {'✅' if okc else '❌'} {name:<18} -> {got!r}（期望 {want!r}）")
    except Exception as e:
        ok = False
        print(f"[5] ❌ {name:<18} 抛异常: {type(e).__name__}: {e}")

# 归一化结果必须是 str 且下游 .strip() 可用
try:
    out = N({"choices": [{"message": {"content": "  padded  "}}]})
    assert isinstance(out, str) and out.strip() == "padded"
    print("[5] ✅ 结果类型为 str，.strip() 可用")
except Exception as e:
    ok = False
    print(f"[5] ❌ 结果类型异常: {e}")

# ── 6) 全卷预算池 ──
import time as _t

from paper_pacer import PaperPacer

p = PaperPacer(total_s=21600, planned=112)
b_start = p.budget_for()
c1 = b_start == p.ideal
print(f"[6a] {'✅' if c1 else '❌'} 起步未落后 -> {b_start}s（期望 {p.ideal}）")
ok &= c1

# 严重落后：已做 10 题、已用 5 小时 → 均摊约 35s < 保底 120
p.done = 10
p.t0 = _t.time() - 18000
b_behind = p.budget_for()
c2 = b_behind == p.min_soft
print(f"[6b] {'✅' if c2 else '❌'} 严重落后 -> 保底 {b_behind}s（期望 {p.min_soft}）")
ok &= c2

# 中度落后：速度外推会超 15%，但均摊仍高于保底 → 收紧到均摊值
p2 = PaperPacer(total_s=21600, planned=112)
p2.done = 50
p2.t0 = _t.time() - 12000
b_mid = p2.budget_for()
c3 = p2.min_soft < b_mid < p2.ideal
print(f"[6c] {'✅' if c3 else '❌'} 中度落后 -> 收紧到 {b_mid:.1f}s（应在 {p2.min_soft}~{p2.ideal} 之间）")
ok &= c3

# 进度登记：mark_done 必须计数
p3 = PaperPacer(total_s=21600, planned=112)
p3.mark_started(7)
p3.mark_done()
p3.mark_done()
c4 = p3.done == 2 and 7 in p3._started
print(f"[6d] {'✅' if c4 else '❌'} mark_done/mark_started 计数 -> done={p3.done}")
ok &= c4

# snapshot 可序列化
try:
    snap = PaperPacer(total_s=21600, planned=112).snapshot()
    import json as _json
    _json.dumps(snap)
    print(f"[6e] ✅ snapshot 可 JSON 序列化 {snap}")
except Exception as e:
    ok = False
    print(f"[6e] ❌ snapshot 异常: {e}")

# 单例：get_instance 必须返回同一对象
c5 = PaperPacer.get_instance() is PaperPacer.get_instance()
print(f"[6f] {'✅' if c5 else '❌'} 单例一致性")
ok &= c5

# 并发因子：并发 3 的单题预算应是并发 1 的 3 倍
# （并发 N 时，同一段墙上时间可并行推进 N 道题）
_a = PaperPacer(total_s=21600, planned=112, concurrency=1, min_soft=0)
_a.done, _a.t0 = 50, _t.time() - 12000
_b = PaperPacer(total_s=21600, planned=112, concurrency=3, min_soft=0)
_b.done, _b.t0 = 50, _t.time() - 12000
_ba, _bb = _a.budget_for(), _b.budget_for()
c6 = abs(_bb / _ba - 3.0) < 0.05
ok &= c6
print(f"[6g] {'✅' if c6 else '❌'} 并发因子：c1={_ba:.1f}s c3={_bb:.1f}s（比值应≈3）")

# 实测标定：623s/题 × 112 题 ÷ 并发 3 ≈ 6.46h
# → 起步不落后（给满 ideal），但「均摊」应落在实测 623s 同量级
_c = PaperPacer(total_s=21600, planned=112, concurrency=3)
_per = 21600 * 3 / 112
c7 = _c.budget_for() == _c.ideal and 500 < _per < 700
ok &= c7
print(f"[6h] {'✅' if c7 else '❌'} 起步给满 {_c.budget_for():.0f}s，均摊 {_per:.0f}s/题（实测 623s）")

# 实测标定：真机 3 题并行用 623s（pace≈208s/题）→ 208×112 = 23259s > 21600s
# → 必须判「落后」并收紧，否则池子形同虚设（这就是把容差从 1.15 降到 1.0 的原因）
_d = PaperPacer(total_s=21600, planned=112, concurrency=3, slack=1.0)
_d.done, _d.t0 = 3, _t.time() - 623
_bd = _d.budget_for()
c8 = _bd < _d.ideal
ok &= c8
print(f"[6i] {'✅' if c8 else '❌'} 实测节奏（623s/3题）→ 收紧到 {_bd:.0f}s（应 < {_d.ideal:.0f}）")

print("\n" + ("全部通过 ✅" if ok else "有失败项 ❌"))
sys.exit(0 if ok else 1)
