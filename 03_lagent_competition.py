"""
挑战杯赛题 XH-202627：基于 Intern-S1 的数学智能体设计与推理创新

用 Lagent 框架实现的参赛方案示例
=============================================
赛题核心要求：
  1. 基于 Intern-S1 API 构建数学智能体
  2. 能理解自然语言数学问题、自主规划求解、输出结果
  3. 启发式解释推理过程
  4. 多类型数学问题中表现稳健
  5. 结构化输出（JSON）

本实现特点（用 Lagent）：
  - Agent（Lagent）+ 系统提示词：自然语言理解 + 推理规划
  - ReAct 模式（可选）：思考 → 写代码 → 执行 → 再思考
  - Python 代码执行：精确数值计算
  - JSON 结构化输出
"""

import json
import re
import sys
import os
import subprocess
import time
_lagent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lagent")
if os.path.isdir(_lagent_path):
    sys.path.insert(0, _lagent_path)
else:
    raise RuntimeError("未找到 Lagent 框架。请将 lagent 目录放在项目根目录下。")

from lagent.agents import Agent, StreamingAgent
from lagent.schema import AgentMessage
from lagent.llms import GPTAPI


# ============================================================
# 1. 封装 Intern-S1 LLM（通过 OpenAI 兼容 API）
# ============================================================
class InternS1API(GPTAPI):
    """Lagent 可调用的 Intern-S1 模型（书生 API）。"""

    def __init__(self, api_key, model="intern-s2-preview", **kwargs):
        super().__init__(
            model_type=model,
            key=api_key,
            api_base="https://chat.intern-ai.org.cn/api/v1/chat/completions",
            **kwargs,
        )


def _get_api_key():
    key = os.environ.get("INTERN_API_KEY", "")
    if not key:
        raise RuntimeError("请设置环境变量 INTERN_API_KEY（你的书生平台 API 密钥）")
    return key


llm = InternS1API(
    api_key=_get_api_key(),
    model="intern-s2-preview",
    max_new_tokens=4096,
    temperature=0.2,
)


# ============================================================
# 2. 系统提示词（对应赛题"过程解释与学习启发"要求）
# ============================================================
MATH_SYSTEM_PROMPT = """你是一名世界级数学解题专家，请按以下规范解决用户提供的数学题：

## 推理规范
1. **问题理解**：用自然语言复述问题，明确已知条件和求解目标；
2. **策略规划**：分析最适合的解题方法（代数、几何、微积分、概率等），说明选择理由；
3. **详细推导**：逐步展示推导过程，对关键步骤给出解释；
4. **代码验证**：当涉及计算、数值验证、符号推导时，编写 Python 代码精确求解，
   代码放在 ```python 和 ``` 之间；
5. **最终答案**：用 LaTeX 公式给出最终结果，并封装为 \\boxed{{答案}}；

## 输出要求
- 最终必须输出一个 JSON 对象，格式如下：
```json
{
  "problem": "原题",
  "solution": {
    "understanding": "问题理解",
    "strategy": "解题策略",
    "derivation": "推导过程",
    "code": "Python代码（如有）",
    "code_output": "代码执行结果",
    "final_answer": "最终答案"
  },
  "educational_insight": "学习启发：本题考察的知识点、解题技巧、常见误区等"
}
```"""


# ============================================================
# 3. 创建 Agent
# ============================================================
agent = Agent(
    llm=llm,
    name="MathSolver",
)
agent.template = [dict(role="system", content=MATH_SYSTEM_PROMPT)]


# ============================================================
# 4. 代码提取与执行工具
# ============================================================
def extract_code_blocks(text: str) -> list[str]:
    """提取所有 Python 代码块。"""
    return re.findall(r"```python\n(.*?)```", text, re.DOTALL)


def execute_code(code: str, timeout: int = 30) -> dict:
    """执行 Python 代码，返回 {stdout, stderr, success}。"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "执行超时", "success": False}


def extract_json(text: str) -> dict | None:
    """从文本中提取 JSON 对象。"""
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if not match:
        match = re.search(r"\{[\s\S]*\"problem\"[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(1) if "```" in match.group(0) else match.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ============================================================
# 5. 完整解题函数（最多 3 轮 Agent 交互）
# ============================================================
def solve_problem(problem: str, metadata: dict = None, max_turns: int = 3) -> dict:
    """
    用 Lagent Agent 求解一个数学问题。

    流程：
      第 1 轮：Agent 理解问题 → 推理 → 生成代码 → JSON 输出
      后续轮：执行代码 → 把结果回传给 Agent → 修正/完善回答

    返回：
      dict: {"final_response": str, "trace": list}
    """
    if metadata is None:
        metadata = {}
    trace = []
    message = AgentMessage(sender="user", content=problem)
    all_code_outputs = []

    for turn in range(max_turns):
        # Agent 推理
        message = agent(message, session_id=0)
        content = message.content
        trace.append({"step": f"turn_{turn+1}", "content": content[:1500]})

        # 提取并执行代码
        codes = extract_code_blocks(content)
        if codes:
            for code in codes:
                exec_result = execute_code(code)
                if exec_result["stdout"]:
                    all_code_outputs.append(exec_result["stdout"])
                elif exec_result["stderr"]:
                    all_code_outputs.append(exec_result["stderr"])

            # 有代码执行结果 → 回传让 Agent 整合
            if all_code_outputs:
                message = AgentMessage(
                    sender="user",
                    content=f"代码执行结果：{all_code_outputs[-1]}\n请完善你的回答，给出最终 JSON 结果。",
                )
                continue

        # 没有代码 → 尝试提取 JSON 结果
        result = extract_json(content)
        if result:
            final_answer = result.get("solution", {}).get("final_answer", "见推导")
            trace.append({"step": "finalize", "content": final_answer})
            return {"final_response": final_answer, "trace": trace}

        # 兜底：提取 \\boxed{}
        final = re.search(r"\\boxed\{(.+?)\}", content)
        final_answer = final.group(1).strip() if final else content.strip()[-500:]
        trace.append({"step": "finalize", "content": final_answer})
        return {"final_response": final_answer, "trace": trace}

    trace.append({"step": "error", "content": f"超过最大轮次 {max_turns}"})
    return {"final_response": "", "trace": trace}


# ============================================================
# 6. 测试多个题目
# ============================================================
if __name__ == "__main__":
    problems = [
        # 题目 1：初等数论（有计算）
        "求 1 到 100 之间所有质数的和。",

        # 题目 2：微积分
        "计算定积分 ∫₀¹ x²·sin(x) dx 的值，精确到小数点后 4 位。",

        # 题目 3：线性代数
        "设矩阵 A = [[2,1],[1,3]]，求 A 的特征值和特征向量。",
    ]

    results = []
    for i, problem in enumerate(problems):
        print(f"\n{'='*60}")
        print(f"题目 {i+1}: {problem}")
        print('='*60)

        start = time.time()
        idx = str(i + 1)
        result = solve_problem(problem)
        elapsed = time.time() - start

        print(f"\n耗时: {elapsed:.1f}s")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        results.append({
            "id": idx,
            **result,
            "elapsed_seconds": round(elapsed, 1),
        })

    # 保存结果
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lagent_math_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"所有结果已保存至: {output_path}")
    print(f"共求解 {len(results)} 题")
