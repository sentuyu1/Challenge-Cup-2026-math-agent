"""知识图谱：18 个竞赛数学题型节点。

用途：供 user_agent.py 在题型识别后检索该题型的完整方法论，作为提示词注入模型。
设计：纯本地、纯文本、无 embedding / 无向量库 / 零 API 调用。
检索粒度 = 题型节点级（key = DOMAIN_CN_TO_EN 中的英文字段名，与 user_agent.domain 对齐）。
兜底：domain 为 other / 空 / 不在表内 / 节点缺失时返回空串，绝不抛异常。

扩展：P2 爬虫可生成 kg_cache/{cache_key}.json 的扩展题解缓存，_merge_extension 加载时静默并入。
"""
from dataclasses import dataclass, field
from typing import Optional
import os
import json
import re

__all__ = [
    "KGNode", "retrieve_kg", "get_kg_node", "all_kg_domains", "kg_stats",
]

# ===================== 数据结构 =====================

@dataclass
class KGNode:
    """题型节点：18 个竞赛数学子领域的方法论知识图谱。"""
    domain_en: str                 # 英文字段名（检索键，与 user_agent 的 domain 一致）
    domain_cn: str                 # 中文题型名
    methods: list                  # 核心方法（短句）
    theorems: list                 # 常用定理 / 关键结论
    flow: list                     # 标准求解流程（编号分步，可直接当执行蓝图）
    pitfalls: list                 # 常见陷阱：现象→原因→对策
    examples: list                 # 典型范式：题目原型 + 适用条件 + 首推方法（不给完整解）
    related_domains: list          # 关联题型（英文字段名）
    disambiguation: list = field(default_factory=list)  # 实体消歧：跨题型共享概念在本题型语境下的含义/区别
    cache_key: str = ""            # 扩展缓存键；"" 表示无扩展缓存
    examples_cache: list = field(default_factory=list)  # 扩展题解缓存 [{"title","url","source","method","solution"}]

# ===================== 节点存储 =====================

_KG_NODES: dict = {}
_REFINED: dict = {}   # 扩展钩子：子关键词 -> 附加提示（当前为空，保留接口）

# ===================== 18 个题型节点 =====================

_KG_NODES["algebra"] = KGNode(
    domain_en="algebra",
    domain_cn="代数",
    methods=[
        "对称多项式与韦达定理：把高次对称式化为初等对称式的多项式",
        "换元降次：整体代换、对称代换、三角换元，消去根式或高次项",
        "因式分解：试根/有理根定理、待定系数、分组分解与最高公因式",
        "不等式：判别式、Cauchy、均值、琴生；先证恒等再证不等",
        "特征根处理：多项式方程的根与系数关系，构造对偶式",
    ],
    theorems=[
        "韦达定理：n 次方程根与系数的关系",
        "因式定理：f(a)=0 ⇔ (x-a)|f(x)",
        "基本/均值不等式、柯西不等式、琴生不等式（凸函数）",
        "对称多项式基本定理：任意对称式可用初等对称式表示",
    ],
    flow=[
        "1. 看是方程、恒等式还是不等式，先化简并标明定义域",
        "2. 识别对称性/周期性，引入初等对称式或整体换元",
        "3. 降次或用定理（韦达/因式定理）建立方程/不等式链",
        "4. 解出后回代验证，排除增根与定义域外解",
    ],
    pitfalls=[
        "换元未回代原变量范围，导致求值/求范围错误；先确定换元的取值范围",
        "不等式放缩方向反了：比较大小前先判断正负",
        "高次根丢失：约去因子时需确认不为零方根",
    ],
    examples=[
        "对称多项式求值（知 xy+… 求和）：用初等对称式化简",
        "含参二次不等式的恒成立：转判别式＋端点分析",
        "分式/根式函数求值域：换元＋单调性",
    ],
    related_domains=["linear_algebra", "number_theory", "calculus"],
    disambiguation=[
        '多项式 —— 代数中强调根与系数、因式分解与韦达；数值分析里它是逼近对象，数学物理里的多项式频率指数是单项式幂次',
        '不等式 —— 代数侧重代数式放缩(均值/Cauchy/琴生)；运筹学里不等式是约束条件，数值分析里常用于误差界，三语境不同',
        '域(field) —— 代数指四则运算封闭的集合；拓扑/复分析里\'域\'多指连通开区域，勿按代数含义误读',
        '根(root) —— 代数指方程解/多项式零点；数值分析\'求根\'指迭代逼近解，数学AI里根还可能指根式，注意语境',
    ],
cache_key="algebra",
)

_KG_NODES["linear_algebra"] = KGNode(
    domain_en="linear_algebra",
    domain_cn="线性代数",
    methods=[
        "行/列变换与初等变换、阶梯形，解线性方程组与求秩",
        "矩阵运算与逆：伴随/初等变换求逆；分块技巧",
        "特征值特征向量、对角化、Jordan 型、最小多项式",
        "二次型：配方法/合同变换化标准形，正定判定（顺序主子式）",
        "秩-零化度定理：rank(A)+dim ker A = n",
    ],
    theorems=[
        "Cayley-Hamilton：矩阵满足其特征多项式",
        "谱定理：实对称矩阵可正交对角化，特征值全实",
        "最小多项式整除特征多项式；对角化 ⇔ 最小多项式无重根（复数域）",
        "正定的等价条件：顺序主子式全正 / 特征值全正 / 存在 P 使 A=P^T P",
    ],
    flow=[
        "1. 明确对象与运算空间，写出行列式/矩阵/方程组的维度关系",
        "2. 优先用秩-零化度、特征值等抽象工具，再考虑硬算",
        "3. 对称矩阵先用谱定理降维；二次型先判断是否正定",
        "4. 代入验证结果满足原方程/原条件",
    ],
    pitfalls=[
        "逆矩阵存在条件忘记行列式 ≠ 0",
        "混淆矩阵乘法次序，非交换性质算错（AB≠BA）",
        "特征向量归一化误用转置而非共轭转置（复情形）",
    ],
    examples=[
        "给特征方程求特征值/重数：最小多项式判别是否可对角化",
        "二次型正定性：顺序主子式判定",
        "矩阵方程 AX=B：两边同乘逆/初等行变换",
    ],
    related_domains=["abstract_algebra", "algebra", "functional_analysis"],
    disambiguation=[
        '矩阵 —— 线性代数是线性变换的表示；数值分析里是可数值消元/分解的对象；数学物理里变换矩阵是基变换工具，维度与稠密性语境不同',
        '特征值 —— 线性代数是理论(特征多项式/对角化)；数值分析用幂迭代/QR 近似求；两者都叫 eigenvalue 但一个是精确理论一个是数值逼近',
        '维数(dimension) —— 线性代数指基底元素个数；微分几何/拓扑里是流形/空间维度，勿混',
        '正交 —— 线性空间内积为零(向量)；统计正交试验是实验设计；复矩阵用共轭转置，注意实数/复数语境',
    ],
cache_key="linear_algebra",
)

