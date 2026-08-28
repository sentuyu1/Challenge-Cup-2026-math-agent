"""finalizer.py — 判分保护：答案提取 + 结构验证（移植自折叠桌 80 分项目）

折叠桌（Shusheng_ChallengeCup_2026）的 Finalizer 是判分保护做得最全的参考实现：
  - 7 层答案提取（【答案】标签 → 答案：标签 → \\boxed{} → final: → 尾部结论 → 整体）
  - 多候选时按「信息丰富度」选优（candidate_richness），而非顺序取第一个
  - 11 种结构验证 gate，专门拦截「截断的 LaTeX 残片 / 元叙述 / 占位符」
  - _META 元叙述检测（模型在讨论格式/思考，不是答案）

纯正则 + 字符串处理，零重依赖。normalize_latex 已内联（原依赖 tools/latex_parser.py）。
"""

from __future__ import annotations

from dataclasses import dataclass
import re


def normalize_latex(text: str) -> str:
    """仅做安全的展示级归一化（非完整 TeX 解析）。"""
    value = text.strip()
    value = value.replace("\x08ar", r"\bar")  # JSON 转义 \b 被拆成 \x08 + ar
    value = re.sub(r"^\$\$?\s*|\s*\$?\$$", "", value)
    value = value.replace(r"\left", "").replace(r"\right", "")
    return value


@dataclass(frozen=True)
class ExtractionResult:
    answer: str
    method: str
    valid: bool
    rejected_reasons: tuple[str, ...] = ()
    raw_has_meta: bool = False
    explicit_answer: bool = False


