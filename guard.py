"""guard.py — 确定性守护（计数题 / 模结构题）

════════════════════════════════════════════════════════
  题面 ──→ 守护判定
              │
      ┌───────┴────────┐
      ▼                ▼
   计数题            模结构题
   （多少种/几个）    （F_2 / Z_m + 求和）
      │                │
   代码有枚举？      代码显式取模？
      │否              │否
      ▼                ▼
   [守护拦截] 不执行 —— 打回让模型重写
════════════════════════════════════════════════════════

为什么需要（两类真实事故的形态）：
  - **计数题**：模型给出"看起来对"的闭式公式，算出来的数是错的
    （实证：闭式给 1120，真值 1792）。计数题的闭式极易在边界/重复计数上出错，
    可靠做法是先在 n=2,3,4 这种最小规模上**暴力枚举**，与公式逐点对照，
    吻合后再外推到题面规模。
  - **模结构题**：在 F_2 / Z_m 上定义的量，最后却按普通整数求和
    （实证：6 个 F_2 取值按整数相加得 3，正确应模 2 得 1）。
    中间量可以按整数算，但**最终聚合必须在结构内完成**。

设计原则：
  - **保守合取**：模结构守护要求"结构信号"与"聚合动作"同时命中才触发，
    避免"证明该映射是 F_2 线性的"这类无聚合的题被误拦；
  - **不执行**，而不是执行后打折——错误的验证结果比没有验证结果更危险
    （下游可能用它覆盖正确的推理答案）。
"""

from __future__ import annotations

import re

# ── 计数题信号 ──
_COUNTING_RE = re.compile(
    r"多少个|多少种|几种|共有多少|有多少[种个对组项]|种数|方案数|选法|"
    r"个数为|求个数|计数|"
    r"how\s+many|number\s+of|count\s+the|enumerate",
    re.IGNORECASE,
)

# ── 模结构信号 ──
_MODULAR_STRUCT_RE = re.compile(
    r"\\mathbb\{F\}_?2|\\mathbb\{Z\}|GF\(2\)|F_2\b|二元域|有限域|剩余类|"
    r"模\s*\d+|同余|\\pmod|modulo",
    re.IGNORECASE,
)

# ── 聚合动作信号（必须有"求和 / 计数 / 合并"这类动作）──
_MODULAR_AGG_RE = re.compile(
    r"求和|之和|总和|相加|\\sum|计数|总数|个数|number\s+of",
    re.IGNORECASE,
)


def needs_enumeration_guard(problem: str) -> bool:
    """题面是否属于"计数"类（多少种 / 几个 / how many）。"""
    return bool(_COUNTING_RE.search(problem or ""))


def code_has_enumeration(code: str) -> bool:
    """代码里是否真的做了枚举（循环或 itertools 枚举库）。"""
    c = code or ""
    if re.search(r"\bfor\b|\bwhile\b", c):
        return True
    return bool(re.search(r"itertools|combinations|permutations|product|subsets|bfs|dfs", c))


def needs_modular_guard(problem: str) -> bool:
    """结构信号 与 聚合动作 同时命中才触发（保守合取，避免误拦）。"""
    p = problem or ""
    return bool(_MODULAR_STRUCT_RE.search(p)) and bool(_MODULAR_AGG_RE.search(p))


def code_complies_modular(code: str) -> bool:
    """代码是否显式地在结构内做最终聚合（取模 / 异或 / 有限域运算）。"""
    return bool(re.search(r"%\s*\d|Mod\(|GF\(|galois|\^=|xor|按位|取模", code or ""))


def guard_reason(problem: str, code: str) -> str:
    """返回拦截原因；空串表示放行。

    拦截信息会作为"代码执行结果"回灌给模型（下游把非答案输出视为
    需要修正的信号），因此这里的文案要能指导模型改写。
    """
    if not problem or not code:
        return ""

    if needs_enumeration_guard(problem) and not code_has_enumeration(code):
        return (
            "计数题：代码只用了闭式公式、没有小规模枚举对照。计数题的闭式"
            "极易在边界或重复计数上出错，必须在最小规模（n=2,3,4 或 ≤4×4 网格）"
            "上暴力枚举、与公式逐点 assert 对照，至少 2 点吻合再外推到题面规模，"
            "并打印对照表。"
        )

    if needs_modular_guard(problem) and not code_complies_modular(code):
        return (
            "模结构题：最终聚合没有在结构内完成（未见显式取模）。中间量可以按"
            "普通整数计算，但求和 / 计数 / 合并必须在 F_2 / Z_m 内进行"
            "（F_2 中 1+1=0，等价于异或或 %2；Z_m 取 %m），并打印结构核验结果。"
        )

    return ""


# ── 验证代码反伪造 ──
# 危险形态：代码不计算、直接打印"验证状态: PASS"——看起来做了验证，
# 实际什么都没验。这种"假证据"一旦被下游当成可靠结论，会顶掉正确答案。

_FABRICATED_CLAIM_RE = re.compile(
    r"验证状态\s*[:：]\s*PASS|验证通过|VERIFIED|核验通过|assert\s+True",
    re.IGNORECASE,
)

#: 实质计算的迹象（循环 / 推导式 / 符号计算 / 比较或类型断言）
#: 注意：**不收录裸 `assert`**——`assert True` 正是最典型的假验证；
#: 真正的断言会带比较符或 isinstance/len，由这些模式覆盖。
_COMPUTE_RE = re.compile(
    r"\bfor\b|\bwhile\b|\bsum\(|solve\(|integrate\(|simplify\(|diff\(|"
    r"isinstance\(|len\(|==|!=|<=|>=",
)


def looks_fabricated_verification(code: str) -> bool:
    """代码是否"声称验证通过但没有实质计算"。"""
    c = code or ""
    if not _FABRICATED_CLAIM_RE.search(c):
        return False
    return not _COMPUTE_RE.search(c)


def authenticity_reason(code: str) -> str:
    """返回反伪造拦截原因；空串表示放行。"""
    if looks_fabricated_verification(code):
        return (
            "验证代码没有做任何实质计算，却直接声称验证通过。请真正执行核验："
            "把候选代回原式化简残差、或用小规模枚举逐点比对，再输出核验结论。"
        )
    return ""