_KG_NODES["calculus"] = KGNode(
    domain_en="calculus",
    domain_cn="微积分",
    methods=[
        "求导法则、链式、隐函数与参数方程求导",
        "不定/定积分：分部积分、换元、分部分式、三角替换",
        "级数：比值/根值审敛、幂级数收敛半径、泰勒展开",
        "极限：洛必达、等价无穷小、夹逼、Taylor 展开定阶",
        "应用到极值/单调性/凹凸性：求导后零点与符号判",
    ],
    theorems=[
        "微积分基本定理：积分与导数互逆",
        "洛必达法则（0/0、∞/∞ 保序）",
        "Taylor 中值定理与 Lagrange 余项",
        "级数审敛：p-级数、比较/比值/根值，交错级数 Leibniz",
        "常用麦克劳林展开及收敛条件：e^x、sin、cos、ln(1±x)、(1+x)^α",
        "Wallis 闭式：∫₀^{π/2} sin^n x dx 按 n 奇偶的阶乘比",
    ],
    flow=[
        "1. 判断是极限/导数/积分/级数，先写清收敛或可导前提",
        "2. 极限先用等价无穷小与 Taylor 定阶，规避洛必达循环",
        "3. 积分识别积分类型选法，注意换元边界变化",
        "4. 级数先判敛再求和；收敛半径用系数比值",
        "5. 结果回代数值整点验证",
    ],
    pitfalls=[
        "洛必达使用前提（0/0）不满足直接套用",
        "换元忘记改积分限；无穷积分/瑕积分判别前未分类",
        "级数首项/偏移进位错误，导致和式少项",
    ],
    examples=[
        "含参极限求参数：Taylor 展开到同阶比较",
        "分部积分求递推 I_n：找相邻项递推",
        "幂级数求和函数：先求导/积分化为等比",
    ],
    related_domains=["real_analysis", "differential_equations", "numerical_analysis"],
    disambiguation=[
        '极限 —— 微积分函数极限；实分析推广为更一般的收敛(序列/函数列)；测度论里涉及可测性，抽象层级递增',
        '积分 —— 微积分的 Riemann/不定积分；实分析 Lebesgue 积分覆盖更广；数学物理的积分变换(Laplace/Fourier)是算子而非求面积',
        '级数 —— 微积分幂级数/Taylor；实分析强调与范数/测度结合；数学物理里是特殊函数展开，求和与收敛判定语境不同',
        '导数 —— 微积分实值求导；泛函分析 Fréchet/Gâteaux 导数是算子；复分析里导数是解析的强性质，可导含义步步增强',
        '收敛 —— 微积分数列/函数项收敛；实分析强调逐点 vs 一致收敛；拓扑里由网/滤定义，注意判断收敛的准则不同',
    ],
cache_key="calculus",
)

_KG_NODES["complex_analysis"] = KGNode(
    domain_en="complex_analysis",
    domain_cn="复分析",
    methods=[
        "Cauchy-Riemann 方程判定解析性",
        "Cauchy 积分定理与积分公式：围道内被积函数性质",
        "留数定理计算围道积分：极点留数提取",
        "Laurent 展开与留数：孤立奇点分类",
        "共形映射：把区域映射到标准区域（单位圆/上半平面）",
    ],
    theorems=[
        "Cauchy 积分定理：区域单连通且 f 解析 → ∮f=0",
        "Cauchy 积分公式 f(a)=∮f(z)/(z-a) dz / (2πi)，高阶导数公式",
        "留数定理：∮_C f dz = 2πi Σ Res(f, 内部奇点)",
        "Liouville 定理：整函数有界则常数",
        "最大模原理、Schwarz 引理：整/有界解析函数取值受限证明常数或零点",
    ],
    flow=[
        "1. 判定 f 解析性（C-R 条件）与奇点位置/类型",
        "2. 围道积分先画路径与孤立奇点，判断内部包含哪些极点",
        "3. 提取留数：简单极点用极限、高阶用 Laurent/求导公式",
        "4. 应用留数定理求和，注意路径方向与实积分回退",
    ],
    pitfalls=[
        "C-R 方程误判解析点（需在邻域成立非单点）",
        "高阶极点留数求导公式次数记错",
        "积分路径半圆实部趋于 0 的前提（Jordan 引理）漏检",
    ],
    examples=[
        "计算实积分 ∫sinx/x：半圆围道 + Jordan 引理",
        "求 f 在 z0 的留数：判定奇点阶数再取公式",
        "共形映射到上半平面：先平移缩放再 Möbius",
    ],
    related_domains=["real_analysis", "calculus", "mathematical_physics"],
    disambiguation=[
        '解析/全纯 —— 复分析专指邻域可导的强性质(严格于实可导)；系统工程\'解析解\'指能写表达式；术语相同含义不同',
        '函数 —— 复分析里是复变函数(值域复平面)；代数里是映射；概率里随机变量；值域与可微意义各不相同',
        '映射 —— 复分析共形映射保角；拓扑/集合论里映射即函数的一般说法，勿把共形属性套用到一般映射',
    ],
cache_key="complex_analysis",
)

