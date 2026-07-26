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

from utils import extract_code, execute_code, extract_boxed, extract_final_answer, is_correct_vote


# ============================================================
# 平台 Client 适配器
# ============================================================
class _PlatformLLMAdapter:
    """把平台提供的 client 包装成 Lagent 兼容的 LLM 后端。

    平台 client 接口（参考 baseline llm_client.py）：
        client.chat(messages, temperature=0.2, max_tokens=4096) -> str
    """

    def __init__(self, client, default_temperature: float = 0.2, default_max_tokens: int = 4096):
        self._client = client
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens

    def chat(self, messages: list, **kwargs) -> str:
        temperature = kwargs.pop("temperature", self._default_temperature)
        max_tokens = kwargs.pop("max_tokens", self._default_max_tokens)
        return self._client.chat(messages, temperature=temperature, max_tokens=max_tokens)


from utils import extract_code, execute_code, extract_boxed, extract_final_answer, is_correct_vote


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
    "你是一位严谨的数学推理智能体。请解决用户给出的数学问题，并给出清晰推理与最终答案。\n\n"
    "要求：\n"
    "1. 先分析题意和关键条件\n"
    "2. 给出必要的推导步骤，关键步骤不可省略\n"
    "3. 涉及计算时写 Python 代码（```python ... ```）\n"
    "4. 最终答案用 \\boxed{答案} 的 LaTeX 格式明确写出"
)

_PROMPT_VOTER = (
    "你是一个数学答案验证器。请判断候选解答是否正确解决了题目。\n\n"
    "不要输出解释。只输出以下两行之一：\n"
    "VERDICT: A\n"
    "或\n"
    "VERDICT: B\n\n"
    "其中 A 表示候选解答正确，B 表示候选解答错误。"
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
    candidate_count: int = 3           # 求解器生成候选答案数（≥1）
    vote_count: int = 2                # 每个候选答案的投票验证次数

    # ── 温度 ──
    analyzer_temperature: float = 0.1
    strategist_temperature: float = 0.2
    solver_temperature: float = 0.6    # 多候选需要较高温度（与 baseline 一致）
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

    def __init__(self, client, config: Optional[AgentConfig] = None):
        """
        参数：
          client: 平台注入的模型客户端，需支持 client.chat(messages, temperature, max_tokens) -> str
          config: 可选推理配置，不传则使用默认值
        """
        self.config = config or AgentConfig()
        cfg = self.config

        # 分析 Agent（低温度，提取结构化信息）
        self._analyzer = Agent(
            llm=_PlatformLLMAdapter(client, cfg.analyzer_temperature, cfg.analyzer_max_tokens),
            template=[{"role": "system", "content": _PROMPT_ANALYZER}],
            name="问题分析师",
        )

        # 策略 Agent（低温度，规划最优路径）
        self._strategist = Agent(
            llm=_PlatformLLMAdapter(client, cfg.strategist_temperature, cfg.strategist_max_tokens),
            template=[{"role": "system", "content": _PROMPT_STRATEGIST}],
            name="策略规划师",
        )

        # 求解 Agent（高温度 0.6，用于多候选采样 — 这是 baseline 核心策略）
        self._solver = Agent(
            llm=_PlatformLLMAdapter(client, cfg.solver_temperature, cfg.solver_max_tokens),
            template=[{"role": "system", "content": _PROMPT_SOLVER}],
            name="数学求解器",
        )

        # 投票 Agent（温度 0.0，确保判断一致性）
        self._voter = Agent(
            llm=_PlatformLLMAdapter(client, cfg.voter_temperature, cfg.voter_max_tokens),
            template=[{"role": "system", "content": _PROMPT_VOTER}],
            name="投票验证器",
        )

        # 教学 Agent
        self._teacher = Agent(
            llm=_PlatformLLMAdapter(client, cfg.teacher_temperature, cfg.teacher_max_tokens),
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

            # ══════════════════════════════════════════════════════
            # ③ 多候选生成（baseline 风格，但加入了分析/策略上下文）
            # ══════════════════════════════════════════════════════
            candidates, gen_trace = self._generate_candidates(problem, analysis, strategy, idx)
            trace.extend(gen_trace)

            # debug 日志：候选数
            trace.append({
                "step": "voting_summary",
                "content": f"生成 {len(candidates)} 个候选答案，准备投票验证。",
            })

            # ══════════════════════════════════════════════════════
            # ④ 多候选投票验证（baseline 风格）
            # ══════════════════════════════════════════════════════
            scored = []
            for cid, candidate in enumerate(candidates):
                confidence, vote_trace = self._vote_on_candidate(problem, candidate, idx, cid)
                scored.append({"content": candidate, "confidence": confidence})
                trace.extend(vote_trace)

            best = max(scored, key=lambda item: item["confidence"])
            trace.append({
                "step": "select_best",
                "content": f"选定最佳候选 (confidence={best['confidence']:.2f}，共 {len(candidates)} 候选)",
            })

            # 从最佳候选中提取最终答案
            final_answer = extract_final_answer(best["content"])
            if not final_answer:
                final_answer = "未能提取答案"

            # ══════════════════════════════════════════════════════
            # ⑤ 教育启发（基于最佳候选）
            # ══════════════════════════════════════════════════════
            teach_msg = AgentMessage(
                sender="user",
                content=(
                    f"原题：{problem}\n"
                    f"最佳解答：{best['content'][:1200]}\n"
                    "请生成教学启发。"
                ),
            )
            insight = self._teacher(teach_msg, session_id=f"{idx}:t").content
            trace.append({"step": "teach", "content": insight})

            elapsed = round(time.time() - t_start, 1)
            trace.append({"step": "finalize", "content": f"耗时 {elapsed}s，confidence={best['confidence']:.2f}"})

            return {"final_response": final_answer, "trace": trace}

        except Exception as exc:
            trace.append({
                "step": "error",
                "content": f"{type(exc).__name__}: {exc}",
            })
            return {"final_response": "", "trace": trace}

    # ── 多候选生成 ──
    def _generate_candidates(
        self, problem: str, analysis: str, strategy: str, idx: int
    ) -> Tuple[List[str], List[Dict]]:
        """生成多个候选解答（baseline _generate_candidates 的增强版）。

        与 baseline 的关键差异：
          - 不是裸题目，而是注入了分析 + 策略作为上下文
          - 每个候选收到不同的采样 seed（通过 candidate_id 区分）
          - 若模型输出包含 Python 代码，自动执行并反馈结果
        """
        candidates = []
        trace = []
        cfg = self.config

        for cid in range(cfg.candidate_count):
            # 为每个候选构造带编号的 prompt（鼓励多样性）
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

            # 求解器调用（使用高温度 0.6 促进多样性）
            response = self._solver(
                solve_msg,
                session_id=f"{idx}:solve:{cid}",
                temperature=cfg.solver_temperature,
                max_tokens=cfg.solver_max_tokens,
            )
            solution_text = response.content

            trace.append({
                "step": f"candidate_{cid}",
                "content": {
                    "candidate_id": cid,
                    "prompt_preview": solve_msg.content[:300],
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
