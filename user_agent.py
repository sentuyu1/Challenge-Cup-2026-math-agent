"""
user_agent.py — 挑战杯 XH-202627 数学智能体入口

基于 Intern-S1 的数学智能体系统，采用 **5 Agent 推理流水线 + 多候选投票** 混合架构：

  ① 问题分析师 ── 题型分类 + 提取关键信息
  ② 策略规划师 ── 设计解题路径 + 选择最优方法
  ③ 数学求解器 ── 多候选生成（温度 0.6 × 3 次采样）
  ④ 投票验证器 ── 对每个候选投票验证（2 次/候选），选最高 confidence
  ⑤ 启发式教师 ── 知识点总结 + 易错点分析

创新融合：
  - 5 步流水线（分析→策略→求解→校验→教学）：结构化推理过程
  - 多候选投票（baseline 精华）：求解器多次采样 + 投票选最优 → 提高鲁棒性
  - Python 代码执行：确保数值计算的精确性

平台加载方式：
  from user_agent import ReasoningAgent
  agent = ReasoningAgent(client=platform_client)
  result = agent.solve(problem, metadata)

规范要求：
  - 不接受/不硬编码 API key，client 由平台注入
  - solve() 签名为 (problem: str, metadata: dict)
  - 返回 {"final_response": str, "trace": list}
"""

import re
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ── Lagent 框架路径 ──
_LAGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lagent")
if os.path.isdir(_LAGENT_DIR):
    sys.path.insert(0, _LAGENT_DIR)

from lagent.agents import Agent
from lagent.schema import AgentMessage

from utils import extract_code, extract_code_blocks, execute_code, extract_boxed, extract_final_answer, is_correct_vote


# ============================================================
# 平台 Client 适配器
# ============================================================
class _PlatformLLMAdapter:
    """把平台提供的 client 包装成 Lagent 兼容的 LLM 后端。

    平台 client 接口（参考 baseline llm_client.py）：
        client.chat(messages, temperature=0.2, max_tokens=4096, thinking_mode=False) -> str

    model 参数：空字符串 = 使用平台默认模型（零风险）；填了 = 覆盖模型名。
    通过 baseline 的 chat(**request_args) 机制传 model 覆盖默认值。
    """

    def __init__(self, client, default_temperature: float = 0.2, default_max_tokens: int = 4096, thinking_mode: bool = False, model: str = ""):
        self._client = client
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._thinking_mode = thinking_mode
        self._model = model

    def chat(self, messages: list, **kwargs) -> str:
        temperature = kwargs.pop("temperature", self._default_temperature)
        max_tokens = kwargs.pop("max_tokens", self._default_max_tokens)
        # 支持运行时覆盖 thinking_mode（多轮推理中间轮可关）
        thinking_mode = kwargs.pop("thinking_mode", self._thinking_mode)
        # 若指定了 model，则通过 request_args 覆盖平台默认模型
        model_kwargs = {"model": self._model} if self._model else {}
        return self._client.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_mode=thinking_mode,
            **model_kwargs,
        )


# ============================================================
# 子 Agent 系统提示词
# ============================================================

_PROMPT_ANALYZER = (
    "你是一位数学问题分析师。对于用户给出的数学问题，请完成以下分析：\n"
    "1. **题型分类**：属于什么数学领域？（微积分、线性代数、概率论、偏微分方程等）\n"
    "2. **已知条件**：列出所有给定的条件和参数\n"
    "3. **求解目标**：明确需要求解什么\n"
    "4. **难度评估**：估算解题需要几步推理\n"
    "用简洁的中文回答，不超过 150 字。"
)

_PROMPT_STRATEGIST = (
    "你是一位数学解题策略专家。前面已经分析了问题，现在请设计解题方案：\n"
    "1. **可选方法**：列出 2-3 种可能的解法（解析法、数值法、图解法等）\n"
    "2. **推荐方案**：选择最优方法并说明理由\n"
    "3. **步骤规划**：用编号列出详细的解题步骤（3-5 步）\n"
    "4. **验证策略**：如何验证答案正确性？\n"
    "用简洁的中文回答，不超过 200 字。"
)

