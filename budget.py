"""

════════════════════════════════════════════════════════
  时间预算管理 · 交半成品 > 交白卷
════════════════════════════════════════════════════════

   硬上限（total，默认 1080s）——永不调整
        │
   ┌────▼──────────────────┐
   │ 软预算 = total − reserve │  reserve 预扣收尾余量（默认 60s）
   └────┬──────────────────┘
        │
   ┌────▼─────────────┐
   │ 各阶段前检查软预算 │
   └────┬─────────────┘
        │ 不足
        ▼
   降级：减推理轮数 / 跳教学 / 返回已有结果

   硬上限 only 用来回答一个问题：「还能不能开始一次新的模型调用？」
   软预算 used 来决定：可选阶段（重试 / 复核 / 形态重述 / 叙述）买不买。

budget.py — 每题时间预算管理（防超时保输出）

新题难题可能超时（平台时限约 20min/题）。哲学：**交半成品 > 交白卷**——
预算内优先保证「有答案输出」，而非「完美推理」。各阶段前检查剩余，不足则
降级（减少推理轮数 / 跳过可选阶段 / 直接返回已有结果）。

软 / 硬两档的意义：
  只有一档预算时，可选阶段会把时间吃到见底，导致**已算出的答案来不及出厂**
  ——最亏的一种丢分。预扣 reserve 后，收尾阶段（清洗、形态整理、返回）
  始终有额度可用。

用法：
    b = TimeBudget(1080)              # 18 分钟，另预扣 60s 收尾
    if b.expired(margin=60): ...      # 软预算不足 60s，降级
    b.fast_path(need=300)             # 软预算不足以再做一次重活
    b.remaining_hard()                # 还能否开始一次新调用（不看 reserve）
    b.timeout_for(420)                # 把阶段上限钳到硬上限内
"""

import time


class TimeBudget:
    def __init__(self, total_s: float = 1080.0, reserve_s: float = 60.0):
        self.total = float(total_s)
        self.reserve = float(reserve_s)
        self.t0 = time.time()

    def elapsed(self) -> float:
        return time.time() - self.t0

    def remaining_hard(self) -> float:
        """硬上限剩余——**永不因难度 / 阶段而调整**。

        用来回答：「还能不能开始一次新的模型调用？」
        （进行中的调用不会被截断，所以判断必须用硬上限。）
        """
        return self.total - self.elapsed()

    def remaining(self) -> float:
        """软预算剩余——预扣收尾余量之后，可选阶段的「购买力」。"""
        return self.total - self.reserve - self.elapsed()

    def expired(self, margin: float = 0.0) -> bool:
        """软预算是否不足 margin 秒（含收尾余量）。"""
        return self.remaining() < margin

    def fast_path(self, need: float = 300.0) -> bool:
        """软预算不足以再完成一次 need 秒的重活。"""
        return self.remaining() < need

    def timeout_for(self, node_limit: float) -> float:
        """把某个阶段的上限钳到硬上限之内，返回实际可用的超时秒数。"""
        try:
            return max(1.0, min(float(node_limit), self.remaining_hard()))
        except Exception:
            return max(1.0, self.remaining_hard())
