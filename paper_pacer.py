"""paper_pacer.py — 全卷预算池（防"整卷跑不完"）

════════════════════════════════════════════════════════
  全卷硬限（默认 6h = 21600s） ÷ 剩余题数
        │
   ┌────▼──────────────────┐
   │ 预测总耗时 > 全卷×1.15？ │  落后
   │ 或 均摊 < MIN_SOFT？     │
   └────┬──────────┬────────┘
        │是         │否
        ▼           ▼
   cap = 均摊      给满 IDEAL
   （不低于 MIN_SOFT）
        │
        └──→ 单题软预算 = min(难度档, cap)
════════════════════════════════════════════════════════

为什么需要（真实教训）：
  早期「每题固定 1200s」的配置，在官方环境跑出了 **11 小时 19 分**、
  112 题只完成 **16 题**、accuracy 0.1429 的结果——因为完全没有全卷视角。
  单题预算再合理，只要题数 × 单题预算 > 全卷时限，后段题目就只能交白卷。

设计要点：
  - **纯时间池**：只管「题数 × 时间」，不管并发（并发由平台 / 线程池控制）；
  - **隐式回收**：某题少花的时间会让后面的均摊自然变大，不需要显式归还队列；
  - **只收紧不放宽**：与题目难度档取 min，绝不把预算改大。
"""

from __future__ import annotations

import os
import threading
import time


class PaperPacer:
    """全卷预算池（单例）。"""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, total_s: float = 21600.0, planned: int = 100,
                 ideal: float = 1200.0, min_soft: float = 300.0,
                 concurrency: int = 3, slack: float = 1.0):
        self.total = float(total_s)
        self.planned = int(planned)
        self.ideal = float(ideal)
        self.min_soft = float(min_soft)
        #: 平台并发数。**必须考虑**：并发 3 时，同样一段墙上时间可以并行推进
        #: 3 道题，单题可用时间是「剩余时间÷剩余题数」的 3 倍。
        #: 忽略并发会把预算算成 1/3，把流水线腰斩。
        self.concurrency = max(1, int(concurrency))
        #: 落后判定的容忍系数。1.0 = 预测会超时就收紧。
        #: 取 >1 意味着"允许超时 X 成"——实测 623s/题已经是 6.46h（超 8%），
        #: 若沿用 1.15，池子根本不会介入，形同虚设。
        self.slack = float(slack)
        self.t0 = time.time()
        self.done = 0
        self._started = set()

    # ── 单例 ──
    @classmethod
    def get_instance(cls) -> "PaperPacer":
        with cls._lock:
            if cls._instance is None:
                total = float(os.environ.get("MATH_AGENT_PAPER_SECONDS", 21600))
                planned = int(os.environ.get("MATH_AGENT_PAPER_PLANNED", 100))
                conc = int(os.environ.get("MATH_AGENT_PAPER_CONCURRENCY", 3))
                slack = float(os.environ.get("MATH_AGENT_PAPER_SLACK", 1.0))
                cls._instance = PaperPacer(total_s=total, planned=planned,
                                           concurrency=conc, slack=slack)
            return cls._instance

    def reset(self, total_s: float = None, planned: int = None) -> None:
        """每卷评测开始前调用一次（清空进度、重置计时起点）。"""
        with type(self)._lock:
            if total_s is not None:
                self.total = float(total_s)
            if planned is not None:
                self.planned = int(planned)
            self.t0 = time.time()
            self.done = 0
            self._started = set()

    # ── 进度登记 ──
    def mark_started(self, idx) -> None:
        with type(self)._lock:
            self._started.add(idx)

    def mark_done(self) -> None:
        """**无论成功失败都必须调用**——否则题数统计失真，池子会算错。"""
        with type(self)._lock:
            self.done += 1

    # ── 预算 ──
    def budget_for(self, idx=None) -> float:
        """返回该题允许的软预算（秒）。"""
        with type(self)._lock:
            elapsed = time.time() - self.t0
            remaining_time = self.total - elapsed
            remaining_problems = max(1, self.planned - self.done)
            done = self.done
            planned = self.planned
            total = self.total
            concurrency = self.concurrency

        # 落后判定①：按当前速度外推，整卷墙上时间会超时 15% 以上。
        # elapsed/done 是「每题平均墙上耗时」——墙上时间已经内含并发重叠，
        # 乘以题数就是整卷墙上总时长，此处**不能再乘并发**。
        behind = False
        if done > 0:
            pace = elapsed / done
            if pace * planned > total * self.slack:
                behind = True

        # 单题可用预算 = 剩余墙上时间 × 并发 ÷ 剩余题数
        # （并发 N 时，剩余的墙上时间里可以并行推进 N 道题）
        per_problem = remaining_time * concurrency / remaining_problems

        # 落后判定②：均摊已低于保底
        if per_problem < self.min_soft:
            behind = True

        if not behind:
            return self.ideal
        return max(self.min_soft, per_problem)

    def snapshot(self) -> dict:
        """供日志/排查：全卷进度快照。"""
        with type(self)._lock:
            elapsed = time.time() - self.t0
            done = self.done
            planned = self.planned
            total = self.total
        remaining_problems = max(0, planned - done)
        return {
            "total_planned": planned,
            "done": done,
            "remaining_problems": remaining_problems,
            "elapsed_s": round(elapsed, 1),
            "remaining_s": round(total - elapsed, 1),
            "pace_s_per_problem": round(elapsed / done, 1) if done else None,
            "budget_now": round(self.budget_for(), 1),
        }
