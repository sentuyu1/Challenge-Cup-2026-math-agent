"""playoff.py — 确定性复算裁决

════════════════════════════════════════════════════════
  推理答案 A ┐
             ├─→ 让模型写一段「只做核验」的代码
  Python答案 B ┘        （不重新解题！）
                          │
                          ▼
                   代回原题复算 / 小规模枚举 / 实测比较
                          │
                          ▼
              PLAYOFF_RESULT: A | B | BOTH | NEITHER | INCONCLUSIVE
════════════════════════════════════════════════════════

为什么需要：
  两条独立路径给出不同答案时，原来的做法是「无条件信代码」。但代码也会错——
  常见于：题面数据缺失时自行补全、把连续问题离散近似、计数题闭式公式边界算错。
  此时代码答案会**直接覆盖正确的推理答案**，把本该拿到的一分丢掉。

  「季后赛」的做法是：不重新解题，只写一段**核验代码**把两个候选都代回原题，
  用确定性证据裁决——比"再采样一次让模型选"可靠得多。

判定语义：
  A            → 候选 A（推理答案）通过核验
  B            → 候选 B（代码答案）通过核验
  BOTH         → 两者等价（都通过）
  NEITHER      → 两者都被证伪（此时应由调用方回炉重解）
  INCONCLUSIVE → 无法机械核验（证明题、数据缺失等）

安全约束：任何异常 / 解析失败一律返回 INCONCLUSIVE，由调用方沿用原有行为。
"""

from __future__ import annotations

import re

_RESULT_RE = re.compile(r"PLAYOFF_RESULT\s*[:：]\s*(A|B|BOTH|NEITHER|INCONCLUSIVE)", re.IGNORECASE)
_PASS_LINE_RE = re.compile(r"候选\s*([AB])\s*核验\s*[:：]\s*(PASS|FAIL|通过|不通过)", re.IGNORECASE)


def build_prompt(problem: str, cand_a: str, cand_b: str) -> str:
    """构造核验代码的生成提示词。"""
    return (
        "你是 Python 数值核验专家。下面是一道数学题和两个互相矛盾的候选答案。\n"
        "**不要重新解题**，只写一段**确定性核验代码**来判断哪个答案是对的。\n\n"
        "核验手段（按题目类型选择）：\n"
        "- 方程/根：把候选代回原方程，化简残差，看哪个为零\n"
        "- 极值：算出目标函数的实际取值，与候选值比较\n"
        "- 计数：把规模缩到 n≤8 或网格 ≤6×6，暴力枚举逐点核对\n"
        "- 存在性：实际搜索并构造出实例\n"
        "- 若无法机械核验（证明题、题面数据缺失），直接输出 INCONCLUSIVE\n\n"
        "要求：\n"
        "1. 只输出一个 ```python``` 代码块，代码块之外不要写解释\n"
        "2. 代码必须打印两行：`候选A核验: PASS` 或 `候选A核验: FAIL`，"
        "候选B同理\n"
        "3. 最后一行必须打印：`PLAYOFF_RESULT: A` / `B` / `BOTH` / `NEITHER` / `INCONCLUSIVE`\n"
        "4. 不要写 print('PASS') 这类没有计算的假核验，必须真的算\n\n"
        f"题目：\n{problem}\n\n"
        f"候选 A：{cand_a}\n\n"
        f"候选 B：{cand_b}\n"
    )


def parse_verdict(output: str) -> str:
    """从执行输出里解析裁决；解析不出返回 INCONCLUSIVE。"""
    text = output or ""
    m = _RESULT_RE.findall(text)
    if m:
        return m[-1].upper()

    # 退化：由「候选X核验: PASS/FAIL」行推断
    verdicts = {k.upper(): v.upper() for k, v in _PASS_LINE_RE.findall(text)}
    a_ok = verdicts.get("A", "").startswith(("PASS", "通过"))
    b_ok = verdicts.get("B", "").startswith(("PASS", "通过"))
    a_seen = "A" in verdicts
    b_seen = "B" in verdicts
    if a_seen and b_seen:
        if a_ok and b_ok:
            return "BOTH"
        if a_ok:
            return "A"
        if b_ok:
            return "B"
        return "NEITHER"
    return "INCONCLUSIVE"


def playoff_verify(problem: str, cand_a: str, cand_b: str, ask, timeout: int = 30) -> str:
    """执行一次复算裁决。

    参数：
      ask: callable(prompt) -> str，负责让模型产出核验代码
      timeout: 代码执行超时

    返回：A / B / BOTH / NEITHER / INCONCLUSIVE
    任何异常都返回 INCONCLUSIVE（调用方据此沿用原有行为）。
    """
    if not problem or not cand_a or not cand_b:
        return "INCONCLUSIVE"
    try:
        from utils import execute_code, extract_code
        raw = ask(build_prompt(problem, cand_a, cand_b))
        code = extract_code(raw or "")
        if not code:
            return "INCONCLUSIVE"
        out = execute_code(code, timeout=timeout, problem=problem)
        return parse_verdict(out)
    except Exception:
        return "INCONCLUSIVE"
