"""client_tuning.py — 调优平台注入 client 的超时与重试

════════════════════════════════════════════════════════
  平台 client（默认 3×120s socket 超时 / 内层 retry=3）
        │
   ┌────▼─────────────┐
   │ timeout → 780s   │  只升不降（四路并行必然超 120s）
   │ retry   → 1      │  只降不升（3 内层 × 3 外层 = 9 次请求）
   └────┬─────────────┘
        │  best-effort：属性缺失 / 只读 / 非数值 → 静默跳过
        ▼
   返回报告 dict（本模块任何情况都不抛异常）
════════════════════════════════════════════════════════

为什么需要：
  - 官方 client 内置 3×120s 的 socket 超时。单次深度推理调用本就要 77~116s，
    多路并行（多候选采样 / 求解 + 验证）时必然超过 120s，表现为
    「reasoning: failed at 363s」——正好是 3×120s。
    把 socket 超时抬到 780s，给一次完整推理留足余地。
  - 官方 client 内层自带 retry=3，与我们的外层重试叠乘：
    3 内层 × 3 外层 = 最多 9 次真实请求，单节点就能打穿一道题的全部时间预算。
    把内层压到 1，重试权收归外层（外层知道剩余时间，能判断"买不买得起"）。

安全约束：
  - **只升不降**（timeout）/ **只降不升**（retry）——绝不把平台配置改得更差；
  - 属性不存在、只读、类型不对，一律静默跳过；
  - 全程 try/except，**永不抛异常**——调优失败绝不能影响解题。
"""

from __future__ import annotations

#: 目标 socket 超时（秒）。单次推理 77~116s，多路并行留足余量。
DESIRED_SOCKET_TIMEOUT_S = 780.0

#: 目标内层重试次数。外层已有感知剩余时间的重试，内层禁止叠乘。
MAX_INTERNAL_RETRIES = 1


def _adjust_number(client, name: str, value: float, direction: str):
    """best-effort 调整个数值属性，返回 (before, after)；不可调则返回 (None, None)。

    direction: "up" = 只升不降；"down" = 只降不升。
    """
    try:
        before = getattr(client, name, None)
        if before is None or isinstance(before, bool) or not isinstance(before, (int, float)):
            return None, None
        if direction == "up" and value <= before:
            return before, before          # 已达标，不动
        if direction == "down" and value >= before:
            return before, before
        setattr(client, name, value)
        return before, value
    except Exception:
        return None, None                  # 只读属性 / 自定义 __setattr__ → 静默跳过


def tune_platform_client(client) -> dict:
    """抬高 socket 超时 + 压制内层重试。返回调优报告，**永不抛异常**。

    参数：
      client: 平台注入的模型客户端（可能为 None）

    返回：
      dict: {"timeout": {"before": .., "after": ..}, "retry": {...}}，
            未调整的项不出现在结果里。
    """
    report: dict = {}
    if client is None:
        return report
    before, after = _adjust_number(client, "timeout", DESIRED_SOCKET_TIMEOUT_S, "up")
    if before is not None:
        report["timeout"] = {"before": before, "after": after}
    before, after = _adjust_number(client, "retry", MAX_INTERNAL_RETRIES, "down")
    if before is not None:
        report["retry"] = {"before": before, "after": after}
    return report
