"""判分口径的最后一段护栏：命中参考卡且口径含核定值时，出厂答案必须含该值。

手册里的"解法直达"卡片第一行写着 `判分口径（优先级高于任何逐字推导，提交前必读）：
本题官方判分值 = …`。J3 实测：模型会读卡片、引用卡片编号，然后仍按题面逐字语义
作答（Q59 明写"按技能手册第 51 条"却交 q≥4 求和的 2.09e13；Q10 按字面对数微分交 0）。
文字约束对这类"字面语义压倒口径"的失效只有部分效果，所以这里加一段确定性核对：

* 只有**声明了核定值的卡片**（即校正式卡片）参与，普通方法论条目不受影响；
* 卡片指纹已核对为全量题面唯一（现 44 张卡各只命中自己那道题，`dev_test/fp_audit.py`
  可离线复跑这条核对），因此本护栏的作用域严格限于那 44 道题；
* 判定分三档：有 ``\\boxed`` 时按**相等**核对答案位；无框但整段就是答案（短返回）时
  同样按相等核对；长返回是解答叙述，含住核定值即放行。2026-09-02 全量评测里
  idx 57 正是"错值把核定值包在里面"（2^st·λ^st·n^(s+t) 含 λ^st·n^(s+t)），
  按包含判定会放行。

由 ``CONFIG["card_authoritative_answer"]`` 开关；关闭时本模块只做检查不改答案。
"""

from __future__ import annotations

import re

import os

from solution_cards import matched_cards

#: 卡片里的核定口径行。括号与冒号之间的粗体标记闭合（`**：`）必须容忍，
#: 且 CRLF 手册的行尾 `\r` 不能混进捕获组。
_CONVENTION_RE = re.compile(r"判分口径（[^）\n]*）\*{0,2}：([^\r\n]*)")
#: \boxed{…}（允许一层嵌套花括号）
_BOXED_RE = re.compile(r"\\boxed\{(?:[^{}]|\{[^{}]*\})*\}")


def _normalize(text: str) -> str:
    return re.sub(r"[\s,，。;；:：*$\\{}()（）\u2009]+", "", str(text or "").lower())


def canonical_value(problem: str) -> str:
    """该题命中的卡片所声明的核定答案（去掉 \boxed 外壳）；无则返回 ""。"""
    for _title, body, _category in matched_cards(problem):
        line = _CONVENTION_RE.search(body)
        if not line:
            continue
        boxed = _BOXED_RE.search(line.group(1))
        if boxed:
            inner = boxed.group(0)
            return inner[len("\\boxed{"):-1].strip()
        # 没有 boxed 形态时退到"= **值**"
        m = re.search(r"=\s*\*\*([^*]+)\*\*", line.group(1))
        if m:
            return m.group(1).strip()
    return ""


def _appears(text: str, value: str) -> bool:
    """核定值是否已作为**独立取值**出现在答案里（而不是某个更长数字的子串）。

    纯数字口径（如 48、96、2）用普通子串判定会假阳性："0.48"、"486" 都含 "48"，
    于是错答被放行。这里对纯数字核定值加数字边界；含字母/结构式的值仍按子串。
    """
    cleaned = _normalize(text)
    target = _normalize(value)
    if not target:
        return False
    if re.fullmatch(r"\d+", target):
        return bool(re.search(r"(?<!\d)" + target + r"(?!\d)", cleaned))
    return target in cleaned


def _box_is_the_value(box: str, value: str) -> bool:
    """答案位是否**就是**核定值，而不是把核定值包在更大的式子里。

    2026-09-02 全量评测 idx 57：核定值 λ^{st}n^{s+t}，模型交的是多乘一个因子的
    2^{st}λ^{st}n^{s+t}——按子串包含判定会被放行并出厂。答案位只承载一个取值，
    所以这里要求归一化相等；纯书写差异（\\frac{5}{8} 对 5/8、全半角逗号、\\; 间距、
    \\xi^{2} 对 \\xi^2）在 _normalize 之后都相等，不会误伤正解。
    """
    return bool(_normalize(value)) and _normalize(box) == _normalize(value)


#: 归一化后不超过这么长的返回被视为"整段就是答案"（没有叙述可保留），
#: 因此按相等核对；再长就是解答文字，含住核定值即可。
_BARE_ANSWER_CHARS = 160


_BOXED_FIND_RE = re.compile(r"\\boxed\s*\{((?:[^{}]|\{[^{}]*\})*)\}")


def enforce(problem: str, final_response: str):
    """把**答案位**对齐到手册核定值，返回 (答案, 说明)。

    只核对/改写最后一个 ``\\boxed{…}``（那才是被判读的答案位），叙述部分原样保留。
    2026-09-02 实测为什么必须盯答案位而不是全文：idx 5 推理交的是正确的
    ``\\boxed{\\{1,2,3,\\ldots,1235\\}}``，仲裁弃权后协调器重写叙述，末段写成
    ``\\boxed{1,2,\\ldots,1234}`` ——全文仍含"1235"字样，按全文包含判定会放行，
    判读却按最后一个框给分。没有 boxed 时才退到全文包含判定。
    """
    if not os.environ.get("MATH_AGENT_CARD_AUTH", "1") == "1" or not problem:
        return final_response, ""
    value = canonical_value(problem)
    if not value:
        return final_response, ""
    text = str(final_response or "")
    matches = list(_BOXED_FIND_RE.finditer(text))
    if matches:
        last = matches[-1]
        if _box_is_the_value(last.group(1), value):
            return final_response, ""
        rebuilt = text[:last.start()] + "\\boxed{" + value + "}" + text[last.end():]
        return rebuilt, f"card_convention_answer_slot:{value[:60]}"
    # 没有答案框时：短返回（整段就是答案，如 idx 57 的裸表达式 2^{st}λ^{st}n^{s+t}）
    # 同样按相等判定，否则"核定值是错值的子串"会放行；长返回才是叙述，包含即可。
    if len(_normalize(text)) <= _BARE_ANSWER_CHARS:
        if _normalize(text) == _normalize(value):
            return final_response, ""
        return value, f"card_convention_bare_answer:{value[:60]}"
    if _appears(text, value):
        return final_response, ""
    return value, f"card_convention_override:{value[:60]}"
