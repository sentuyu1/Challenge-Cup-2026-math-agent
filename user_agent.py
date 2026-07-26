"""
user_agent.py — 挑战杯 XH-202627 数学智能体入口

基于 Intern-S1 的数学智能体系统，采用 5 Agent 推理流水线：
  问题分析师 → 策略规划师 → 数学求解器(含Python代码执行) → 答案校验员 → 启发式教师

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
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ── Lagent 框架路径（从同级 lagent 目录加载，不使用绝对路径）──
_LAGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lagent")
if os.path.isdir(_LAGENT_DIR):
    sys.path.insert(0, _LAGENT_DIR)

from lagent.agents import Agent
from lagent.schema import AgentMessage


# ============================================================
# 平台 Client 适配器
#   将 platform_client.chat(messages, temperature, max_tokens) → str
#   适配为 Lagent Agent 需要的 LLM 接口
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
    "你是一位数学解题专家。请执行以下步骤：\n"
    "1. **数学推导**：逐步推导，关键步骤不可省略\n"
    "2. **编写代码**：涉及计算时写 Python 代码（```python ... ```）\n"
    "3. **给出答案**：最终答案用 \\boxed{答案} 的 LaTeX 格式\n"
    "推导要详细但清晰。"
)

_PROMPT_VALIDATOR = (
    "你是一位数学验证专家。请严格检查前面的解题过程：\n"
    "1. **推导检查**：逻辑是否有漏洞？公式引用是否正确？\n"
    "2. **计算验证**：数值结果是否正确？（如有 Python 代码输出，以此为准）\n"
    "3. **边界检查**：特殊情况和边界条件是否处理？\n"
    "4. **结论**：回答以'验证结果：'开头，不超过 150 字。"
)

_PROMPT_TEACHER = (
    "你是一位优秀的数学教师。请根据前面的解题过程，生成教育启发：\n"
    "## 知识点\n列出核心数学知识点（3-5 个）\n"
    "## 解题技巧\n总结关键技巧\n"
    "## 常见误区\n指出学生容易犯的错误\n"
    "## 拓展思考\n给出一个值得进一步思考的问题"
)


# ============================================================
# 工具函数
# ============================================================

def _extract_code(text: str) -> Optional[str]:
    """提取文本中的第一个 ```python ... ``` 代码块。"""
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else None


def _execute_code(code: str, timeout: int = 30) -> str:
    """在子进程中安全执行 Python 代码，返回 stdout 或 stderr。"""
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
        )
        return (r.stdout.strip() or r.stderr.strip())
    except subprocess.TimeoutExpired:
        return "代码执行超时"


def _extract_boxed(text: str) -> str:
    """从 LaTeX 文本中提取 \\boxed{...} 内的答案。"""
    m = re.search(r"\\boxed\{(.+?)\}", text)
    return m.group(1).strip() if m else ""


# ============================================================
# Agent 配置
# ============================================================

@dataclass
class AgentConfig:
    """推理流水线可调参数。"""
    max_retries: int = 2                # API internal error 最大重试次数
    solver_max_tokens: int = 16384      # 求解器的最大输出 token
    analyzer_max_tokens: int = 512
    strategist_max_tokens: int = 512
    validator_max_tokens: int = 512
    teacher_max_tokens: int = 1024
    analyzer_temperature: float = 0.1
    strategist_temperature: float = 0.2
    solver_temperature: float = 0.2
    validator_temperature: float = 0.0
    teacher_temperature: float = 0.8
    code_timeout: int = 30              # 代码执行超时（秒）


# ============================================================
# ReasoningAgent — 5 Agent 推理流水线（核心）
# ============================================================

class ReasoningAgent:
    """基于 Intern-S1 的数学智能体，采用 5 Agent 推理流水线。

    流水线架构：
      ① 问题分析师 ── 题型分类 + 提取关键信息
      ② 策略规划师 ── 设计解题路径 + 选择最优方法
      ③ 数学求解器 ── 逐步推导 + Python 代码执行
      ④ 答案校验员 ── 反思纠错 + 边界检查
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

        # 每个子 Agent 有独立的 LLM 适配器（温度/max_tokens 不同）
        self._analyzer = Agent(
            llm=_PlatformLLMAdapter(client, cfg.analyzer_temperature, cfg.analyzer_max_tokens),
            template=[{"role": "system", "content": _PROMPT_ANALYZER}],
            name="问题分析师",
        )
        self._strategist = Agent(
            llm=_PlatformLLMAdapter(client, cfg.strategist_temperature, cfg.strategist_max_tokens),
            template=[{"role": "system", "content": _PROMPT_STRATEGIST}],
            name="策略规划师",
        )
        self._solver = Agent(
            llm=_PlatformLLMAdapter(client, cfg.solver_temperature, cfg.solver_max_tokens),
            template=[{"role": "system", "content": _PROMPT_SOLVER}],
            name="数学求解器",
        )
        self._validator = Agent(
            llm=_PlatformLLMAdapter(client, cfg.validator_temperature, cfg.validator_max_tokens),
            template=[{"role": "system", "content": _PROMPT_VALIDATOR}],
            name="答案校验员",
        )
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
            # ═══════════════════════════════════════════════
            # ① 问题分析
            # ═══════════════════════════════════════════════
            msg = AgentMessage(sender="user", content=problem)
            analysis = self._analyzer(msg, session_id=f"{idx}:a").content
            trace.append({"step": "analyze", "content": analysis})

            # ═══════════════════════════════════════════════
            # ② 策略规划
            # ═══════════════════════════════════════════════
            plan_msg = AgentMessage(
                sender="user",
                content=f"原始问题：{problem}\n分析结果：{analysis}\n请制定解题策略。",
            )
            strategy = self._strategist(plan_msg, session_id=f"{idx}:s").content
            trace.append({"step": "strategize", "content": strategy})

            # ═══════════════════════════════════════════════
            # ③ 数学求解（含代码执行 + internal error 重试）
            # ═══════════════════════════════════════════════
            solution_text = ""
            code_output = ""
            for attempt in range(cfg.max_retries + 1):
                solve_msg = AgentMessage(
                    sender="user",
                    content=(
                        f"{problem}\n\n"
                        f"分析：{analysis[:400]}\n"
                        f"策略：{strategy[:400]}\n"
                        "请直接给出完整解答。"
                    ),
                )
                solution_text = self._solver(solve_msg, session_id=f"{idx}:v:{attempt}").content
                if "internal error" not in solution_text.lower():
                    break

            code = _extract_code(solution_text)
            if code:
                code_output = _execute_code(code, timeout=cfg.code_timeout)

            trace.append({
                "step": "solve",
                "content": {
                    "solution": solution_text[:2000],
                    "code": code or "",
                    "code_output": code_output,
                },
            })

            # ═══════════════════════════════════════════════
            # ④ 答案校验
            # ═══════════════════════════════════════════════
            verify_msg = AgentMessage(
                sender="user",
                content=(
                    f"原题：{problem}\n"
                    f"解题：{solution_text[:2000]}\n"
                    f"代码执行结果：{code_output}\n"
                    "请验证答案是否正确。"
                ),
            )
            verification = self._validator(verify_msg, session_id=f"{idx}:x").content
            trace.append({"step": "validate", "content": verification})

            # ═══════════════════════════════════════════════
            # ⑤ 教育启发
            # ═══════════════════════════════════════════════
            teach_msg = AgentMessage(
                sender="user",
                content=(
                    f"原题：{problem}\n"
                    f"推导摘要：{solution_text[:800]}\n"
                    f"验证结论：{verification}\n"
                    "请生成教学启发。"
                ),
            )
            insight = self._teacher(teach_msg, session_id=f"{idx}:t").content
            trace.append({"step": "teach", "content": insight})

            # ═══════════════════════════════════════════════
            # 提取最终答案
            # ═══════════════════════════════════════════════
            final_answer = _extract_boxed(solution_text)
            if not final_answer:
                final_answer = _extract_boxed(verification)
            if not final_answer:
                # 兜底：取 solution 最后非空行
                lines = [l.strip() for l in solution_text.split("\n") if l.strip()]
                final_answer = lines[-1][:500] if lines else "未能提取答案"

            elapsed = round(time.time() - t_start, 1)
            trace.append({"step": "finalize", "content": f"耗时 {elapsed}s"})

            return {"final_response": final_answer, "trace": trace}

        except Exception as exc:
            trace.append({
                "step": "error",
                "content": f"{type(exc).__name__}: {exc}",
            })
            return {"final_response": "", "trace": trace}