_KG_NODES["geometry"] = KGNode(
    domain_en="geometry",
    domain_cn="几何",
    methods=[
        "解析几何：建坐标系，用坐标/向量把几何条件方程化",
        "向量法：点积/叉积表达垂直、共线、面积、夹角",
        "三角法与正弦余弦定理：边角互相转化",
        "复数法与三角化：旋转、均匀缩放用乘复数表示",
        "初等几何：全等/相似、翻转/旋转对称、辅助线构型",
    ],
    theorems=[
        "余弦定理 c²=a²+b²-2ab cosC；正弦定理 a/sinA=b/sinB=2R",
        "面积公式：½bc sinA、海伦公式、向量叉积模/2",
        "中点坐标与距离公式、两点式方程",
        "圆幂定理、托勒密定理（四点共圆）",
    ],
    flow=[
        "1. 是平面/立体、求证/求值，先定坐标系或选主元",
        "2. 解析化：把已知几何条件翻译成方程/向量等式",
        "3. 用余弦/正弦定理代换边角，或用向量关系消元",
        "4. 解出目标量，回代验证几何关系确满足",
    ],
    pitfalls=[
        "坐标法忘记写两直线垂直/平行的斜率条件",
        "错代角的对边，正弦/余弦定理误配边角",
        "面积/体积公式漏掉 1/2 或 1/3 系数",
    ],
    examples=[
        "求三角形面积：已知两边夹角用 ½bc sinA",
        "证明垂直/平行：向量点积为 0 / 叉积为 0",
        "解析几何求轨迹：设动点坐标消参",
    ],
    related_domains=["algebra", "linear_algebra", "calculus"],
    disambiguation=[
        '空间 —— 几何指 Euclid 平面/立体空间可建坐标系；拓扑\'空间\'是带拓扑结构的集合(更抽象)；泛函空间是函数集合，层级不同',
        '距离 —— 几何是实际度量(线段长)；度量空间\'度量\'是满足公理的抽象函数；泛函范数距离在无穷维，语义从具体到抽象',
        '度(degree)/角 —— 几何角度；图论节点\'度\'是邻边数；多项式次数也称 degree，一词多义按领域定',
        '球面 —— 几何三维球面；拓扑/微分几何里球面是紧流形(S^n)，侧重拓扑不变性与曲率，非仅三维形状',
    ],
cache_key="geometry",
)

_KG_NODES["number_theory"] = KGNode(
    domain_en="number_theory",
    domain_cn="数论",
    methods=[
        "同余与模运算：把大数问题模化",
        "素数分解与唯一分解定理求 gcd/lcm",
        "丢番图方程：模 mod 约束、不等式夹逼、因数分解法",
        "中国剩余定理求同余方程组",
        "费马小定理/欧拉定理降指数",
    ],
    theorems=[
        "唯一分解（算术基本定理）",
        "费马小定理 a^(p-1)≡1 (mod p)，欧拉定理推广",
        "中国剩余定理：互素模的同余系统解唯一 mod 积",
        "整除性：a|bc 且 (a,b)=1 ⟹ a|c",
        "费马/欧拉指数降阶 + 平方剩余、二次互反率（判定二次同余）",
    ],
    flow=[
        "1. 先看模几最有效，常用小素数(2,3,5,7)模判奇偶/整除",
        "2. 对式子做素数分解，比较指数",
        "3. 解同余方程用 CRT；丢番图用整除/因式分解夹逼",
        "4. 验证所有剩余类，防漏解或增解",
        "5. 指数巨大先欧拉定理降阶到模周期；平方问题试二次剩余判定",
    ],
    pitfalls=[
        "模运算指数不降就用欧拉，需化到互素情形",
        "解同余方程漏掉模的周期，gcd(m)倍",
        "丢番图放大缩小过于激进丢掉整数解",
        "把 a/b 当整数用：需先证整除才可作商",
    ],
    examples=[
        "求模幂 a^b mod m：分解 + 费马小定理降指数",
        "解同余方程组：互素模用 CRT",
        "证明某数为平方数：先看模 4/模 8 残差",
    ],
    related_domains=["abstract_algebra", "combinatorics"],
    disambiguation=[
        '模(modulo)/模数 —— 数论同余的模；抽象代数\'模(module)\'是环上代数结构，两个\'模\'是不同概念勿混淆',
        '阶(order) —— 数论指模周期(乘法阶)；群论\'阶\'指群/元素个数；微分方程\'阶\'是导数最高阶，多义词',
        '整除 —— 数论的整除关系；多项式环里也有整除；抽象代数环里整除在商结构中有更多，注意所在环',
        '数(number) —— 数论的整数/素数性质；实/复分析里是实数/复数；数学物理里数可能带物理单位，语义域不同',
    ],
cache_key="number_theory",
)

