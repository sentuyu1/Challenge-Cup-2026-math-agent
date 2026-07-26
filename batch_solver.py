"""
批量数学解题脚本（直接调用 Intern-S1 API）

功能：
1. 读取 JSON 格式的题目文件
2. 逐题调用 Intern-S1 模型
3. 解析模型输出中的答案
4. 保存为比赛要求的 JSON 结果格式
5. 支持断点续跑（中途失败可以从上次位置继续）
6. 自动限速，避免触发 API 流控

使用方法：
1. 确保 .env 文件中配置了 INTERN_S1_API_KEY
2. 准备好题目文件（如 sample_problems.json）
3. 运行：python batch_solver.py --input sample_problems.json --output results.json
"""

import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# 加载 .env 文件中的环境变量
load_dotenv()


# ===================== 配置区域 =====================
API_KEY = os.environ.get("INTERN_S1_API_KEY")
BASE_URL = "https://chat.intern-ai.org.cn/api/v1/"
MODEL = "intern-s1"  # 可换成 intern-s1-pro / intern-s1-mini

# API 流控：默认每分钟 30 次，所以每次请求间隔至少 2 秒
REQUEST_INTERVAL = 2.0
MAX_RETRIES = 3

SYSTEM_PROMPT = """你是一名数学解题专家。请按以下步骤解决题目：
1. 仔细阅读题目，理解已知条件和求解目标；
2. 进行逐步推理，必要时使用数学符号和公式；
3. 给出最终答案；
4. 最后必须输出 JSON 格式的结果，格式如下：
{"answer": "你的最终答案", "reasoning": "简要的推理过程"}

注意：
- answer 字段只放最终答案，不要放推理过程；
- reasoning 字段放关键推理步骤；
- JSON 必须放在最后一行，且确保格式正确。
"""


def create_client():
    """创建 OpenAI 客户端。"""
    if not API_KEY:
        raise ValueError("请先配置 INTERN_S1_API_KEY 环境变量或在 .env 文件中设置")
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def parse_answer(text: str):
    """
    从模型输出中提取答案和推理过程。
    优先解析最后的 JSON 块，如果解析失败则做简单兜底。
    """
    import re

    # 尝试找到最后一个 ```json ... ``` 块
    json_blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_blocks:
        try:
            result = json.loads(json_blocks[-1])
            return {
                "answer": str(result.get("answer", "")).strip(),
                "reasoning": str(result.get("reasoning", "")).strip(),
            }
        except json.JSONDecodeError:
            pass

    # 尝试找到最后一对大括号内的 JSON
    matches = re.findall(r'\{.*"answer".*"reasoning".*\}', text, re.DOTALL)
    if matches:
        try:
            result = json.loads(matches[-1])
            return {
                "answer": str(result.get("answer", "")).strip(),
                "reasoning": str(result.get("reasoning", "")).strip(),
            }
        except json.JSONDecodeError:
            pass

    # 兜底：把最后 200 字当作答案
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    final_answer = lines[-1] if lines else text.strip()
    return {
        "answer": final_answer[:500],
        "reasoning": text.strip()[:1000],
    }


def solve_one_problem(client, problem_text: str, retries: int = MAX_RETRIES):
    """
    调用 Intern-S1 解一道题，带重试机制。
    """
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": problem_text},
                ],
                thinking_mode=True,
                temperature=0.2,
                max_tokens=4096,
            )
            raw_text = response.choices[0].message.content
            parsed = parse_answer(raw_text)
            return {
                "success": True,
                "answer": parsed["answer"],
                "reasoning": parsed["reasoning"],
                "raw_response": raw_text,
                "error": None,
            }
        except Exception as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # 指数退避：1秒、2秒、4秒
                print(f"  请求失败，{wait_time}秒后重试... 错误：{e}")
                time.sleep(wait_time)
            else:
                return {
                    "success": False,
                    "answer": "",
                    "reasoning": "",
                    "raw_response": "",
                    "error": str(e),
                }


def load_problems(input_path: str):
    """读取题目文件。"""
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_results(output_path: str):
    """加载已存在的结果，用于断点续跑。"""
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_results(results, output_path: str):
    """保存结果到 JSON 文件。"""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="批量数学解题")
    parser.add_argument("--input", default="sample_problems.json", help="输入题目文件路径")
    parser.add_argument("--output", default="results.json", help="输出结果文件路径")
    parser.add_argument("--start", type=int, default=0, help="从第几题开始（从0计数）")
    args = parser.parse_args()

    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输入文件：{args.input}")
    print(f"输出文件：{args.output}")

    # 读取题目
    problems = load_problems(args.input)
    total = len(problems)
    print(f"共读取 {total} 道题目")

    # 加载已有结果（断点续跑）
    results = load_existing_results(args.output)
    completed_ids = {r["idx"] for r in results if "idx" in r}
    print(f"已存在 {len(results)} 条结果，将跳过已完成的题目")

    # 创建客户端
    client = create_client()

    # 批量解题
    for idx, problem in enumerate(problems):
        if idx < args.start:
            continue

        problem_id = problem.get("id", f"prob_{idx:03d}")

        if problem_id in completed_ids:
            print(f"[{idx+1}/{total}] {problem_id} 已存在，跳过")
            continue

        print(f"\n[{idx+1}/{total}] 正在解答：{problem_id}")
        problem_text = problem.get("problem", "")

        result = solve_one_problem(client, problem_text)

        record = {
            "idx": idx,
            "status": "success" if result["success"] else "error",
            "final_response": result["answer"],
            "trace": [{"step": "reasoning", "content": result["reasoning"]}],
            "domain": problem.get("domain", ""),
            "error": result["error"] or None,
            "timestamp": datetime.now().isoformat(),
        }
        if result["error"]:
            record["error"] = {"type": "APIError", "message": result["error"]}

        results.append(record)
        completed_ids.add(problem_id)

        # 每道题后立即保存，防止中断丢失进度
        save_results(results, args.output)

        print(f"  状态：{'成功' if result['success'] else '失败'}")
        print(f"  答案：{result['answer'][:100]}...")

        # 限速：除了最后一题都等待
        if idx < total - 1:
            time.sleep(REQUEST_INTERVAL)

    print(f"\n完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"结果已保存到：{args.output}")
    print(f"成功：{sum(1 for r in results if r['success'])}/{total}")


if __name__ == "__main__":
    main()
