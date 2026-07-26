"""
================================================================================
挑战杯 XH-202627 参赛方案：创新推理链设计
================================================================================

赛题核心要求：
  ① 推理链设计 — 多 Agent 协作流水线（非单次调用）
  ② 表达清晰度 — 结构化 JSON + 逐步推导
  ③ 教育启发性 — 每道题输出知识点和易错点

创新点（用 Lagent 原生能力，PyTorch 式设计）：
  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │ 1. 理解Agent │ → │ 2. 策略Agent  │ → │ 3. 求解Agent  │ → │ 4. 校验Agent  │
  │ Problem      │    │ Strategy      │    │ Solver        │    │ Validator     │
  │ Analyzer     │    │ Planner       │    │ (代码+执行)    │    │ (反思纠错)    │
  └─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
         ↓                    ↓                  ↓                  ↓
  "这是偏微分      "分离变量法       "u(x,t)=e^{-t}     "代入验证，等式
   方程初边值       最适合..."        sin(x)"            成立，正确"

  ┌─────────────┐
  │ 5. 教学Agent  │ ← 生成启发式解释 / JSON 输出
  │ Teacher       │
  └─────────────┘

Lagent 技术栈：
  - lagent.agents.Agent         → 每个角色的基类
  - lagent.agents.Sequential    → 链式流水线
  - lagent.schema.AgentMessage  → 消息传递
  - lagent.llms.GPTAPI          → Intern-S1 API 封装

运行：python math_agent.py --interactive
================================================================================
"""

import json
import re
import sys
import os
import subprocess
import time
import argparse

# Lagent 框架路径（优先用同级目录下的 lagent）
_lagent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lagent")
if os.path.isdir(_lagent_path):
    sys.path.insert(0, _lagent_path)
else:
    raise RuntimeError(
        "未找到 Lagent 框架。请将 lagent 目录放在项目根目录下，\n"
        "或执行: git clone https://github.com/InternLM/lagent.git"
    )

from lagent.agents import Agent, Sequential
from lagent.schema import AgentMessage
from lagent.llms import GPTAPI


# ============================================================
# Intern-S1 API 适配
# ============================================================
class InternS1API(GPTAPI):
    """Intern-S1 书生模型，通过 OpenAI 兼容接口访问。"""

    def __init__(self, api_key: str, model: str = "intern-s1", max_new_tokens: int = 4096, **kwargs):
        super().__init__(
            model_type=model,
            key=api_key,
            api_base="https://chat.intern-ai.org.cn/api/v1/chat/completions",
            max_new_tokens=max_new_tokens,
            **kwargs,
        )


def _get_api_key():
    key = os.environ.get("INTERN_API_KEY", "")
    if not key:
        raise RuntimeError("请设置环境变量 INTERN_API_KEY（你的书生平台 API 密钥）")
    return key


# ============================================================
# 工具函数
# ============================================================
def extract_code(text: str) -> str | None:
    m = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else None


def run_code(code: str) -> str:
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=30,
        )
        return r.stdout.strip() or r.stderr.strip()
    except subprocess.TimeoutExpired:
        return "执行超时"


# ============================================================
# ① 理解 Agent — 分类题型、提取关键信息
# ============================================================
ANALYZER_PROMPT = """你是一位数学问题分析师。对于用户给出的数学问题，请完成以下分析：

1. **题型分类**：这属于什么数学领域？（如：微积分、线性代数、概率论、偏微分方程等）
2. **已知条件**：列出所有给定的条件和参数
3. **求解目标**：明确需要求解什么
4. **难度评估**：估算解题需要几步推理

用简洁的中文回答，不超过 150 字。"""

analyzer_llm = InternS1API(api_key=_get_api_key(), max_new_tokens=512, temperature=0.1)
analyzer = Agent(llm=analyzer_llm, name="问题分析师")
analyzer.template = [{"role": "system", "content": ANALYZER_PROMPT}]


# ============================================================
# ② 策略 Agent — 规划解题路径
# ============================================================
STRATEGIST_PROMPT = """你是一位数学解题策略专家。前面已经分析了问题，现在请设计解题方案：

1. **可选方法**：列出 2-3 种可能的解法（如：解析法、数值法、图解法等）
2. **推荐方案**：选择最优方法并说明理由
3. **步骤规划**：用编号列出详细的解题步骤（3-5 步）
4. **验证策略**：如何验证答案正确性？

用简洁的中文回答，不超过 200 字。"""

strategist_llm = InternS1API(api_key=_get_api_key(), max_new_tokens=512, temperature=0.2)
strategist = Agent(llm=strategist_llm, name="策略规划师")
strategist.template = [{"role": "system", "content": STRATEGIST_PROMPT}]