_KG_NODES["combinatorics"] = KGNode(
    domain_en="combinatorics",
    domain_cn="组合数学",
    methods=[
        "计数原理：加法/乘法原理、排列组合与二项式",
        "生成函数：把数列计数编码成幂级数",
        "递推关系：列递推、特征方程求解",
        "容斥原理：多集合计数相互减并",
        "Pigeonhole/双向计数：存在性与下界",
    ],
    theorems=[
        "二项式定理 (1+x)^n=ΣC(n,k)x^k",
        "容斥原理：交并计数",
        "Catalan/Stirling 数等常见计数对象",
        "有限射影/图计数的极值如 Erdős–Moser 类",
    ],
    flow=[
        "1. 决定是否有序（排列/组合），是否可重复（多项式）",
        "2. 大计数优先用生成函数或递推，不逐项枚举",
        "3. 有重叠集合用容斥",
        "4. 核对小规模特例（n=1,2,3）验证公式",
    ],
    pitfalls=[
        "重复计数：对象顺序没去重",
        "生成函数收尾忘按系数提取",
        "递推缺少初始项，导致整体偏移",
    ],
    examples=[
        "路径计数：递推/公式 C",
        "受限排列计数：容斥",
        "生日/鸽巢存在性：pigeonhole 论证",
    ],
    related_domains=["probability", "graph_theory", "number_theory"],
    disambiguation=[
        '图 —— 组合数学把它当计数对象之一(如 Cayley 公式)；图论里图是专门研究对象(顶点+边)；机器学习图模型是条件独立结构，域不同',
        '树 —— 组合计数应用；图论里树是连通无圈图；数据结构里树是计算机组织；本图谱更接近图论，注意题设',
        '组合 —— 组合数学纯计数/排列；运筹\'组合优化\'是选物筹目标；算法\'组合\'是数据结合，注意问的是求解还是计数',
        '递推 —— 组合数字序列递推；动态规划递推是状态转移优化；运筹学递推是优化步，方法与目标不同',
    ],
cache_key="combinatorics",
)

_KG_NODES["graph_theory"] = KGNode(
    domain_en="graph_theory",
    domain_cn="图论",
    methods=[
        "识别图类型：树、二分图、平面图、正则图",
        "最短路径 Dijkstra/BFS；最小生成树 Prim/Kruskal",
        "最大匹配 Hall 定理/增广路",
        "欧拉/哈密顿回路存在性判定",
        "图染色、二分性（奇圈）判断",
    ],
    theorems=[
        "握手定理：度数和 = 2|E|",
        "树满足 |E|=|V|-1",
        "二分图 ⇔ 无奇数圈；König 定理（匹配=顶点覆盖）",
        "平面图 Euler 公式 V-E+F=2",
    ],
    flow=[
        "1. 建图：把题条件转成顶点/边",
        "2. 判断目标问题类型（最短路/匹配/覆盖/连通性）",
        "3. 选算法或定理，注意图是否加权/有向",
        "4. 小示例手推验证",
    ],
    pitfalls=[
        "Dijkstra 用于负权会错；负权需 Bellman-Ford",
        "二分图误判：需无奇圈",
        "度数和奇校验漏加",
    ],
    examples=[
        "求两点最短路径：无负权 Dijkstra",
        "二分图最大匹配：增广路",
        "判断可达/连通分量：BFS/DFS",
    ],
    related_domains=["combinatorics", "operations_research"],
    disambiguation=[
        '图 —— 图论专指顶点+边的离散结构(研究对象)；组合数学里是计数辅助；机器学习里是数据表示，域不同',
        '路径(path) —— 图论指顶点/边序列；积分路径是平面/线积分路径；拓扑里路径是同伦中的闭路径变形，定义各异',
        '度(degree) —— 图论节点邻边数；多项式次数、几何角度、数论周期也用 degree，按图论语境读',
        '距离 —— 图论边数/加权最短路径(离散)；几何/泛函是连续度量距离，定义域不同勿直接套公式',
    ],
cache_key="graph_theory",
)

_KG_NODES["probability"] = KGNode(
    domain_en="probability",
    domain_cn="概率论",
    methods=[
        "明确样本空间，古典概型计数 (C(n,k)/N)",
        "条件概率、全概率/贝叶斯公式",
        "期望/方差计算：线性期望、全期望公式",
        "随机变量分布识别（二项、泊松、正态、均匀）",
        "大数定律与中心极限定理近似",
    ],
    theorems=[
        "全概率公式：按互斥完备事件分解",
        "贝叶斯公式：后验 = 先验×似然 / 归一",
        "期望线性 E[aX+bY]=aEX+bEY（无需独立）",
        "方差 Var(X)=E[X²]-(EX)²",
    ],
    flow=[
        "1. 定义事件与随机变量，写清样本空间",
        "2. 独立/互斥判定，选条件/全概率/贝叶斯",
        "3. 期望用线性拆，方差用 E[X²]-μ²",
        "4. 分布和归一验证 Σp=1",
    ],
    pitfalls=[
        "依赖事件误当独立相乘概率",
        "样本空间不对称导致古典概型计数错",
        "期望对非线性函数直接套线性（E[f(X)]≠f(EX)）",
    ],
    examples=[
        "条件概率与贝叶斯：先写后验公式",
        "求期望：线性分解或用指示变量",
        "二项分布期望 np 方差 np(1-p)",
    ],
    related_domains=["combinatorics", "real_analysis"],
    disambiguation=[
        '分布 —— 概率指随机变量概率规律；实分析\'分布(广义函数)\'指 delta 等线性泛函；泛函里是完全不同的对象，勿混',
        '空间 —— 概率样本空间(事件集合)；拓扑/度量空间是带结构集合，含义独立，概率题内一般不涉及拓扑',
        '期望 —— 概率 E[X]；统计推断里是总体均值估计；运筹学常把期望当目标(期望利润)，视角不同',
        '独立 —— 概率指事件/变量独立；代数线性无关、数论互素都叫独立相关词，词的数学含义不等同',
    ],
cache_key="probability",
)