_PROMPT_SOLVER = (
    "你是一位严谨的数学推理智能体。请解决用户给出的数学问题，并给出清晰推理与最终答案。\n"
    "请使用中文回答，所有推导、解释和结论必须用中文书写。\n\n"
    "要求：\n"
    "1. 先分析题意和关键条件\n"
    "2. 给出必要的推导步骤，关键步骤不可省略\n"
    "3. 涉及计算时写 Python 代码（```python ... ```），稍后会反馈执行结果供你修正\n"
    "4. 最终答案用 \\boxed{答案} 的 LaTeX 格式明确写出"
)

_PROMPT_SOLVER_PROOF = (
    "你是一位严谨的数学定理证明专家。请对给定的数学命题给出完整严谨的证明。\n"
    "请使用中文回答，所有推导、解释和结论必须用中文书写。\n\n"
    "要求：\n"
    "1. 明确写出需要证明的命题\n"
    "2. 给出从已知条件到结论的完整逻辑推导，每一步都要有严格的数学依据\n"
    "3. 涉及计算验证时写 Python 代码（```python ... ```）\n"
    "4. 证明完成后，在 \\boxed{成立} 或 \\boxed{结论} 中写明最终结论\n"
    "5. 注意处理边界条件和特殊情况\n"
    "6. 如果题面问「是否」类问题，需明确回答「是」或「否」并证明"
)

_PROMPT_SOLVER_COMPUTE = (
    "你是一位数学计算专家。请对给定的数学计算题给出精确解答。\n"
    "请使用中文回答，所有推导、解释和结论必须用中文书写。\n\n"
    "要求：\n"
    "1. 先明确需要计算的目标\n"
    "2. 选择合适的计算方法并说明理由\n"
    "3. 编写 Python 代码进行数值/符号计算（```python ... ```），稍后会反馈执行结果\n"
    "4. 根据代码执行结果，给出精确答案\n"
    "5. 最终答案用 \\boxed{答案} 的 LaTeX 格式明确写出\n"
    "6. 数值答案保留合理精度，但优先给出精确解析表达式"
)

_PROMPT_VOTER = (
    "你是一个数学答案验证器。请判断候选解答是否正确解决了题目。\n\n"
    "不要输出解释。只输出以下两行之一：\n"
    "VERDICT: A\n"
    "或\n"
    "VERDICT: B\n\n"
    "其中 A 表示候选解答正确，B 表示候选解答错误。"
)

_PROMPT_SUMMARIZER = (
    "你是一位数学推理摘要专家。请把下面的解题推理压缩成若干条关键引理（lemma）。\n\n"
    "要求：\n"
    "1. 每条引理是推导过程中得出的、可复用的关键中间结论\n"
    "2. 用简洁的数学语言陈述，附上简短证明依据\n"
    "3. 只保留对解题真正有用的结论，去掉冗余步骤\n"
    "4. 最多提取 4 条引理\n\n"
    "输出格式（每条一行）：\n"
    "引理：<陈述>（依据：<证明依据>）\n"
    "引理：<陈述>（依据：<证明依据>）\n"
    "...\n\n"
    "如果这段推理没有可复用的中间结论，只输出：无"
)

_PROMPT_LEMMA_VERIFIER = (
    "你是一个数学引理验证器。请判断下面这条引理（中间结论）是否正确。\n\n"
    "引理：\n"
    "{lemma}\n\n"
    "只输出一行：VERDICT: A（正确）或 VERDICT: B（错误）"
)

_PROMPT_PROCESS_VERIFIER = (
    "你是一个数学证明审查员。请检查下面的解答，找出逻辑漏洞、计算错误或推理缺口。\n\n"
    "题目：\n{problem}\n\n"
    "解答：\n{solution}\n\n"
    "如果解答正确且完整，只输出：VERDICT: A\n"
    "如果存在漏洞，输出：VERDICT: B，并简要指出问题所在"
)


_PROMPT_TEACHER = (
    "你是一位优秀的数学教师。请根据前面的解题过程，生成教育启发：\n"
    "## 知识点\n列出核心数学知识点（3-5 个）\n"
    "## 解题技巧\n总结关键技巧\n"
    "## 常见误区\n指出学生容易犯的错误\n"
    "## 拓展思考\n给出一个值得进一步思考的问题"
)


# ============================================================
# Agent 配置（含 voting 参数，融合 baseline AgentConfig）
# ============================================================