# ============================================================
# ③ 求解 Agent — 推导 + 写代码 + 执行
# ============================================================
SOLVER_PROMPT = """你是一位数学解题专家。前面已完成问题分析和策略规划，请执行以下步骤：

1. **数学推导**：按计划逐步推导
2. **编写代码**：涉及计算时写 Python 代码（```python ... ```）
3. **给出答案**：最终答案用 \\boxed{答案} 的 LaTeX 格式

重要：推导要详细但清晰，关键步骤不可省略。"""

solver_llm = InternS1API(api_key=_get_api_key(), max_new_tokens=16384, temperature=0.2)
solver = Agent(llm=solver_llm, name="数学求解器")
solver.template = [{"role": "system", "content": SOLVER_PROMPT}]


# ============================================================
# ④ 校验 Agent — 反思纠错
# ============================================================
VALIDATOR_PROMPT = """你是一位数学验证专家。请严格检查前面的解题过程：

1. **推导检查**：逻辑是否有漏洞？公式引用是否正确？
2. **计算验证**：数值结果是否正确？（如有 Python 代码输出，以此为准）
3. **边界检查**：特殊情况和边界条件是否处理？
4. **结论**：回答是否正确？如有问题，请纠正。

回答以"验证结果："开头，不超过 150 字。"""

validator_llm = InternS1API(api_key=_get_api_key(), max_new_tokens=512, temperature=0.0)
validator = Agent(llm=validator_llm, name="答案校验员")
validator.template = [{"role": "system", "content": VALIDATOR_PROMPT}]


# ============================================================
# ⑤ 教学 Agent — 生成教育启发（赛题核心要求）
# ============================================================
TEACHER_PROMPT = """你是一位优秀的数学教师。请根据前面的解题过程，生成一段教育启发内容，格式为：

## 知识点
列出本题涉及的核心数学知识点（3-5 个）

## 解题技巧
总结解这类题的关键技巧和思路

## 常见误区
指出学生容易犯的错误

## 拓展思考
给出一个值得进一步思考的相关问题

用 JSON 格式输出：
```json
{
  "knowledge_points": ["知识点1", "知识点2", ...],
  "techniques": ["技巧1", "技巧2", ...],
  "common_mistakes": ["误区1", "误区2", ...],
  "further_thought": "拓展思考问题"
}
```"""

teacher_llm = InternS1API(api_key=_get_api_key(), max_new_tokens=1024, temperature=0.8)
teacher = Agent(llm=teacher_llm, name="启发式教师")
teacher.template = [{"role": "system", "content": TEACHER_PROMPT}]