_KG_NODES["differential_equations"] = KGNode(
    domain_en="differential_equations",
    domain_cn="微分方程",
    methods=[
        "识别类型：可分离、齐次、一阶线性、伯努利、恰当方程",
        "一阶线性用积分因子；可分离直接积分",
        "二阶常系数线性：特征方程，含非齐次用待定系数/常数变易",
        "PDE 部分转阈值：先分清常微分/偏微分",
        "初值/边值定解，验证唯一性",
    ],
    theorems=[
        "一阶线性通解公式 y=e^{-∫P}(∫Q e^{∫P}dx+C)",
        "二阶常系数齐次：特征根实数/复数分三种",
        "常数变易法求解非齐次",
        "初值问题解存在唯一性（Lipschitz）",
    ],
    flow=[
        "1. 判定阶数、线性、齐次",
        "2. 一阶先用可分离/积分因子；二阶先用特征方程",
        "3. 非齐次补特解（待定系数/常数变易）",
        "4. 代入初/边值定常数，验根",
    ],
    pitfalls=[
        "二阶特征根重根时解形式 (Ax+B)e^rx 混淆",
        "积分因子没乘完全导致不可积",
        "初值代入的是通解而非特解",
    ],
    examples=[
        "一阶线性：积分因子",
        "二阶常系数齐次：特征根判别",
        "伯努利方程：换元化一阶线性",
    ],
    related_domains=["calculus", "partial_differential_equations", "numerical_analysis"],
    disambiguation=[
        '初值/边值 —— ODE 定解条件；PDE 称初边值问题；数值分析离散为初值递推，连续与离散对应需区分',
        '解 —— ODE 通/特解(函数)；数值分析\'数值解\'是近似序列；PDE 弱解在变分意义，\'解\'的层级不同',
        '方程 —— ODE 常微分；PDE 偏微分；代数方程、不定方程(数论)类型各异，先分清题目属于哪类',
        '阶(order) —— ODE 指导数最高阶；群论阶/数论模周期/多项式次数另说，按题型定',
    ],
cache_key="differential_equations",
)

_KG_NODES["partial_differential_equations"] = KGNode(
    domain_en="partial_differential_equations",
    domain_cn="偏微分方程",
    methods=[
        "分离变量法：u=X(x)T(t) 化为本征值问题",
        "特征线法：一阶双曲/传输沿特征线化 ODE",
        "Fourier/Laplace 变换：把 PDE 变代数或 ODE",
        "格林函数法：线性非齐次用点源叠加",
        "能量估计/弱解：存在唯一性与定性分析",
    ],
    theorems=[
        "线性 PDE：通解=齐次+特解，叠加原理",
        "三类方程：椭圆(Laplace)、抛物(热传导)、双曲(波动)",
        "调和函数最值原理；Sturm-Liouville 特征函数正交",
        "傅里叶级数/变换收敛定理",
    ],
    flow=[
        "1. 判定类型(椭圆/抛物/双曲)与定解条件(初值/边界)",
        "2. 首选分离变量：写本征值方程解特征函数",
        "3. 非齐次边界先齐次化；非齐次项用特征展开/Duhamel",
        "4. 用初值定叠加系数，回代验证",
    ],
    pitfalls=[
        "方程误分类（需先标准化再判型）",
        "非齐次边界未独立处理就套 Dirichlet 特征",
        "分离变量收敛：漏叠加系数，特 w 于正则性边界",
    ],
    examples=[
        "热传导方程：分离变量+正弦级数",
        "波动方程：特征线/达朗贝尔",
        "Laplace 圆域：极坐标分离变量",
    ],
    related_domains=["differential_equations", "real_analysis", "mathematical_physics", "numerical_analysis"],
    disambiguation=[
        '方程类型(椭圆/抛物/双曲) —— PDE 按二阶主部判型；微分几何曲率方程也引椭圆但偏定性，本图谱按 PDE 分类',
        '解/弱解 —— PDE 经典解 vs 弱解(变分/分布)；数学物理多带物理界带；泛函弱解依赖 Sobolev 空间，抽象度递进',
        '特征线 —— PDE 一阶双曲传播轨迹；线性代数特征向量对象是矩阵，用语相似但对象不同',
        '本征值 —— PDE(Sturm-Liouville)给出函数空间展开基；线性代数本征值是矩阵谱，数值分析也是矩阵，语境不同',
    ],
cache_key="partial_differential_equations",
)

_KG_NODES["topology"] = KGNode(
    domain_en="topology",
    domain_cn="拓扑学",
    methods=[
        "连续性/同胚判定：开集逆像、映射性质",
        "紧致/连通性：性质在连续映射下保持",
        "同伦与基本群：分类空间点/闭路径",
        "紧致空间乘积(Tychonoff)、度量空间可分性",
        "用定义构造反例证明不满足某性质",
    ],
    theorems=[
        "紧集的连续像紧；连通像连通",
        "Heine-Borel：R^n 紧 ⇔ 有界闭",
        "紧 Hausdorff 中的闭集紧、正则/正规性",
        "度量化定理、Tychonoff 乘积紧性",
    ],
    flow=[
        "1. 判断是概念判断(是/否)还是构造反例",
        "2. 明确用到的拓扑性质及其对映首要条件",
        "3. 判断题给反例；构造题给显式集合/图",
        "4. 检查是否满足定义成立条件",
    ],
    pitfalls=[
        "紧/闭混淆：R^n 中闭不一定紧（需有界）",
        "连通 vs 路径连通的强弱搞反",
        "映射性质方向其逆命题误以为成立",
    ],
    examples=[
        "判断子空间紧性：Heine-Borel 直接查有界闭",
        "验证映射连续：查开集逆像开",
        "判断连通：找不到非平凡既开且闭子集",
    ],
    related_domains=["real_analysis", "functional_analysis", "abstract_algebra"],
    disambiguation=[
        '空间 —— 拓扑\'拓扑空间/度量空间\'即研究对象；几何里是日常空间；泛函是高阶函数集合，抽象层级最高',
        '度量(metric) —— 拓扑度量满足公理泛化；几何距离是日常度量；本质相同但拓扑更强调公理与诱导性质与分离性，勿当普通几何量',
        '开/闭 —— 拓扑由开集公理定义集合族；实分析/几何开闭与区间端点绑定，欧氏情形可用直觉但证明依拓扑定义',
        '连通/紧 —— 拓扑连续不变性质；几何连通直观、实分析里区间连通，拓扑中证明方式(反例/定义)不同',
    ],
cache_key="topology",
)