@dataclass
class AgentConfig:
    """推理流水线可调参数。"""
    # ── 多候选投票（核心鲁棒性参数）──
    candidate_count: int = 2           # 求解器生成候选答案数（≥1），多轮推理模式下用较小值
    vote_count: int = 2                # 每个候选答案的投票验证次数

    # ── 多轮层次化推理（Intern-S1-MO 核心）──
    reasoning_rounds: int = 2          # 推理轮数（≥1），每轮：求解→摘要引理→验证→下一轮复用；2轮平衡耗时与深度

    # ── 温度 ──
    analyzer_temperature: float = 0.1
    strategist_temperature: float = 0.2
    solver_temperature: float = 0.6    # 多候选默认温度（每个候选独立计算温度梯度）
    voter_temperature: float = 0.0     # 投票需要确定性
    teacher_temperature: float = 0.8

    # ── max_tokens ──
    solver_max_tokens: int = 16384
    analyzer_max_tokens: int = 512
    strategist_max_tokens: int = 512
    voter_max_tokens: int = 1024
    teacher_max_tokens: int = 1024

    # ── 其他 ──
    internal_error_retries: int = 2    # API internal error 重试
    code_timeout: int = 30             # 代码执行超时（秒）
    model: str = ""                    # 模型名，空=用平台默认（甲方推荐 s2）；平台评测固定模型，代码传 model 无效


# ============================================================
# ReasoningAgent — 5 Agent 流水线 + 多候选投票（核心）
# ============================================================