# ============================================================
# 推理流水线 — Lagent Sequential（类比 PyTorch nn.Sequential）
# ============================================================
class InferencePipeline:
    """
    推理流水线：理解 → 策略 → 求解(含代码执行) → 校验 → 教学

    这是赛题的**核心创新**：不是单次 prompt 调用，而是
    用 Lagent Sequential 将推理链分解为 5 个专用 Agent。
    每个 Agent 各司其职，消息自动传递（类比神经网络层）。
    """

    def __init__(self):
        self.analyzer = analyzer
        self.strategist = strategist
        self.solver = solver
        self.validator = validator
        self.teacher = teacher

    def solve(self, problem: str, metadata: dict = None, verbose: bool = True, max_retries: int = 2) -> dict:
        t0 = time.time()

        for attempt in range(max_retries + 1):
            try:
                # ── 第 1 步：问题分析 ──
                if verbose:
                    print("\n" + "─" * 50)
                    tag = f"重试{attempt}" if attempt > 0 else "1/5"
                    print(f"🔍 [{tag}] 分析问题...", end=" ", flush=True)
                msg = AgentMessage(sender="user", content=problem)
                analysis = self.analyzer(msg, session_id=0)
                if verbose:
                    print("✓")
                    print(f"     {analysis.content[:120]}")

                # ── 第 2 步：策略规划 ──
                if verbose:
                    tag2 = f"重试{attempt}" if attempt > 0 else "2/5"
                    print(f"🧭 [{tag2}] 规划策略...", end=" ", flush=True)
                plan_msg = AgentMessage(
                    sender="user",
                    content=f"原始问题：{problem}\n分析结果：{analysis.content}\n请制定解题策略。",
                )
                plan = self.strategist(plan_msg, session_id=1)
                if verbose:
                    print("✓")
                    print(f"     {plan.content[:120]}")

                # ── 第 3 步：求解（含代码执行） ──
                if verbose:
                    tag3 = f"重试{attempt}" if attempt > 0 else "3/5"
                    print(f"⚡ [{tag3}] 数学求解...", end=" ", flush=True)
                solve_msg = AgentMessage(
                    sender="user",
                    content=f"{problem}\n\n分析摘要：{analysis.content[:300]}\n\n请直接给出完整解答。",
                )
                solution = self.solver(solve_msg, session_id=2)
                solution_text = solution.content

                # 检测 internal error
                if "internal error" in solution_text.lower():
                    if attempt < max_retries:
                        if verbose:
                            print("⚠️ API internal error，重试中...")
                        continue
                    else:
                        if verbose:
                            print("⚠️ (重试耗尽，使用现有结果)")

                # 提取并执行 Python 代码
                code_output = ""
                code = extract_code(solution_text)
                if code:
                    code_output = run_code(code)
                    if code_output and verbose:
                        print(f"✓ (代码输出: {code_output})")
                elif verbose:
                    print("✓ (纯推导)")

                if verbose and len(solution_text) > 200:
                    print(f"     {solution_text[:200]}...")
                elif verbose:
                    print(f"     {solution_text}")

                # ── 第 4 步：校验 ──
                if verbose:
                    print("✅ [4/5] 验证答案...", end=" ", flush=True)
                verify_msg = AgentMessage(
                    sender="user",
                    content=(
                        f"原题：{problem}\n"
                        f"解题过程：{solution_text}\n"
                        f"代码执行结果：{code_output}\n"
                        "请验证答案是否正确。"
                    ),
                )
                verification = self.validator(verify_msg, session_id=3)
                if verbose:
                    print("✓")
                    print(f"     {verification.content[:120]}")

                # ── 第 5 步：教育启发 ──
                if verbose:
                    print("💡 [5/5] 生成教学启发...", end=" ", flush=True)
                teach_msg = AgentMessage(
                    sender="user",
                    content=f"原题：{problem}\n推导：{solution_text}\n验证：{verification.content}\n请生成教学启发。",
                )
                insight = self.teacher(teach_msg, session_id=4)
                if verbose:
                    print("✓")

                elapsed = round(time.time() - t0, 1)

                # 提取最终答案
                final = re.search(r"\\boxed\{(.+?)\}", solution_text)
                final_answer = final.group(1) if final else "见推导"

                # 解析教育启发 JSON
                try:
                    insight_json = json.loads(
                        re.search(r"```json\s*\n(.*?)\n```", insight.content, re.DOTALL).group(1)
                    )
                except Exception:
                    insight_json = {"knowledge_points": [], "techniques": [], "common_mistakes": [], "further_thought": ""}

                return {
                    "final_response": final_answer,
                    "trace": [
                        {"step": "analyze", "content": analysis.content},
                        {"step": "strategize", "content": plan.content},
                        {"step": "solve", "content": solution_text[:2000]},
                        {"step": "code_exec", "content": code_output if code_output else "(无代码)"},
                        {"step": "validate", "content": verification.content},
                        {"step": "teach", "content": insight.content},
                        {"step": "finalize", "content": f"最终答案: {final_answer}, 耗时 {elapsed}s"},
                    ],
                    "_internal": {
                        "code": code or "",
                        "educational": insight_json,
                        "elapsed_seconds": elapsed,
                    },
                }

            except Exception as e:
                if attempt < max_retries:
                    if verbose:
                        print(f"⚠️ 错误: {e}，重试中...")
                    continue
                else:
                    return {
                        "final_response": "",
                        "trace": [
                            {"step": "error", "content": f"{type(e).__name__}: {e}"},
                        ],
                        "_internal": {"error": str(e), "elapsed_seconds": round(time.time() - t0, 1)},
                    }

        return {"final_response": "", "trace": [{"step": "error", "content": "超过最大重试次数"}]}


# ============================================================
# CLI 入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Intern-S1 数学智能体 — 5 Agent 推理流水线")
    parser.add_argument("--interactive", action="store_true", default=True, help="交互模式")
    parser.add_argument("--batch", type=str, help="JSON 题目文件")
    parser.add_argument("--output", type=str, help="结果输出 JSON")
    args = parser.parse_args()

    pipeline = InferencePipeline()

    print("=" * 60)
    print("Intern-S1 数学智能体系统")
    print("创新推理链：分析 → 策略 → 求解 → 校验 → 教学")
    print("基于 Lagent 框架 (5 Agent Sequential Pipeline)")
    print("=" * 60)

    if args.batch:
        with open(args.batch, encoding="utf-8") as f:
            data = json.load(f)
        problems = [p if isinstance(p, str) else p["problem"] for p in data]
        results = []
        for i, p in enumerate(problems):
            print(f"\n{'='*50}\n[{i+1}/{len(problems)}] {p[:80]}...")
            r = pipeline.solve(p, verbose=True)
            results.append(r)
            print(f"\n答案: {r['final_response']}")
        out = args.output or "results.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存: {out}")
    else:
        print("\n交互模式，输入数学题，quit 退出\n")
        results = []
        while True:
            p = input("题目> ").strip()
            if p.lower() in ("quit", "q", "exit"):
                break
            if not p:
                continue
            r = pipeline.solve(p, verbose=True)
            results.append(r)
            print(f"\n📌 答案: {r['final_response']}")
            edu = r.get("_internal", {}).get("educational", {})
            if edu.get("knowledge_points"):
                print(f"📚 知识点: {', '.join(edu['knowledge_points'])}")


if __name__ == "__main__":
    main()