_KG_NODES["real_analysis"] = KGNode(
    domain_en="real_analysis",
    domain_cn="实分析",
    methods=[
        "ε-δ 论证：极限、连续、一致连续",
        "测度与 Lebesgue 积分：可测性判定",
        "逐点/一致收敛区分；控制收敛/单调收敛换极限",
        "可微性、导数性质、中值定理",
        "完备性：Cauchy 列、Baire 范畴",
    ],
    theorems=[
        "一致收敛 ⟹ 极限可交换(积分/导数)",
        "单调收敛/控制收敛定理（Lebesgue）",
        "Arzelà-Ascoli；Bolzano-Weierstrass",
        "Riemann vs Lebesgue 可积条件",
    ],
    flow=[
        "1. 判断题(是/否)还是证明题，先明确定义",
        "2. 一致性问题优先给反例（函数列指数/锯齿）",
        "3. 换极限前先验一致收敛/控制收敛条件",
        "4. 定义直接验证或反证",
    ],
    pitfalls=[
        "把逐点收敛当一致收敛换极限",
        "控制收敛缺被控制函数导致交换失败",
        "测度为零集上的超控误以为可忽略的作用",
    ],
    examples=[
        "证明一致收敛：求 sup|f_n-f|→0",
        "判定可积：不连续点集测度",
        "换极限：用 DCT 找 g 被控",
    ],
    related_domains=["calculus", "functional_analysis", "topology"],
    disambiguation=[
        '收敛 —— 实分析区分逐点 vs 一致收敛(换序关键)；微积分只默认收敛；拓扑/泛函由网、范数定义更抽象，是收敛概念层级递进',
        '可测/测度 —— 实分析 Lebesgue 测度与可测函数；概率测度是归一化的概率特例；数学物理一般不用，勿跨域',
        '序列/函数列 —— 实分析函数序列求极限/一致逼近；数值分析迭代序列是数值逼近；概率序列强调收敛模式，语义不同',
        '几乎处处(a.e.) —— 实分析测度意义几乎处处；概率里\'几乎必然(a.s.)\'是概率1事件，测度与概率术语对应但对象不同',
    ],
cache_key="real_analysis",
)

_KG_NODES["functional_analysis"] = KGNode(
    domain_en="functional_analysis",
    domain_cn="泛函分析",
    methods=[
        "范数/内积空间性质：三角不等式、Cauchy-Schwarz",
        "Banach/Hilbert 空间系列定理（Banach-Steinhaus、开映射）",
        "算子有界性与范数计算 sup||Tx||/||x||",
        "对偶空间与 Riesz 表示",
        "紧算子/谱定理；变分与映射观点",
    ],
    theorems=[
        "Hahn-Banach，开映射定理，闭图定理",
        "Banach-Steinhaus：点态有界⟹一致有界",
        "Riesz 表示：Hilbert 连续线性泛函由内积给出",
        "Cauchy-Schwarz |<x,y>|≤||x||||y||",
    ],
    flow=[
        "1. 判定空间类型(Banach/Hilbert/内积)与完整性",
        "2. 有界算子先验证线性+||T||<∞",
        "3. 用定理：完备性/对偶/谱",
        "4. 构型反例验证必要条件",
    ],
    pitfalls=[
        "内积空间误用竖范数||·||2 性质到无穷范数",
        "完整性未证实就套闭图/开映射等定理",
        "对偶元混淆函数/泛函方向",
    ],
    examples=[
        "求算子范数：先证||Tx||≤M||x||再找 x 取等",
        "证连续线性泛函：用 Riesz 表示或序列连续性",
        "用闭图定理证明算子有界",
    ],
    related_domains=["real_analysis", "topology", "linear_algebra"],
    disambiguation=[
        '空间 —— 泛函内积/Hilbert/Banach 空间是函数或序列集合；拓扑空间是几何直觉抽象；几何空间是几何对象，抽象层级最高',
        '范数 —— 泛函权衡长度的公理化函数；数值分析指向量/矩阵范数(2-范数等)；线性代数范数更具体，泛函最一般',
        '算子 —— 泛函指线性映射(关注有界/完备)；微积分/ODE 里\'算子\'如求导/微分算子也指映射，泛函更重有界性与谱',
        '线性泛函/对偶 —— 泛函无穷维需先证连续有界；线性代数有限维线性函数更初等，表示定理是泛函核心',
    ],
cache_key="functional_analysis",
)

