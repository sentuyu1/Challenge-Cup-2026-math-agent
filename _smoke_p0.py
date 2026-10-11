"""P0 冒烟：用假 client 走完一次 solve，确认不崩、返回结构正确"""
import os
import sys

PROJ = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJ)
sys.path.insert(0, PROJ)

from user_agent import ReasoningAgent


class FakeClient:
    """假平台 client：永远返回一个带 \\boxed 的完整四段式回答。"""
    timeout = 120          # 供 client_tuning 调优
    retry = 3

    def chat(self, messages, **kwargs):
        return (
            "## 问题分析\n这是一道简单加法题。\n"
            "## 详细解题步骤\n1. 由加法定义，1+1=2。\n"
            "## 最终答案\n\\boxed{2}\n"
            "## 关键验证点\n2-1=1，正确。"
        )


results = []

# ① 正常传 metadata
try:
    a = ReasoningAgent(client=FakeClient())
    r = a.solve("1+1=?", {"idx": 0})
    ok = isinstance(r, dict) and bool(str(r.get("final_response", "")).strip())
    results.append(("正常 metadata", ok, str(r.get("final_response"))[:60], r.get("trace") is not None))
except Exception as e:
    results.append(("正常 metadata", False, f"{type(e).__name__}: {e}", False))

# ② 不传 metadata（平台真实调用形态）—— 曾经的 TypeError 现场
try:
    a = ReasoningAgent(client=FakeClient())
    r = a.solve("1+1=?")
    ok = isinstance(r, dict) and bool(str(r.get("final_response", "")).strip())
    results.append(("缺省 metadata", ok, str(r.get("final_response"))[:60], r.get("trace") is not None))
except TypeError as e:
    results.append(("缺省 metadata", False, f"❌ TypeError（整批 error）: {e}", False))
except Exception as e:
    results.append(("缺省 metadata", False, f"{type(e).__name__}: {e}", False))

# ③ metadata 传 None
try:
    a = ReasoningAgent(client=FakeClient())
    r = a.solve("1+1=?", None)
    ok = isinstance(r, dict) and bool(str(r.get("final_response", "")).strip())
    results.append(("metadata=None", ok, str(r.get("final_response"))[:60], r.get("trace") is not None))
except Exception as e:
    results.append(("metadata=None", False, f"{type(e).__name__}: {e}", False))

# ④ client 调优是否生效
try:
    fc = FakeClient()
    ReasoningAgent(client=fc)
    tuned = (fc.timeout == 780 and fc.retry == 1)
    results.append(("client 已被调优", tuned, f"timeout={fc.timeout} retry={fc.retry}", True))
except Exception as e:
    results.append(("client 已被调优", False, f"{type(e).__name__}: {e}", False))


class BlockClient:
    """模拟官方 client 返回 OpenAI content blocks 结构（历史事故：全题 invalid）。"""
    timeout = 120
    retry = 3

    def chat(self, messages, **kwargs):
        return {"content": [{"type": "text", "text": "## 问题分析\nok\n## 最终答案\n\\boxed{2}"}]}


# ⑤ 平台 client 返回 content blocks 形态
try:
    a = ReasoningAgent(client=BlockClient())
    r = a.solve("1+1=?", {"idx": 0})
    ok = isinstance(r, dict) and bool(str(r.get("final_response", "")).strip())
    results.append(("content blocks 形态", ok, str(r.get("final_response"))[:60], r.get("trace") is not None))
except Exception as e:
    results.append(("content blocks 形态", False, f"{type(e).__name__}: {e}", False))


class OpenAICompatClient:
    """模拟 OpenAI 兼容 dict 形态。"""
    timeout = 120
    retry = 3

    def chat(self, messages, **kwargs):
        return {"choices": [{"message": {"content": "## 最终答案\n\\boxed{2}"}}]}


# ⑥ 平台 client 返回 OpenAI 兼容 dict 形态
try:
    a = ReasoningAgent(client=OpenAICompatClient())
    r = a.solve("1+1=?", {"idx": 0})
    ok = isinstance(r, dict) and bool(str(r.get("final_response", "")).strip())
    results.append(("OpenAI 兼容形态", ok, str(r.get("final_response"))[:60], r.get("trace") is not None))
except Exception as e:
    results.append(("OpenAI 兼容形态", False, f"{type(e).__name__}: {e}", False))


# ⑦ 全卷预算：solve 跑完必须登记进度（成功 / 失败都要计）
from paper_pacer import PaperPacer

_p = PaperPacer.get_instance()
_before = _p.done
try:
    a = ReasoningAgent(client=FakeClient())
    a.solve("1+1=?", {"idx": 99})
    ok = _p.done == _before + 1
    results.append(("全卷进度登记", ok, f"done {_before} -> {_p.done}，budget={_p.budget_for():.0f}s", True))
except Exception as e:
    results.append(("全卷进度登记", False, f"{type(e).__name__}: {e}", False))

# ⑧ 异常路径也必须登记（solve 内部抛错时通过 finally 计数）
_before2 = _p.done
try:
    class BoomClient:
        timeout = 120
        retry = 3

        def chat(self, *a, **k):
            raise RuntimeError("模拟平台侧崩溃")

    a = ReasoningAgent(client=BoomClient())
    r = a.solve("1+1=?", {"idx": 98})
    ok = _p.done == _before2 + 1 and isinstance(r, dict)
    results.append(("异常路径仍登记", ok, f"done {_before2} -> {_p.done}，final={str(r.get('final_response'))[:20]!r}", r.get("trace") is not None))
except Exception as e:
    results.append(("异常路径仍登记", False, f"❌ 未兜住: {type(e).__name__}: {e}", False))

print()
allok = True
for name, ok, detail, has_trace in results:
    flag = "✅" if ok else "❌"
    allok &= ok
    print(f"{flag} {name:<18} trace={'有' if has_trace else '无'}  {detail[:70]}")

print("\n" + ("冒烟通过 ✅" if allok else "冒烟有失败 ❌"))
sys.exit(0 if allok else 1)
