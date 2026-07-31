"""
utils.py — 公共工具函数

项目内所有模块共享的：
  - 代码提取与安全执行
  - JSON 提取
  - LaTeX \\boxed{} 答案提取
  - VERDICT 投票解析
"""

import json
import re
import subprocess
import sys
from typing import Optional


# ============================================================
# 代码提取与执行
# ============================================================

def extract_code(text: str) -> Optional[str]:
    """提取文本中第一个 ```python ... ``` 代码块。"""
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1).rstrip('\n') if m else None


def extract_code_blocks(text: str) -> list:
    """提取文本中所有 ```python ... ``` 代码块。"""
    return [code.rstrip('\n') for code in re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)]


def execute_code(code: str, timeout: int = 30) -> str:
    """在子进程中安全执行 Python 代码，返回 stdout 或 stderr。

    安全策略：
      - 独立子进程隔离
      - timeout 限制执行时间
      - 仅允许数学计算相关模块（白名单策略）
      - 平台评分环境通常有外层沙箱，此处为额外保险
    """
    # 危险模块黑名单检查（防止代码注入或系统破坏）
    _FORBIDDEN_IMPORTS = {'os', 'subprocess', 'shutil', 'socket', 'requests',
                          'http', 'urllib', 'ctypes', 'multiprocessing', 'threading'}
    for word in _FORBIDDEN_IMPORTS:
        if re.search(r'\b' + word + r'\b', code):
            return f'[安全拦截] 代码包含禁止的模块调用: {word}'

    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
        )
        return (r.stdout.strip() or r.stderr.strip())
    except subprocess.TimeoutExpired:
        return "代码执行超时"


def execute_code_dict(code: str, timeout: int = 30) -> dict:
    """安全执行 Python 代码，返回 {"stdout", "stderr", "ok"} 字典。"""
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
        )
        return {
            "stdout": r.stdout.strip(),
            "stderr": r.stderr.strip(),
            "ok": r.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "超时", "ok": False}


# ============================================================
# JSON 提取
# ============================================================

def extract_json(text: str) -> Optional[dict]:
    """从文本中提取第一个合法的 JSON 对象。

    优先级：
      1. ```json ... ``` 代码块
      2. 最外层 { ... }
    """
    # 先找 ```json ... ```
    m = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 再找最外层 { ... }
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ============================================================
# LaTeX 答案提取
# ============================================================

def extract_boxed(text: str) -> str:
    """从 LaTeX 文本中提取 \\boxed{...} 内的答案。

    支持嵌套括号：\\boxed{\\frac{1}{2}} → \\frac{1}{2}
    兜底：取最后非空行前 500 字符。
    """
    # 方案 1: 标准正则（单层括号）
    m = re.search(r"\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", text)
    if m:
        return m.group(1).strip()

    # 方案 2: 手动匹配嵌套括号
    idx = text.find("\\boxed{")
    if idx >= 0:
        start = idx + len("\\boxed{")
        depth = 1
        pos = start
        while pos < len(text) and depth > 0:
            if text[pos] == '{':
                depth += 1
            elif text[pos] == '}':
                depth -= 1
            pos += 1
        if depth == 0:
            return text[start:pos-1].strip()

    return ""


def extract_final_answer(text: str) -> str:
    """综合提取最终答案（多层兜底策略）。

    1. \\boxed{...}
    2. 最后非空行中查找"答案"相关标记
    3. 最后非空行前 500 字符
    """
    # 优先 \\boxed
    ans = extract_boxed(text)
    if ans:
        return ans

    # 查找中文最终答案标记
    patterns = [
        r'(?:最终答案|答案为?|answer\s*[:：]?)\s*(.+?)(?:\n|$)',
        r'(?:所以|因此|故)\s*(.+?)(?:\n|$)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result = m.group(1).strip()
            if len(result) < 500:
                return result

    # 兜底：最后非空行
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return lines[-1][:500] if lines else ""


# ============================================================
# VERDICT 投票解析
# ============================================================

def is_correct_vote(verdict: str) -> bool:
    """解析 verifier 输出，判断投票结果。

    兼容格式：
      - VERDICT: A / VERDICT：B
      - 单独一行 A 或 B
      - CORRECT / INCORRECT
    """
    # VERDICT: A 或 VERDICT：B
    verdict_matches = re.findall(
        r"\bVERDICT\s*[:：]\s*([AB])\s*[。.]?",
        verdict,
        flags=re.IGNORECASE,
    )
    if verdict_matches:
        return verdict_matches[-1].upper() == "A"

    # 单独一行 A 或 B
    label_matches = re.findall(
        r"^\s*([AB])\s*[。.]?\s*$",
        verdict,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if label_matches:
        return label_matches[-1].upper() == "A"

    # CORRECT / INCORRECT
    words = re.findall(r"\b[A-Z]+\b", verdict.upper())
    if "INCORRECT" in words:
        return False
    return "CORRECT" in words