_KG_NODES["abstract_algebra"] = KGNode(
    domain_en="abstract_algebra",
    domain_cn="抽象代数",
    methods=[
        "群/环/域结构识别：阶、子群、同态、正规子群",
        "Sylow 定理判定子群存在与共轭",
        "同构定理第一/二/三，商结构",
        "理想/商环、主理想整环、域扩张次数",
        "Galois 理论：多项式分裂域与自同构群对应",
    ],
    theorems=[
        "Lagrange：|H| 整除 |G|",
        "Sylow 定理：存在 p-Sylow，个数 ≡1 mod p 且整除 |G|；用降次数证明非单群",
        "同构定理：G/K ≅ im",
        "Galois 基本定理：中间域与子群 1-1 对应",
        "Cayley 定理（群作用/同态嵌入置换群）、中心化子的阶公式",
    ],
    flow=[
        "1. 先确定代数结构(群/环/域)与阶/元个数",
        "2. 问子群用 Lagrange/Sylow；问同态用正规核",
        "3. 域扩张算次数 [F:K] 与是否可分/正规",
        "4. 判断题给反例或证充分性",
        "5. 判非单用 Sylow 计数：数 p-Sylow 个数 n_p 与 |G| 整除性产生异于平凡正规子群",
    ],
    pitfalls=[
        "Sylow 个数条件 n_p≡1 mod p 的完整判定漏写",
        "商群合法性需正规子群前提",
        "可区分 domain 扩张 vs 自同构群大小",
        "把群作用当每点都自由：核对固定点集（Stabilizer）",
    ],
    examples=[
        "判断群是否循环/Abel：查生成元",
        "用 Sylow 定理找 p-子群",
        "计算域扩张次数与 Galois 群",
    ],
    related_domains=["linear_algebra", "number_theory", "topology"],
    disambiguation=[
        '域(field) —— 抽象代数指四则封闭的域；几何/复分析\'域\'是连通开区域；数论有限域是数的结构，按代数含义读',
        '阶/群 —— 抽象代数群元素的阶与群阶；数论乘法阶(模周期)是特例；微分方程\'阶\'是导数阶，多义词按结构定',
        '运算 —— 代数系统上的二元运算(封封闭结合)；日常/编程\'运算\'是计算动作，勿当代数结构理解',
        '理想/环 —— 抽象代数环的理想(同态核)；几乎仅在代数语境出现，见到 PID、商环、理想判为抽象代数而非泛泛代数',
    ],
cache_key="abstract_algebra",
)

_KG_NODES["operations_research"] = KGNode(
    domain_en="operations_research",
    domain_cn="运筹学",
    methods=[
        "线性规划：建模目标+约束，顶点法与单纯形",
        "整数/动态规划：状态转移与递推最优",
        "最短路/网络流/指派：Ford-Fulkerson、匈牙利、Dijkstra",
        "排列/调度/装箱启发式：贪心、最近邻等",
        "对偶与敏感性：影子价格",
    ],
    theorems=[
        "LP 最优解在可行域顶点",
        "对偶定理强/弱对偶：max≤min 与互补松弛",
        "最大流=最小割 (Max-flow Min-cut)",
        "匈牙利定理：指派问题的组合最优",
    ],
    flow=[
        "1. 写清楚决策变量、目标、全部约束条件",
        "2. 线性规划数顶点；图问题选对应算法",
        "3. 整数/调度序列用 DP/贪心+验证可行",
        "4. 最优解代入每个约束核验可行性",
    ],
    pitfalls=[
        "约束漏写或重复导致可行域错",
        "LP 忽略非负约束/整数约束",
        "贪心不保证全局最优却在正证题当最优先用",
    ],
    examples=[
        "线性规划最大利润：画可行域数顶点",
        "指派问题：匈牙利法",
        "最大流：lloyd-Fulkerson + 割验证",
    ],
    related_domains=["graph_theory", "linear_algebra", "combinatorics"],
    disambiguation=[
        '优化/规划 —— 运筹学求目标最优(规划)；数学分析\'极值\'是函数局部求导问题；组合数学常计数/枚举，目标不同',
        '约束 —— 运筹指可行域上的限制(不等式/等式)；物理/工程约束是定律或资源；概率无直接约束概念，洞察题目本体',
        '指派/分配 —— 运筹指派问题是组合优化；经济学分配是资源配比；组合数学分配指计数各类划分，按领域定',
        '网络/流 —— 运筹网络流/最大流算法明确；图论网络分析共享模型但侧重可达结构；物理\'流\'是连续量，区分离散/连续',
    ],
cache_key="operations_research",
)

_KG_NODES["numerical_analysis"] = KGNode(
    domain_en="numerical_analysis",
    domain_cn="数值分析",
    methods=[
        "插值/逼近：Lagrange、Newton、最小二乘",
        "数值积分：梯形、Simpson 与误差阶",
        "数值微分：前/后/中心差分与截断误差",
        "方程求根：二分、Newton 迭代、收敛阶",
        "ODE/特征值数值法：Euler、Runge-Kutta、幂迭代",
    ],
    theorems=[
        "插值误差余项含 (n+1) 阶导数与乘积项",
        "区间二分误差 ≤ (b-a)/2^n；Newton 二次收敛",
        "中心差分误差 O(h²)，前差 O(h)",
        "幂迭代收敛到最大模特征值",
    ],
    flow=[
        "1. 明确数值任务与给定数据(节点/步长)",
        "2. 选方法并写出公式，代步长/节点",
        "3. 估算误差阶，必要时细化步长比较",
        "4. 数值结果与解析解或真值比对数量级",
    ],
    pitfalls=[
        "差分步长过大导致截断/计算误差掩盖",
        "Simpson/梯形阶数用错被积函数光滑性不足",
        "迭代不发散条件（导数/谱半径）未查",
    ],
    examples=[
        "用中心差分算导数：h=0.1 代公式",
        "Simpson 数值积分：偶数区间",
        "Newton 求根：给定初值迭代",
    ],
    related_domains=["calculus", "differential_equations", "linear_algebra"],
    disambiguation=[
        '误差 —— 数值分析指截断/舍入误差(量化逼近质量)；统计误差是随机/测量误差；数学证明中误差是分析用词，语境不同',
        '迭代 —— 数值分析逼近根的迭代步骤；数学序列论迭代是函数复合递推，目标不同(求根 vs 不动点/极限)',
        '插值/逼近 —— 数值分析用离散数据近似函数；泛函逼近论更理论(完备/稠密)，是非理边界清晰',
        '矩阵数值 —— 数值分析解方程组/特征值用数值算法(迭代/分解)；线性代数是精确代数理论，注意数值误差累积',
    ],
cache_key="numerical_analysis",
)