class ReasoningAgent:
    """基于 Intern-S1 的数学智能体，采用 **5 Agent 流水线 + 多候选投票** 混合架构。

    流水线架构：
      ① 问题分析师 ── 题型分类 + 提取关键信息
      ② 策略规划师 ── 设计解题路径 + 选择最优方法
      ③ 数学求解器 ── 多候选生成（temperature=0.6 × 3 采样）
      ④ 投票验证器 ── 每候选投票 2 次，选最高 confidence
      ⑤ 启发式教师 ── 知识点总结 + 易错点分析

    用法：
      >>> agent = ReasoningAgent(client=platform_client)
      >>> result = agent.solve("求 1+2+...+100 的和", {"idx": 0})
      >>> print(result["final_response"])
    """

    def __init__(self, client, config: Optional[AgentConfig] = None, *args, **kwargs):
        """
        参数：
          client: 平台注入的模型客户端，需支持 client.chat(messages, temperature, max_tokens) -> str
          config: 可选推理配置，不传则使用默认值
          *args, **kwargs: 平台额外注入参数（兼容未来扩展）
        """
        self.config = config or AgentConfig()
        cfg = self.config

        # 分析 Agent（低温度，提取结构化信息）
        self._analyzer = Agent(
            llm=_PlatformLLMAdapter(client, cfg.analyzer_temperature, cfg.analyzer_max_tokens, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_ANALYZER}],
            name="问题分析师",
        )

        # 策略 Agent（低温度，规划最优路径）
        self._strategist = Agent(
            llm=_PlatformLLMAdapter(client, cfg.strategist_temperature, cfg.strategist_max_tokens, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_STRATEGIST}],
            name="策略规划师",
        )

        # 求解 Agent（高温度 0.6，用于多候选采样 — 这是 baseline 核心策略）
        # 创建两个版本：证明专用 + 计算专用，根据题型自动选择
        # 求解阶段开启 thinking mode，提升复杂推理正确率
        self._solver_proof = Agent(
            llm=_PlatformLLMAdapter(client, cfg.solver_temperature, cfg.solver_max_tokens, thinking_mode=True, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_SOLVER_PROOF}],
            name="数学求解器(证明)",
        )
        self._solver_compute = Agent(
            llm=_PlatformLLMAdapter(client, cfg.solver_temperature, cfg.solver_max_tokens, thinking_mode=True, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_SOLVER_COMPUTE}],
            name="数学求解器(计算)",
        )

        # 投票 Agent（温度 0.0，确保判断一致性）
        self._voter = Agent(
            llm=_PlatformLLMAdapter(client, cfg.voter_temperature, cfg.voter_max_tokens, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_VOTER}],
            name="投票验证器",
        )

        # 摘要 Agent（把长推理压缩成引理，Intern-S1-MO 的 summarizer）
        self._summarizer = Agent(
            llm=_PlatformLLMAdapter(client, 0.2, 2048, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_SUMMARIZER}],
            name="引理摘要器",
        )

        # 引理验证 Agent（验证中间结论正确性，防错误传播）
        self._lemma_verifier = Agent(
            llm=_PlatformLLMAdapter(client, 0.0, 512, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_LEMMA_VERIFIER}],
            name="引理验证器",
        )

        # 过程验证 Agent（检查最终解答漏洞，Intern-S1-MO 的 process verifier）
        self._process_verifier = Agent(
            llm=_PlatformLLMAdapter(client, 0.0, 1024, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_PROCESS_VERIFIER}],
            name="过程验证器",
        )

        # 教学 Agent
        self._teacher = Agent(
            llm=_PlatformLLMAdapter(client, cfg.teacher_temperature, cfg.teacher_max_tokens, model=cfg.model),
            template=[{"role": "system", "content": _PROMPT_TEACHER}],
            name="启发式教师",
        )

    # ── solve() —— 平台要求的入口方法 ──
    def solve(self, problem: str, metadata: Dict) -> Dict:
        """求解一道数学题。

        参数：
          problem  (str): 数学题题面文本
          metadata (dict): 题目元信息，至少包含 idx

        返回：
          dict: {"final_response": str, "trace": list}
        """
        idx = metadata.get("idx", 0)
        trace: List[Dict[str, Any]] = []
        t_start = time.time()
        cfg = self.config

        try:
            # ══════════════════════════════════════════════════════
            # ① 问题分析
            # ══════════════════════════════════════════════════════
            msg = AgentMessage(sender="user", content=problem)
            analysis = self._analyzer(msg, session_id=f"{idx}:a").content
            trace.append({"step": "analyze", "content": analysis})

            # ══════════════════════════════════════════════════════
            # ② 策略规划
            # ══════════════════════════════════════════════════════
            plan_msg = AgentMessage(
                sender="user",
                content=f"原始问题：{problem}\n分析结果：{analysis}\n请制定解题策略。",
            )
            strategy = self._strategist(plan_msg, session_id=f"{idx}:s").content
            trace.append({"step": "strategize", "content": strategy})

            # 判断是否为证明题：题面含证明/推导/构造/定理等关键词
            _proof_keywords = ["证明", "求证", "推导", "判断并证明", "证明或反驳",
                               "是否", "定理", "引理", "当且仅当", "充要",
                               "构造", "说明其存在", "证明或"]
            is_proof = any(kw in problem for kw in _proof_keywords)

            # ══════════════════════════════════════════════════════
            # ③ 多轮层次化推理（Intern-S1-MO 核心：推理→摘要引理→复用）
            # ══════════════════════════════════════════════════════
            best_text, reason_trace = self._multi_round_reason(problem, analysis, strategy, idx, is_proof)
            trace.extend(reason_trace)

            trace.append({
                "step": "reasoning_done",
                "content": f"多轮推理完成，共 {cfg.reasoning_rounds} 轮。",
            })

            # ── 构建 final_response（FAQ Q120/Q118 要求完整解答，非仅 boxed 结论）──
            boxed_answer = extract_boxed(best_text)

            # is_proof 已在第②步后判定，此处直接复用

            if is_proof:
                # 证明题：返回完整解答（judger 需要判断推理过程是否合理）
                # 同时确保 boxed 结论可见
                if len(best_text) < 8000:
                    final_response = best_text
                else:
                    # 过长时保留关键头尾
                    final_response = best_text[:4000] + "\n\n... (中间过程省略) ...\n\n" + best_text[-4000:]
            elif boxed_answer:
                # 计算题/填空题：返回关键推导摘要 + 最终答案
                # 取解答最后 1/3（通常含最终推导+答案）避免丢失上下文
                answer_parts = best_text.split("\n")
                if len(answer_parts) > 30:
                    # 保留开头的分析 + 结尾的答案
                    final_response = (
                        "\n".join(answer_parts[:8])
                        + "\n\n... (推导过程) ...\n\n"
                        + "\n".join(answer_parts[-20:])
                    )
                else:
                    final_response = best_text
            else:
                # 兜底：返回完整解答
                final_response = best_text if len(best_text) < 8000 else best_text[:4000] + best_text[-4000:]

            final_response = final_response.strip()
            if not final_response:
                final_response = boxed_answer or "未能提取答案"

            final_answer = boxed_answer or extract_final_answer(best_text) or "见解答"

            trace.append({
                "step": "finalize",
                "content": {
                    "boxed_answer": final_answer,
                    "is_proof": is_proof,
                    "final_response_length": len(final_response),
                },
            })

            # ══════════════════════════════════════════════════════
            # ⑤ 教育启发（基于最终解答）
            # ══════════════════════════════════════════════════════
            teach_msg = AgentMessage(
                sender="user",
                content=(
                    f"原题：{problem}\n"
                    f"最终解答：{best_text[:1200]}\n"
                    "请生成教学启发。"
                ),
            )
            insight = self._teacher(teach_msg, session_id=f"{idx}:t").content
            trace.append({
                "step": "teach",
                "content": {
                    "raw": insight,
                    "note": "本题的教育启发（知识点、技巧、误区、拓展）",
                },
            })

            elapsed = round(time.time() - t_start, 1)
            trace.append({"step": "finalize", "content": f"耗时 {elapsed}s"})

            return {"final_response": final_response, "trace": trace}

        except Exception as exc:
            trace.append({
                "step": "error",
                "content": f"{type(exc).__name__}: {exc}",
            })
            return {"final_response": "", "trace": trace}

    # ── 解析引理摘要 ──
    @staticmethod
    def _parse_lemmas(text: str) -> List[str]:
        """从摘要器输出中解析引理列表。"""
        lemmas = []
        for line in text.split("\n"):
            line = line.strip()
            if not line or line == "无" or line == "无。":
                continue
            # 匹配 "引理：..." 或 "引理1：..." 等格式
            if "引理" in line and "：" in line:
                # 取引理冒号后的内容，截断到合理长度
                content = line.split("：", 1)[1].strip() if "：" in line else line
                if len(content) > 5:
                    lemmas.append(content[:200])
        # 去重保序
        seen = set()
        unique = []
        for l in lemmas:
            if l not in seen:
                seen.add(l)
                unique.append(l)
        return unique[:4]

    # ── 多轮层次化推理（Intern-S1-MO 核心）──
    def _multi_round_reason(
        self, problem: str, analysis: str, strategy: str, idx: int, is_proof: bool
    ) -> Tuple[str, List[Dict]]:
        """多轮层次化推理：每轮「求解 → 摘要引理 → 复用引理继续深挖」。

        对齐 Intern-S1-MO 的 reasoning → summarizer → verifier 循环：
          - 第 1 轮：给出初步解答
          - 中间轮：把上一轮结论压成引理，带着引理继续深挖
          - 最后一轮：得出最终解
        """
        cfg = self.config
        solver = self._solver_proof if is_proof else self._solver_compute
        trace = []
        lemmas: List[str] = []
        current_solution = ""

        for round_idx in range(cfg.reasoning_rounds):
            is_final = (round_idx == cfg.reasoning_rounds - 1)

            # ── 构造 prompt ──
            if round_idx == 0:
                prompt = (
                    f"题目：\n{problem}\n\n"
                    f"分析摘要：{analysis[:300]}\n"
                    f"推荐策略：{strategy[:300]}\n\n"
                    "请给出完整解答，在最后用 \\boxed{答案} 明确写出最终结果。"
                )
            else:
                lemma_text = "\n".join(f"{i+1}. {l}" for i, l in enumerate(lemmas)) if lemmas else "(无)"
                prompt = (
                    f"题目：\n{problem}\n\n"
                    f"你之前已经推导出以下关键结论（引理）：\n{lemma_text}\n\n"
                    "请基于这些已证结论继续深入推理，完善并最终确定解答。"
                    "不要重复推导已经确定的引理，直接在它们基础上推进。\n"
                    "在最后用 \\boxed{答案} 明确写出最终结果。"
                )

            solve_msg = AgentMessage(sender="user", content=prompt)
            # 中间轮关 thinking mode（省时间），最后一轮开启深度推理
            round_thinking = is_final
            response = solver(
                solve_msg,
                session_id=f"{idx}:round:{round_idx}",
                temperature=cfg.solver_temperature,
                max_tokens=cfg.solver_max_tokens,
                thinking_mode=round_thinking,
            )
            current_solution = response.content

            # ── 代码执行反馈（保留原有能力）──
            code_blocks = extract_code_blocks(current_solution)
            if code_blocks:
                code_outputs = [execute_code(c, timeout=cfg.code_timeout) for c in code_blocks]
                if code_outputs:
                    feedback = "\n".join(f"[代码块 {i+1} 执行结果]:\n{out}" for i, out in enumerate(code_outputs))
                    has_error = any(
                        'error' in o.lower() or 'traceback' in o.lower() or 'indexerror' in o.lower()
                        or 'typeerror' in o.lower() or 'syntaxerror' in o.lower() or 'nameerror' in o.lower()
                        for o in code_outputs
                    )
                    if has_error:
                        refine_prompt = (
                            "你之前写的代码执行时遇到错误，请查看错误输出修正代码或改用解析方法，"
                            "注意原题没有变化：\n\n" + feedback +
                            "\n\n输出修正后的完整解答，最后用 \\boxed{答案} 给出结果。"
                        )
                    else:
                        refine_prompt = (
                            "以下是你的代码执行结果，请据此确认数值是否正确，如有误请修正：\n\n"
                            + feedback +
                            "\n\n输出完整解答，最后用 \\boxed{答案} 给出结果。"
                        )
                    refined = solver(
                        AgentMessage(sender="user", content=refine_prompt),
                        session_id=f"{idx}:round:{round_idx}:refine",
                        temperature=0.1,
                        max_tokens=cfg.solver_max_tokens,
                        thinking_mode=False,
                    )
                    refined_text = refined.content
                    # 防跑偏/防丢推导
                    drifted = any(kw in refined_text for kw in ["假设题目", "缺少具体的", "没有提供", "如果您有具体"])
                    if drifted:
                        current_solution = current_solution + "\n\n[代码执行反馈]:\n" + feedback[:500]
                    elif len(refined_text) < 100 and len(current_solution) > 200:
                        rb = extract_boxed(refined_text)
                        ob = extract_boxed(current_solution)
                        if rb and ob:
                            current_solution = current_solution.replace(ob, rb)
                        else:
                            current_solution = current_solution + "\n\n" + refined_text
                    else:
                        current_solution = refined_text

            trace.append({
                "step": f"round_{round_idx}",
                "content": {
                    "round": round_idx,
                    "is_final": is_final,
                    "lemmas_carried": len(lemmas),
                    "response": current_solution[:2000],
                },
            })

            # ── 非最后一轮：摘要成引理 + 验证引理（防错误传播）──
            if not is_final:
                summary_msg = AgentMessage(sender="user", content=current_solution[:3000])
                summary = self._summarizer(
                    summary_msg,
                    session_id=f"{idx}:summary:{round_idx}",
                    temperature=0.2,
                    max_tokens=2048,
                )
                candidate_lemmas = self._parse_lemmas(summary.content)

                # 逐条验证引理，只保留验证通过的
                verified_lemmas = []
                for lemma in candidate_lemmas:
                    verify_msg = AgentMessage(
                        sender="user",
                        content=f"引理：{lemma}\n\n请判断这条引理是否正确。",
                    )
                    verdict_resp = self._lemma_verifier(
                        verify_msg,
                        session_id=f"{idx}:lemma_verify:{round_idx}:{len(verified_lemmas)}",
                        temperature=0.0,
                        max_tokens=512,
                    )
                    ok = is_correct_vote(verdict_resp.content)
                    if ok:
                        verified_lemmas.append(lemma)
                    trace.append({
                        "step": f"lemma_verify_{round_idx}",
                        "content": {"lemma": lemma[:100], "verified": ok},
                    })

                if verified_lemmas:
                    lemmas = verified_lemmas
                trace.append({
                    "step": f"summary_{round_idx}",
                    "content": {"lemmas": lemmas},
                })

        # ── 最终过程验证 + 修正循环（Intern-S1-MO 的 process verifier）──
        # 最后一轮解答做漏洞检查，FAIL 则反馈修正，最多 1 次
        for fix_round in range(1):
            verify_msg = AgentMessage(
                sender="user",
                content=f"题目：{problem}\n\n解答：{current_solution[:3000]}\n\n请检查是否有漏洞。",
            )
            verdict_resp = self._process_verifier(
                verify_msg,
                session_id=f"{idx}:process_verify",
                temperature=0.0,
                max_tokens=1024,
            )
            ok = is_correct_vote(verdict_resp.content)
            trace.append({
                "step": "process_verify",
                "content": {"passed": ok, "feedback": verdict_resp.content[:200]},
            })

            if ok:
                break
            # FAIL：把 verifier 反馈交给 solver 修正
            fix_prompt = (
                f"题目：{problem}\n\n"
                f"你的解答：{current_solution[:3000]}\n\n"
                f"审查员指出以下问题：{verdict_resp.content[:500]}\n\n"
                "请根据审查意见修正解答，在最后用 \\boxed{答案} 给出最终结果。"
            )
            fixed = solver(
                AgentMessage(sender="user", content=fix_prompt),
                session_id=f"{idx}:process_fix",
                temperature=0.1,
                max_tokens=cfg.solver_max_tokens,
                thinking_mode=False,
            )
            fixed_text = fixed.content
            drifted = any(kw in fixed_text for kw in ["假设题目", "缺少具体的", "没有提供", "如果您有具体"])
            if not drifted:
                current_solution = fixed_text
            trace.append({
                "step": "process_fix",
                "content": {"fixed": not drifted, "response": current_solution[:2000]},
            })

        return current_solution, trace

    # ── 多候选生成（含代码执行反馈环 + 题型自适应）──
    def _generate_candidates(
        self, problem: str, analysis: str, strategy: str, idx: int, is_proof: bool = False
    ) -> Tuple[List[str], List[Dict]]:
        """生成多个候选解答，每个候选含代码执行→反馈→修正的闭环。

        流程：
          1. 根据题型选择 solver（证明专用 / 计算专用）
          2. 求解器给出初步解答（含 Python 代码）
          3. 提取并执行代码，收集输出
          4. 将执行结果反馈给求解器，要求修正/确认
          5. 取修正后的解答作为最终候选
        """
        candidates = []
        trace = []
        cfg = self.config

        # ── 题型自适应：选择对应的 solver ──
        solver = self._solver_proof if is_proof else self._solver_compute

        for cid in range(cfg.candidate_count):
            # ═══ 第 1 轮：初步求解 ═══
            solve_msg = AgentMessage(
                sender="user",
                content=(
                    f"题目：\n{problem}\n\n"
                    f"分析摘要：{analysis[:300]}\n"
                    f"推荐策略：{strategy[:300]}\n\n"
                    f"请给出完整解答（候选编号：{cid + 1}/{cfg.candidate_count}）。\n"
                    "在最后用 \\boxed{答案} 明确写出最终结果。"
                ),
            )

            # 恒温 0.6（温度梯度曾起反作用，回退为恒温）
            response = solver(
                solve_msg,
                session_id=f"{idx}:solve:{cid}",
                temperature=cfg.solver_temperature,
                max_tokens=cfg.solver_max_tokens,
            )
            solution_text = response.content

            # ═══ 第 2 轮：代码执行 + 反馈修正 ═══
            code_blocks = extract_code_blocks(solution_text)
            if code_blocks:
                code_outputs = []
                for code in code_blocks:
                    exec_result = execute_code(code, timeout=cfg.code_timeout)
                    code_outputs.append(exec_result)

                if code_outputs:
                    # 检查是否存在代码执行错误
                    has_error = any(
                        'error' in out.lower() or 'traceback' in out.lower() or 'indexerror' in out.lower()
                        or 'typeerror' in out.lower() or 'syntaxerror' in out.lower() or 'nameerror' in out.lower()
                        for out in code_outputs
                    )

                    feedback = "\n".join(
                        f"[代码块 {i+1} 执行结果]:\n{out}"
                        for i, out in enumerate(code_outputs)
                    )

                    if has_error:
                        refine_prompt = (
                            "你之前写的代码执行时遇到了错误，请查看以下错误输出，找出代码中的问题并修正推导中的数值错误：\n\n"
                            f"{feedback}\n\n"
                            "注意：原题没有变化，你仍然需要回答原题。"
                            "代码错误不代表题目无解，请尝试修正代码逻辑后重新给出解答。"
                            "如果代码暂时无法修正，请基于解析方法继续推导。"
                            "务必输出完整的解答文本（含推导），在最后用 \\boxed{答案} 给出最终结果。"
                        )
                    else:
                        refine_prompt = (
                            "以下是你的代码执行结果，请检查并修正答案：\n\n"
                            f"{feedback}\n\n"
                            "请根据这些结果，检查数值是否正确。"
                            "仅修改有误的计算或结论，保持原有推导结构。"
                            "务必输出完整的解答文本（含推导），在最后用 \\boxed{答案} 给出最终结果。"
                            "不要只输出 \\boxed{}，要保留所有推理步骤。"
                        )

                    refine_msg = AgentMessage(sender="user", content=refine_prompt)
                    refined = solver(
                        refine_msg,
                        session_id=f"{idx}:refine:{cid}",
                        temperature=0.1,  # 修正阶段用低温度
                        max_tokens=cfg.solver_max_tokens,
                    )
                    refined_text = refined.content

                    # ── 安全合并：修正轮丢失推导或跑偏时保留原始解答 ──
                    # 跑偏信号：模型说"假设题目/缺少具体题目/没有提供"
                    drifted = any(kw in refined_text for kw in ["假设题目", "缺少具体的", "没有提供",
                                                                 "针对具体问题", "如果您有具体"])

                    if drifted:
                        # 修正轮跑偏（编造了新题目）→ 回退到第一轮，仅用代码输出追加提示
                        solution_text = solution_text + "\n\n[代码执行反馈]:\n" + feedback[:500]
                    elif len(refined_text) < 100 and len(solution_text) > 200:
                        # 修正轮输出极短（可能只给了 \boxed{}）→ 用修正的 boxed 替换原始的
                        refined_boxed = extract_boxed(refined_text)
                        original_boxed = extract_boxed(solution_text)
                        if refined_boxed and original_boxed:
                            solution_text = solution_text.replace(original_boxed, refined_boxed)
                        else:
                            solution_text = solution_text + "\n\n" + refined_text
                    else:
                        solution_text = refined_text

                    trace.append({
                        "step": f"candidate_{cid}_refine",
                        "content": {
                            "candidate_id": cid,
                            "code_count": len(code_outputs),
                            "code_outputs": code_outputs,
                            "refined_response": solution_text[:2000],
                        },
                    })
                else:
                    trace.append({
                        "step": f"candidate_{cid}_code_exec",
                        "content": {
                            "candidate_id": cid,
                            "code_count": len(code_blocks),
                            "note": "代码执行完成，无有效输出",
                        },
                    })

            # 记录候选
            trace.append({
                "step": f"candidate_{cid}",
                "content": {
                    "candidate_id": cid,
                    "solver_type": "proof" if is_proof else "compute",
                    "response": solution_text[:2000],
                },
            })

            candidates.append(solution_text)

        return candidates, trace

    # ── 投票验证 ──
    def _vote_on_candidate(
        self, problem: str, candidate: str, idx: int, candidate_id: int
    ) -> Tuple[float, List[Dict]]:
        """对单个候选解答进行多次投票，返回 confidence 分数。

        与 baseline _verify_candidate 一致：
          - vote_count 次独立投票
          - 每次投票用相同的 prompt + temperature=0.0
          - confidence = 正确票数 / 总票数
        """
        votes = []
        trace = []
        cfg = self.config

        for vote_id in range(cfg.vote_count):
            vote_msg = AgentMessage(
                sender="user",
                content=(
                    "题目：\n"
                    f"{problem}\n\n"
                    "候选解答：\n"
                    f"{candidate[:3000]}\n\n"
                    "请判断候选解答是否正确。\n"
                    "只输出一行：VERDICT: A 或 VERDICT: B。"
                ),
            )
            response = self._voter(
                vote_msg,
                session_id=f"{idx}:vote:{candidate_id}:{vote_id}",
                temperature=cfg.voter_temperature,
                max_tokens=cfg.voter_max_tokens,
            )
            verdict = response.content
            is_correct = is_correct_vote(verdict)
            votes.append(is_correct)

            trace.append({
                "step": f"vote_{candidate_id}_{vote_id}",
                "content": {
                    "candidate_id": candidate_id,
                    "vote_id": vote_id,
                    "verdict": verdict[:200],
                    "is_correct": is_correct,
                },
            })

        confidence = sum(votes) / len(votes) if votes else 0.0
        return confidence, trace
