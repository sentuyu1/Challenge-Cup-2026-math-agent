"""
批量数学解题脚本（直接调用 Intern-S1 API）

功能：
1. 读取 JSON 格式的题目文件
2. 逐题调用 Intern-S1 模型
3. 解析模型输出中的答案
4. 保存为比赛要求的目录式 JSON 结果格式（outputs/0.json, 1.json, ...）
5. 支持断点续跑（已存在的 idx.json 自动跳过）
6. 支持并发调用（默认 8 路） + 自动限速

使用方法：
1. 确保 .env 文件中配置了 INTERN_API_KEY
2. 准备好题目文件（如 sample_problems.json）
3. 运行：python batch_solver.py --input_file sample_problems.json --output_dir outputs
"""

import asyncio
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
API_KEY = os.environ.get("INTERN_API_KEY")
BASE_URL = "https://chat.intern-ai.org.cn/api/v1/"
MODEL = "intern-s2-preview"  # 默认使用 S2 以获得最佳数学推理能力

# 并发控制（对齐 baseline）
LOCAL_MAX_CONCURRENCY = int(os.environ.get("LOCAL_MAX_CONCURRENCY", "8"))
REQUEST_INTERVAL = 0.5  # 并发模式下缩短间隔，主要靠 semaphore 控制
MAX_RETRIES = 3

SYSTEM_PROMPT = """你是一名数学解题专家。请按以下步骤解决题目：
1. 仔细阅读题目，理解已知条件和求解目标；
2. 进行逐步推理，必要时使用数学符号和公式；
3. 给出最终答案；
4. 最后用 \\boxed{答案} 的 LaTeX 格式输出最终答案。

注意：
- 最终答案必须放在 \\boxed{} 中；
- 推理过程尽量详细清晰。
"""


def create_client():
    """创建 OpenAI 客户端。"""
    if not API_KEY:
        raise ValueError("请先配置 INTERN_API_KEY 环境变量或在 .env 文件中设置")
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def parse_answer(text: str):
    """
    从模型输出中提取答案和推理过程。
    优先解析 \\boxed{}，兜底用最后非空行。
    """
    from utils import extract_boxed

    # 优先 \\boxed{}
    boxed = extract_boxed(text)
    if boxed:
        return {
            "answer": boxed,
            "reasoning": text.strip()[:2000],
        }

    # 兜底：把最后 200 字当作答案
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    final_answer = lines[-1] if lines else text.strip()
    return {
        "answer": final_answer[:500],
        "reasoning": text.strip()[:2000],
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
                temperature=0.2,
                max_tokens=16384,
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
    """读取题目文件（支持 JSON 数组或 JSONL）。"""
    with open(input_path, "r", encoding="utf-8") as f:
        # 尝试 JSON 数组
        content = f.read().strip()
        if content.startswith("["):
            return json.loads(content)
        # JSONL 格式：每行一个 JSON
        problems = []
        for line in content.split("\n"):
            line = line.strip()
            if line:
                problems.append(json.loads(line))
        return problems


def save_single_result(output_dir: str, idx: int, record: dict):
    """保存单题结果到 output_dir/{idx}.json（对齐基线目录格式）。"""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{idx}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def check_existing(output_dir: str, idx: int) -> bool:
    """检查某题结果是否已存在且非空（用于断点续跑）。"""
    filepath = os.path.join(output_dir, f"{idx}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 文件存在且有内容 → 跳过
            if data:
                return True
        except (json.JSONDecodeError, IOError):
            pass
    return False


def main():
    parser = argparse.ArgumentParser(description="批量数学解题")
    parser.add_argument("--input_file", default="sample_problems.json", help="输入题目文件路径")
    parser.add_argument("--output_dir", default="outputs", help="输出目录（每题的 idx.json）")
    parser.add_argument("--start", type=int, default=0, help="从第几题开始（从0计数）")
    parser.add_argument("--concurrency", type=int, default=LOCAL_MAX_CONCURRENCY, help="并发数")
    args = parser.parse_args()

    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输入文件：{args.input_file}")
    print(f"输出目录：{args.output_dir}")
    print(f"并发数：{args.concurrency}")

    # 读取题目
    problems = load_problems(args.input_file)
    total = len(problems)
    print(f"共读取 {total} 道题目")

    # 统计已完成的题目（断点续跑）
    skipped_count = sum(1 for i in range(total) if check_existing(args.output_dir, i))
    if skipped_count > 0:
        print(f"已存在 {skipped_count} 条结果，将跳过已完成的题目")

    # 创建客户端
    client = create_client()

    # ── 异步并发主循环 ──
    semaphore = asyncio.Semaphore(args.concurrency)
    success_count = 0
    fail_count = 0

    async def process_one(idx: int, problem: dict):
        nonlocal success_count, fail_count

        if check_existing(args.output_dir, idx):
            print(f"[{idx+1}/{total}] idx={idx} 已存在，跳过")
            return

        async with semaphore:
            print(f"\n[{idx+1}/{total}] 正在解答：idx={idx}")
            problem_text = problem.get("problem", "")

            result = await asyncio.to_thread(solve_one_problem, client, problem_text)

            # 对齐 baseline 输出格式: idx / status / final_response / trace / error
            if result["success"]:
                record = {
                    "idx": idx,
                    "status": "success",
                    "final_response": result["answer"],
                    "trace": [{"step": "solve", "content": result["reasoning"]}],
                }
                success_count += 1
            else:
                record = {
                    "idx": idx,
                    "status": "error",
                    "final_response": "",
                    "error": {
                        "type": "APIError",
                        "message": result["error"] or "未知错误",
                    },
                    "trace": [],
                }
                fail_count += 1

            # 每道题后保存为独立文件（对齐基线 outputs/{idx}.json）
            await asyncio.to_thread(save_single_result, args.output_dir, idx, record)

            status_text = '成功' if result['success'] else '失败'
            print(f"  状态：{status_text}")
            print(f"  答案：{result['answer'][:100]}...")

    async def run_all():
        tasks = [process_one(idx, p) for idx, p in enumerate(problems) if idx >= args.start]
        await asyncio.gather(*tasks)

    asyncio.run(run_all())

    print(f"\n完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"结果已保存至：{args.output_dir}/")
    print(f"成功：{success_count}，失败：{fail_count}，跳过：{skipped_count}")


if __name__ == "__main__":
    main()