_KG_NODES["mathematical_physics"] = KGNode(
    domain_en="mathematical_physics",
    domain_cn="数学物理方法",
    methods=[
        "偏微分方程定解：分离变量、积分变换、Green 函数",
        "特殊函数：Legendre/Laguerre/Bessel 的级数与本征值",
        "Fourier 级数/变换与 Laplace 变换",
        "变分原理：极值/约束极值、能量泛函",
        "量纲分析与相似解/渐近",
    ],
    theorems=[
        "Sturm-Liouville 本征值问题：正交完备",
        "Fourier 级数收敛（Dirichlet 条件）",
        "Laplace 变换卷积定理",
        "变分欧拉-Lagrange 方程",
    ],
    flow=[
        "1. 识别物理场景(热/波/势)对应方程",
        "2. 按边界定解条件选方法",
        "3. 分离变量或变换后求解本征值",
        "4. 叠加定系数，物理量纲与初始核验",
    ],
    pitfalls=[
        "物理量纲错导致结果数量级错误",
        "边界条件奇异性处理漏掉正则性要求",
        "特殊函数指标/系数抄错",
    ],
    examples=[
        "Bessel 方程本征值：圆域热/波",
        "Laplace 变换解 ODE 初值",
        "变分求极值曲线：欧拉方程",
    ],
    related_domains=["partial_differential_equations", "differential_equations", "complex_analysis"],
    disambiguation=[
        '变换 —— 数学物理 Fourier/Laplace 变换是积分算子；线性代数变换是线性映射；复变共形映射保角，域不同',
        '特殊函数 —— 数学物理专指 Legendre/Bessel/超几何等；泛函函数是任意对象；数值分析是离散数据，无需混用',
        '本征值问题 —— 数学物理 Sturm-Liouville 本征展开函数；线性代数/数值特征值对象是矩阵，产生的基不同(函数 vs 向量)',
        '变分 —— 数学物理变分(欧拉-拉格朗日)求泛函极值函数；运筹优化求决策变量最优，数学结构不同',
    ],
cache_key="mathematical_physics",
)

# ===================== 组装与检索 =====================

def _assemble(node: KGNode, max_len: int) -> str:
    """把节点组装为中文方法论提示文本。"""
    lines = [f"\n\n【题型知识图谱：{node.domain_cn}（{node.domain_en}）】"]
    lines.append("## 核心方法")
    lines += [f"- {m}" for m in node.methods]
    lines.append("## 常用定理")
    lines += [f"- {t}" for t in node.theorems]
    if node.flow:
        lines.append("## 标准求解流程")
        lines += [f"{i}. {s}" for i, s in enumerate(node.flow, 1)]
    if node.pitfalls:
        lines.append("## 常见陷阱")
        lines += [f"- {p}" for p in node.pitfalls]
    if node.examples:
        lines.append("## 典型范式")
        lines += [f"- {e}" for e in node.examples]
    if node.related_domains:
        rel_names = [_KG_NODES[d].domain_cn for d in node.related_domains if d in _KG_NODES]
        if rel_names:
            lines.append("## 关联题型")
            lines.append("- " + "、".join(rel_names))
    if node.disambiguation:
        lines.append("## 概念消歧")
        lines += [f"- {m}" for m in node.disambiguation]
    if node.examples_cache:
        lines.append("## 扩展题解参考(缓存)")
        for item in node.examples_cache[:2]:
            m = (item.get('method') or '').strip()
            t = (item.get('title') or '').strip()
            if m:
                lines.append(f"- {t}：{m}")
            else:
                # method 为空：用题解正文开头作方法摘要（知识合并兜底）
                sol = (item.get('solution') or '').replace("\n", " ").strip()
                digest = re.sub(r'\s+', ' ', sol)[:130] if sol else "（无题解正文）"
                head = f"{t}：" if t else ""
                lines.append(f"- {head}{digest}…")
    text = "\n".join(lines)
    if len(text) > max_len:
        text = text[:max_len] + "\n…(已截断)"
    return text


_KG_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kg_cache")


def _merge_extension(node: KGNode) -> None:
    """把 kg_cache/{cache_key}.json 的扩展题解并入 node.examples_cache；无文件/坏文件静默跳过。"""
    if node.examples_cache or not node.cache_key:
        return
    try:
        fp = os.path.join(_KG_CACHE_DIR, f"{node.cache_key}.json")
        if not os.path.exists(fp):
            return
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items", [])
        node.examples_cache = items[:5]
    except Exception:  # noqa: BLE001
        node.examples_cache = []


def retrieve_kg(domain: str, problem: str = "", use_extension: bool = True, max_len: int = 1400) -> str:
    """按题型取知识图谱节点，组装为中文方法论提示文本。

    - 按 domain_en 精确取节点组装提示；
    - （扩展钩子）problem 子关键词精化：当前 _refine 为 no-op 直通，不进入二级检索；
    - 兜底：domain 为 other / 空 / 节点缺失 → 返回 ""，绝不抛异常。
    """
    try:
        if not domain:
            return ""
        node = _KG_NODES.get(domain)
        if node is None:
            return ""
        if use_extension:
            _merge_extension(node)
        return _assemble(node, max_len=max_len)
    except Exception:  # noqa: BLE001
        return ""


def get_kg_node(domain: str) -> Optional[KGNode]:
    return _KG_NODES.get(domain)


def all_kg_domains() -> set:
    return set(_KG_NODES.keys())


def kg_stats() -> dict:
    return {
        "n_nodes": len(_KG_NODES),
        "n_with_cache": sum(1 for n in _KG_NODES.values() if n.cache_key),
        "domains": sorted(_KG_NODES.keys()),
    }


# P2 扩展钩子：根据题目子关键词返回附加提示；当前保留接口、返回空。
def _refine(problem: str) -> list:
    return []


if __name__ == "__main__":
    import sys
    print("节点数:", kg_stats()["n_nodes"])
    for d in sorted(_KG_NODES):
        t = retrieve_kg(d, max_len=400)
        print("-", d, "len=", len(t))
    print("兜底 other:", repr(retrieve_kg("other")))