class Finalizer:
    """Extract explicit answer candidates without silently repairing malformed text."""

    _LABEL = re.compile(
        r"(?im)^\s*(?:(?:【\s*(?:最终答案|答案|结论)\s*】|(?:最终\s*)?答案|结论)\s*[:：]?|(?:final\s+answer|answer)\s*[:：])\s*([^\n]+?)\s*$"
    )
    _BRACKET_LABEL = re.compile(
        r"【\s*(?:最终答案|答案|结论)\s*】\s*[:：]?\s*([^`\n]+)",
        re.IGNORECASE,
    )
    _PLACEHOLDER = re.compile(
        r"^(?:最终答案|完整答案|完整结论|答案|final(?:\s+answer)?|answer|check\s+format(?:ting)?|format(?:ting)?|(?:final\s+)?(?:conclusion|response|done)|[.。…`'\"，,]+)$",
        re.IGNORECASE,
    )
    _META = re.compile(
        r"(?:<think\b|thinking process|(?im:^\s*(?:analysis|drafting)\s*[:：])|check formatting|check spacing|"
        r"system prompt|prompt instruction|final answer should|最后一行必须|思考过程|分析过程|推理过程|"
        r"格式检查|检查格式|提示词|\bplan\b|(?im:^\s*structure\s*:)|(?:final answer )?content for (?:the )?first line|final answer content|\blet(?:'s| us)\b|\bi (?:need|will|should)\b|\bthe (?:user|task|instruction|prompt)\b|"
        r"\bg\d+\s*\[(?:proof|formula|scalar|truth|construction)|必查字段|"
        r"让我(?:验证|确认|组织)|我(?:需要|应该)|输出时)",
        re.IGNORECASE,
    )

    @staticmethod
    def extract(candidate: str) -> str:
        result = Finalizer.extract_result(candidate)
        return result.answer if result.valid else ""

    @staticmethod
    def extract_result(candidate: str) -> ExtractionResult:
        text = str(candidate or "").strip()
        if not text:
            return ExtractionResult("", "empty", False, ("empty",))
        text = re.sub(r"<\|(?:assistant|user|system|endoftext)\|>", "", text, flags=re.IGNORECASE).strip()
        raw_has_meta = Finalizer.contains_meta(text)

        # 向后扫描最后一个有效【答案】标签值，跳过回显的占位符
        bracket_labels = Finalizer._BRACKET_LABEL.findall(text)
        bracket_results = [
            Finalizer._result(label, "bracket_label", raw_has_meta=raw_has_meta, explicit=True)
            for label in bracket_labels
        ]
        valid_bracket_results = [result for result in bracket_results if result.valid]
        if valid_bracket_results:
            return max(
                enumerate(valid_bracket_results),
                key=lambda item: (Finalizer._candidate_richness(item[1].answer), item[0]),
            )[1]
        labels = Finalizer._LABEL.findall(text)
        if labels:
            label_results = [
                Finalizer._result(label, "label", raw_has_meta=raw_has_meta, explicit=True)
                for label in labels
            ]
            valid_label_results = [result for result in label_results if result.valid]
            if valid_label_results:
                return max(
                    enumerate(valid_label_results),
                    key=lambda item: (Finalizer._candidate_richness(item[1].answer), item[0]),
                )[1]
            return label_results[-1]
        boxed = Finalizer._last_boxed(text)
        if boxed is not None:
            if not boxed and r"\boxed{" in text:
                # 保留未闭合的源文本，让结构验证报告真实截断
                return Finalizer._result(text, "boxed_unclosed", raw_has_meta=raw_has_meta, explicit=True)
            return Finalizer._result(boxed, "boxed", raw_has_meta=raw_has_meta, explicit=True)
        final_lines = re.findall(r"(?im)^\s*final\s*[:：]\s*([^\n]+)", text)
        if final_lines:
            return Finalizer._result(final_lines[-1], "final_marker", raw_has_meta=raw_has_meta, explicit=True)
        if raw_has_meta:
            recovered = Finalizer._recover_tail_conclusion(text)
            if recovered:
                return Finalizer._result(recovered, "tail_segment", raw_has_meta=True)
            return ExtractionResult("", "meta_without_explicit_answer", False, ("meta_without_explicit_answer",), True, False)
        return Finalizer._result(text, "whole_response")

    @staticmethod
    def contains_meta(value: str) -> bool:
        return bool(Finalizer._META.search(str(value or "")))

    @staticmethod
    def extract_solution(candidate: str) -> str:
        """证明题：保留推理过程，只做展示级清理。"""
        return Finalizer._clean(str(candidate or "").strip())

    @staticmethod
    def _candidate_richness(value: str) -> tuple[int, int, int]:
        text = str(value or "").strip()
        mathematical = len(re.findall(r"[=+\-*/^\\]|\d|∈|⊆|≤|≥", text))
        sentences = len([item for item in re.split(r"[。；;\n]+", text) if item.strip()])
        return (sentences, mathematical, min(len(text), 2000))

    @staticmethod
    def validate_structure(answer: str) -> tuple[str, ...]:
        value = str(answer or "").strip()
        reasons: list[str] = []
        if not value:
            return ("empty",)
        if Finalizer._PLACEHOLDER.fullmatch(value):
            reasons.append("placeholder")
        if re.fullmatch(r"<\s*(?:完整答案|最终答案|答案|完整结论)\s*>", value):
            reasons.append("placeholder")
        if re.fullmatch(r"(?:final\s+)?(?:conclusion|response|done)[.。!?！]?", value, re.IGNORECASE):
            reasons.append("placeholder")
        if re.fullmatch(
            r"(?:final\s+)?(?:check|checking)(?:\s+(?:on|the|all|format(?:ting)?|constraints?|answer|result)){0,4}\s*[:：]?",
            value,
            re.IGNORECASE,
        ):
            reasons.append("placeholder")
        if re.search(r"(?:裁决|修正|补齐|重做)后的?(?:完整)?答案|(?:complete|final) answer after (?:review|correction)", value, re.IGNORECASE):
            reasons.append("placeholder")
        if re.search(r"完整答案|<\s*完整答案\s*>|\b(?:adjudicated|corrected|complete) (?:final )?answer\b", value, re.IGNORECASE):
            reasons.append("placeholder")
        if re.search(r"并给出全部结论.*(?:必要依据|必要算式)|给出全部结论.*再写", value):
            reasons.append("placeholder")
        if re.search(r"\b(?:this|that) (?:looks|seems) like\b|\bspecific test case\b|\blooks like noise\b", value, re.IGNORECASE):
            reasons.append("meta_text")
        if re.search(r"\bthis (?:phrasing|wording|instruction|prompt)\b", value, re.IGNORECASE):
            reasons.append("meta_text")
        if Finalizer._META.search(value):
            reasons.append("meta_text")
        if not re.search(r"[\w\u4e00-\u9fff=+\-*/^\\]", value):
            reasons.append("meaningless_fragment")
        if re.fullmatch(r"[\\`'\"\s]+", value):
            reasons.append("meaningless_fragment")
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", value):
            reasons.append("control_character")
        if re.search(r"</?[A-Za-z][A-Za-z0-9_-]*(?:\s+[^<>]*)?>", value):
            reasons.append("markup_fragment")
        if value.count("```") % 2:
            reasons.append("unclosed_code_fence")
        if value.count("$") % 2:
            reasons.append("unclosed_inline_math")
        if value.count(r"\(") != value.count(r"\)"):
            reasons.append("unclosed_inline_latex")
        if value.count(r"\[") != value.count(r"\]"):
            reasons.append("unclosed_display_latex")
        for environment in re.findall(r"\\begin\{([^}]+)\}", value):
            if len(re.findall(rf"\\end\{{{re.escape(environment)}\}}", value)) < len(
                re.findall(rf"\\begin\{{{re.escape(environment)}\}}", value)
            ):
                reasons.append("unclosed_latex_environment")
                break
        if not Finalizer._balanced_braces(value):
            reasons.append("unclosed_latex_brace")
        return tuple(reasons)

    @staticmethod
    def _result(
        value: str,
        method: str,
        *,
        raw_has_meta: bool = False,
        explicit: bool = False,
    ) -> ExtractionResult:
        answer = Finalizer._clean(value)
        reasons = Finalizer.validate_structure(answer)
        return ExtractionResult(answer if not reasons else "", method, not reasons, reasons, raw_has_meta, explicit)

    @staticmethod
    def _clean(answer: str) -> str:
        value = re.sub(r"^```(?:latex|text|markdown)?\s*|\s*```$", "", answer.strip(), flags=re.IGNORECASE)
        return normalize_latex(value).strip().strip('"“”')

    @staticmethod
    def _last_boxed(text: str) -> str | None:
        marker = r"\boxed{"
        position = text.rfind(marker)
        if position < 0:
            return None
        start = position + len(marker)
        depth = 1
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return text[start:index].strip()
        return ""

    @staticmethod
    def _balanced_braces(value: str) -> bool:
        depth = 0
        escaped = False
        for char in value:
            if char == "\\" and not escaped:
                escaped = True
                continue
            if char == "{" and not escaped:
                depth += 1
            elif char == "}" and not escaped:
                depth -= 1
                if depth < 0:
                    return False
            escaped = False
        return depth == 0

    @staticmethod
    def _recover_tail_conclusion(candidate: str) -> str:
        meta = re.compile(
            r"(?:thinking|analysis|draft|check|constraint|instruction|prompt|format|plan|content for (?:the )?first line|final answer content|"
            r"let(?:'s| us)|i (?:will|should|need)|思考|分析|草稿|检查|提示|格式)",
            re.IGNORECASE,
        )
        for paragraph in reversed(re.split(r"\n\s*\n+", str(candidate or ""))):
            value = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", paragraph.strip())
            if not 2 <= len(value) <= 800 or meta.search(value):
                continue
            conclusion = re.match(r"^(?:因此|所以|故|综上|从而|可得|结论|即)", value)
            formula = len(value) <= 240 and bool(re.fullmatch(
                r"[$\\A-Za-z0-9_{}()[\].,+\-*/^=<>≤≥∈\s]+", value
            )) and "=" in value
            if not (conclusion or formula):
                continue
            answer = Finalizer._clean(value)
            if not Finalizer.validate_structure(answer):
                return answer
        return ""
