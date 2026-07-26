"""
批量数学解题脚本（使用 Lagent Agent）

功能：
1. 读取 JSON 格式的题目文件
2. 使用 Lagent 数学 Agent 逐题求解
3. 解析代码执行结果和最终答案
4. 保存为 JSON 结果格式
5. 支持断点续跑

使用方法：
1. 确保已安装 lagent：pip install -e ./lagent
2. 确保 .env 文件中配置了 INTERN_S1_API_KEY
3. 运行：python batch_solver_lagent.py --input sample_problems.json --output results_lagent.json
"""

import os
import json
import time
import argparse
from datetime import datetime

from dotenv import load_dotenv

from lagent.agents import Agent
from lagent.schema import AgentMessage
from lagent.llms import GPTAPI
from lagent.actions import ActionExecutor, IPythonInteractive
from lagent.prompts.parsers import ToolParser
from lagent.agents.aggregator import InternLMToolAggregator


load_dotenv()


# ===================== 配置区域 =====================
API_KEY = os.environ.get("INTERN_S1_API_KEY")
MODEL = "intern-s1"
REQUEST_INTERVAL = 2.0  # 限速，避免 API 流控
MAX_TURNS = 3           # 每道题最多几轮思考-执行循环

SYSTEM_PROMPT = """你是一名数学解题专家。请按以下步骤解决题目：
1. 仔细阅读题目，理解已知条件和求解目标；
2. 分析解题思路，必要时编写 Python 代码辅助计算；
3. 把 Python 代码放在 ```python 和 ``` 之间；
4. 根据代码执行结果，给出最终答案；
5. 最终答案用 JSON 格式输出：{"answer": "...", "reasoning": "..."}
"""


class InternS1API(GPTAPI):
    """封装 Intern-S1 API。"""

    def __init__(self, api_key, model="intern-s1", **kwargs):
        super().__init__(
            model_type=model,
            key=api_key,
            url="https://chat.intern-ai.org.cn/api/v1/chat/completions",
            retry=3,
            **kwargs,
        )


def create_math_agent():
    """创建数学解题 Agent。"""
    if not API_KEY:
        raise ValueError("请先配置 INTERN_S1_API_KEY")

    llm = InternS1API(
        api_key=API_KEY,
        model=MODEL,
        max_new_tokens=4096,
        temperature=0.2,
    )

    parser = ToolParser(
        tool_type="code interpreter",
        begin="```python\n",
        end="\n```\n",
    )

    agent = Agent(
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        output_format=parser,
        aggregator=InternLMToolAggregator(),
    )

    executor = ActionExecutor(actions=[IPythonInteractive()])
    return agent, executor


def extract_json_from_text(text: str):
    """从文本中提取 JSON 结果。"""
    import re

    # 尝试找 ```json ... ``` 块
    blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if blocks:
        try:
            data = json.loads(blocks[-1])
            return data.get("answer", ""), data.get("reasoning", "")
        except json.JSONDecodeError:
            pass

    # 尝试找大括号 JSON
    matches = re.findall(r'\{.*"answer".*"reasoning".*\}', text, re.DOTALL)
    if matches:
        try:
            data = json.loads(matches[-1])
            return data.get("answer", ""), data.get("reasoning", "")
        except json.JSONDecodeError:
            pass

    # 兜底
    return text.strip()[-200:], text.strip()[:800]


def solve_one_problem(agent, executor, problem_text: str):
    """使用 Lagent 解一道题。"""
    try:
        message = AgentMessage(sender="user", content=problem_text)
        full_history = []

        for turn in range(MAX_TURNS):
            message = agent(message)
            full_history.append({"role": "agent", "content": message.content})

            # 如果没有代码需要执行，说明已经给出答案
            if message.formatted is None or message.formatted.get("tool_type") is None:
                answer, reasoning = extract_json_from_text(message.content)
                return {
                    "success": True,
                    "answer": str(answer),
                    "reasoning": str(reasoning),
                    "raw_response": message.content,
                    "error": None,
                    "turns": turn + 1,
                }

            # 执行代码
            message = executor(message)
            full_history.append({"role": "executor", "content": message.content})

        # 超过最大轮数，取最后一轮 Agent 输出作为答案
        answer, reasoning = extract_json_from_text(full_history[-2]["content"])
        return {
            "success": True,
            "answer": str(answer),
            "reasoning": str(reasoning),
            "raw_response": full_history[-2]["content"],
            "error": None,
            "turns": MAX_TURNS,
        }

    except Exception as e:
        return {
            "success": False,
            "answer": "",
            "reasoning": "",
            "raw_response": "",
            "error": str(e),
            "turns": 0,
        }


def load_problems(input_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_results(output_path: str):
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_results(results, output_path: str):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="使用 Lagent 批量数学解题")
    parser.add_argument("--input", default="sample_problems.json", help="输入题目文件路径")
    parser.add_argument("--output", default="results_lagent.json", help="输出结果文件路径")
    args = parser.parse_args()

    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输入文件：{args.input}")
    print(f"输出文件：{args.output}")

    problems = load_problems(args.input)
    total = len(problems)
    print(f"共读取 {total} 道题目")

    results = load_existing_results(args.output)
    completed_ids = {r["idx"] for r in results if "idx" in r}
    print(f"已存在 {len(results)} 条结果，将跳过已完成的题目")

    agent, executor = create_math_agent()

    for idx, problem in enumerate(problems):
        problem_id = problem.get("id", f"prob_{idx:03d}")

        if problem_id in completed_ids:
            print(f"[{idx+1}/{total}] {problem_id} 已存在，跳过")
            continue

        print(f"\n[{idx+1}/{total}] 正在解答：{problem_id}")
        problem_text = problem.get("problem", "")

        result = solve_one_problem(agent, executor, problem_text)

        record = {
            "idx": idx,
            "status": "success" if result["success"] else "error",
            "final_response": result["answer"],
            "trace": [{"step": "reasoning", "content": result["reasoning"]}],
            "domain": problem.get("domain", ""),
            "error": result["error"] or None,
            "turns": result["turns"],
            "timestamp": datetime.now().isoformat(),
        }
        if result["error"]:
            record["error"] = {"type": "RuntimeError", "message": result["error"]}

        results.append(record)
        completed_ids.add(problem_id)
        save_results(results, args.output)

        print(f"  状态：{'成功' if result['success'] else '失败'}")
        print(f"  答案：{result['answer'][:100]}...")

        # 重置 Agent 记忆，避免上一题干扰下一题
        agent.reset()

        if idx < total - 1:
            time.sleep(REQUEST_INTERVAL)

    print(f"\n完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"结果已保存到：{args.output}")
    print(f"成功：{sum(1 for r in results if r['success'])}/{total}")


if __name__ == "__main__":
    main()
