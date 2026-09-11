"""
difficulty.py — 题目难度分类（L0 分流决策，移植折叠桌 difficulty.py 思想）

确定性规则、零 LLM：
  - hard：证明/构造/计数/博弈/微分方程/留数/求所有解…（论证链长、需搜索）
  - easy：短计算题（求导/积分/极限/数值计算，题面短）
  - medium：其余

用途：按难度分流推理资源——easy 减少推理轮数省时；hard 保留完整多轮 + 工具。
"""

import re

# 硬题标记（长链推理 / 需构造 / 需证明 / 计数枚举）
_HARD_MARKERS = re.compile(
    r"证明|求证|推导|论证|构造|计数|组合数|排列数|微分方程|通解|留数|曲率|正规子群|"
    r"热方程|协方差函数|算子范数|开覆盖|线性规划|求所有|所有可能|全部|是否|当且仅当|"
    r"prove|construct|counterexample|bijection|induction|differential equation|residue|"
    r"find all|all possible|all functions|all pairs|all values|determine all|show that|"
    r"count|counting|enumerate|number of|how many|winning|optimal|maximum|minimum|"
    r"determine the|compute the number",
    re.IGNORECASE,
)

# 简单计算标记（短计算题）
_EASY_MARKERS = re.compile(
    r"计算|求导|求积分|求极限|求值|化简|代入|数值|近似|展开|calculate|compute|evaluate|"
    r"simplify|derivative|integral|limit|approximate",
    re.IGNORECASE,
)


def classify_difficulty(problem: str, is_proof: bool = False) -> str:
    """返回 "easy" / "medium" / "hard"。"""
    p = problem or ""
    if is_proof:
        return "hard"
    if _HARD_MARKERS.search(p):
        return "hard"
    # 短计算题 → easy（题面短 + 计算词）
    if len(p) <= 60 and _EASY_MARKERS.search(p):
        return "easy"
    return "medium"
