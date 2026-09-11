"""
budget.py — 每题时间预算管理（防超时保输出）

新题难题可能超时（平台时限约 20min/题）。哲学：**交半成品 > 交白卷**——
预算内优先保证「有答案输出」，而非「完美推理」。各阶段前检查剩余，不足则
降级（减少推理轮数 / 跳过可选阶段 / 直接返回已有结果）。

用法：
    b = TimeBudget(1080)          # 18 分钟预算（留 2 分钟收尾）
    if b.expired(margin=60): ...  # 剩余不足 60s，降级
    b.fast_path(need=300)          # 剩余不足以再做一次重活
"""

import time


class TimeBudget:
    def __init__(self, total_s: float = 1080.0):
        self.total = float(total_s)
        self.t0 = time.time()

    def elapsed(self) -> float:
        return time.time() - self.t0

    def remaining(self) -> float:
        return self.total - self.elapsed()

    def expired(self, margin: float = 0.0) -> bool:
        """剩余时间是否不足 margin 秒（含收尾余量）。"""
        return self.remaining() < margin

    def fast_path(self, need: float = 300.0) -> bool:
        """剩余时间不足以再完成一次 need 秒的重活。"""
        return self.remaining() < need
