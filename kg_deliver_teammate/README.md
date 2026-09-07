# knowledge_graph.py — 数学题型知识图谱（独立、可迁移）

一个**纯本地、零依赖、可独立复制迁移**的数学模型知识图谱模块。
它按「题型」组织 18 个竞赛数学子领域的解题方法论（核心方法 / 常用定理 / 标准求解流程 / 常见陷阱 / 典型范式 / 关联题型），供任意数学解题系统在「题型识别」之后检索该题型的方法论，作为提示词注入推理。

> 设计目标：**解耦**。本文件只依赖 Python 标准库（`dataclasses`、`os`、`json`），不 import 任何业务代码、不联网、不调用任何 API。把文件复制到你的项目里即可用。

---

## 1. 这个文件解决什么问题

很多数学解题系统（LLM 智能体、RAG 检索器、自动解题工具）在拿到题目后，通常只做一层很粗的分类或只给一句话的领域提示。
这个图谱把「每个题型该用什么方法、什么定理、按什么流程、避免什么坑」结构化沉淀下来，让系统在**识别出题型后**直接取出这一段方法论，注入提示词，引导模型用正确方法解题。

典型使用链路：

```
题目文本
  └─(你的题型识别器)→ domain(题型 key)
        └─ retrieve_kg(domain) → 一段中文方法论提示文本
              └─ 拼进你的 prompt / 检索上下文
```

---

## 2. 迁移 / 集成

### 2.1 三步迁移

1. 复制 `knowledge_graph.py` 到你的项目（可放任意目录，**无相对路径依赖**；它内部只用 `os.path.dirname(__file__)` 定位可选的扩展缓存目录）。
2. `import` 它（直接 import 或丢到 sys.path）。
3. 调用 `retrieve_kg(domain)` 拿方法论文本。

### 2.2 零依赖确认

- 只用到标准库：`dataclasses`、`typing`、`os`、`json`。
- 不需要网络、不需要向量库、不需要 API key、不需要 numpy/sympy 等。
- 不需要在 `requirements.txt` 加任何东西。

### 2.3 最小可用示例

```python
from knowledge_graph import retrieve_kg, get_kg_node, all_kg_domains, kg_stats

# ① 看有哪些题型（18 个）
print(all_kg_domains())

# ② 直接取某题型的方法论提示（字符串，可直接拼进 prompt）
pde_prompt = retrieve_kg("partial_differential_equations")
# → "\n\n【题型知识图谱：偏微分方程（partial_differential_equations）】\n## 核心方法\n- 分离变量法：…"

# ③ 短路兜底：识别不到 / 不在表内 → 返回空串，绝不抛异常
print(retrieve_kg("other"))        # ""
print(retrieve_kg("not_a_domain")) # ""

# ④ 如果要做你自己的检索逻辑，可取结构化节点对象
node = get_kg_node("number_theory")
print(node.methods)   # 核心方法列表
print(node.theorems)  # 常用定理列表
print(node.flow)      # 标准求解流程（分步）
```

---

## 3. API 接口文档

### 3.1 `retrieve_kg(domain: str, problem: str = "", use_extension: bool = True, max_len: int = 1400) -> str`

**主入口**：按题型 key 取节点，组装为一段中文方法论提示文本（可直接当提示词注入）。

- `domain`：题型 key（见下方"题型 key 对照表"）。传 `other` / 空串 / 不存在 / 节点缺失 → 返回 `""`。
- `problem`：题目文本。**当前未用于二级检索**（保留为扩展钩子），传空或不传均可。
- `use_extension`：是否尝试加载 `kg_cache/<cache_key>.json` 扩展题解缓存。默认 `True`；无缓存文件时静默跳过。
- `max_len`：组装后文本最大长度（字符），超长会截断并追加"…(已截断)"。默认 `1400`，避免注入提示过长。

### 3.2 `get_kg_node(domain: str) -> Optional[KGNode]`

返回结构化节点对象（`KGNode` dataclass），供你自己写检索/组装逻辑。节点不存在返回 `None`。

### 3.3 `all_kg_domains() -> set[str]`

返回全部 18 个题型 key 集合。

### 3.4 `kg_stats() -> dict`

返回统计：`{n_nodes, n_with_cache, domains}`，可用于健康检查 / 测试。

### 3.5 内部辅助

- `_merge_extension(node)`：把 `kg_cache/<cache_key>.json` 的扩展题解并入节点；无文件 / 坏文件静默跳过。
- `_refine(problem) -> list`：扩展钩子（当前返回空列表，预留给未来"按题目子关键词精化到具体方法"的二级检索）。

---

## 4. 数据结构（KGNode schema）

`KGNode` 是一个 `dataclass`，字段如下：

| 字段 | 类型 | 含义 |
|------|------|------|
| `domain_en` | str | 题型 key（检索键，见下表） |
| `domain_cn` | str | 题型中文名 |
| `methods` | list[str] | 核心方法（短句） |
| `theorems` | list[str] | 常用定理 / 关键结论 |
| `flow` | list[str] | 标准求解流程（编号分步，可直接当执行蓝图） |
| `pitfalls` | list[str] | 常见陷阱：现象→原因→对策 |
| `examples` | list[str] | 典型范式：题目原型 + 适用条件 + 首推方法 |
| `related_domains` | list[str] | 关联题型（其它 `domain_en`），用于跨域迁移提示 |
| `disambiguation` | list[str] | **实体消歧**：跨题型共享概念（如"积分/空间/阶/域"）在本题型语境下的含义区分，检索时以「概念消歧」小节注入，防模型把 A 题型术语当作 B 题型理解 |
| `cache_key` | str | 扩展缓存文件名关键词；`""` 表示无扩展缓存 |
| `examples_cache` | list[dict] | 扩展题解缓存条目（`_merge_extension` 填充） |

---

## 4.1 实体消歧与对齐（基于知识图谱构建方法论）

按知识图谱构建的"信息抽取 → 知识融合（实体链接/消歧/对齐/合并）→ 知识加工（本体/质量评估）"三层流程，本图谱已做两类优化：

- **实体消歧**：18 个题型节点各配置 3~5 条 `disambiguation`。针对跨题型同名不同义的共享概念（如 `积分`在微积分是求面积、在数学物理是积分变换算子；`空间`在几何是几何空间、在拓扑是拓扑空间、在泛函是函数空间），明确给出本题型语境下的含义与边界。检索时注入为「## 概念消歧」小节。
- **实体对齐 / 悬空引用修复**：修正了 `geometry` 引用不存在的 `trigonometry_analog` 域、`operations_research` 拼写 `lloyd`→`Ford-Fulkerson`、`mathematical_physics` 的 `LeGendre`→`Legendre` 等术语对齐问题。
- **知识合并兜底**：扩展缓存条目 `method` 为空时，注入改为取题解正文开头作方法摘要显示，避免输出空方法标签。

配套工具（开发目录 `dev_backup/`）：
- `kg_disambiguate.py` / `kg_write_disambig.py`：注入/重写节点消歧
- `kg_check_misclass.py`：质量评估——检测缓存里跨题型疑似错配条目，产出报告供人工复核（默认不改数据，`--apply` 才落盘）

## 5. 题型 key 对照表（18 个）

| domain_en（检索用） | domain_cn（中文） |
|---|---|
| `algebra` | 代数 |
| `linear_algebra` | 线性代数 |
| `calculus` | 微积分 |
| `complex_analysis` | 复分析 |
| `geometry` | 几何 |
| `number_theory` | 数论 |
| `combinatorics` | 组合数学 |
| `graph_theory` | 图论 |
| `probability` | 概率论 |
| `differential_equations` | 微分方程 |
| `partial_differential_equations` | 偏微分方程 |
| `topology` | 拓扑学 |
| `real_analysis` | 实分析 |
| `functional_analysis` | 泛函分析 |
| `abstract_algebra` | 抽象代数 |
| `operations_research` | 运筹学 |
| `numerical_analysis` | 数值分析 |
| `mathematical_physics` | 数学物理方法 |

---

## 6. 扩展机制：真实题解缓存（可选）

图谱的静态方法论节点是"骨架"。你可以用**真实题解**给每个题型补"血肉"，形成更充分的解题参考。

### 6.1 缓存格式与加载

1. 在 `knowledge_graph.py` 同目录建 `kg_cache/` 文件夹（本模块会自动定位该目录）。
2. 每个题型放一个 JSON 文件，命名 `kg_cache/<cache_key>.json`，结构为：

```json
{
  "domain_en": "partial_differential_equations",
  "cache_key": "partial_differential_equations",
  "updated_at": "2026-09-05",
  "items": [
    {"title": "题目原型", "url": "https://...", "source": "github",
     "method": "分离变量法", "solution": "题解正文…"}
  ]
}
```

3. 调用 `retrieve_kg(domain)` 时（默认 `use_extension=True`），会把 `items` 并入节点，在提示文本末尾追加「扩展题解参考(缓存)」区块（实际加载前 5 条，展示前 2 条）。
4. **无缓存 / 文件损坏时静默跳过**，不影响主流程；`items` 为空数组也合法（视为无扩展）。

> 注意：扩展缓存建议放在你的项目本地（例如 `.gitignore` 忽略 `kg_cache/`），避免把大数据提交进仓库。

### 6.2 用爬虫工具自动生成缓存（推荐）

项目自带一个开发工具 `dev_backup/kg_scraper.py`（纯脚本、不入提交仓库），可从 GitHub raw 抓取真实题解并自动生成 `kg_cache/*.json`，格式与上述完全一致。

```bash
# 抓全部 18 个题型（每个最多 5 条；已有缓存自动跳过）
python kg_scraper.py --all
# 只抓单个题型
python kg_scraper.py --domain algebra --limit 5
# 强制重抓（覆盖已有缓存）
python kg_scraper.py --all --force --limit 10
```

爬虫特性：
- **数据源可扩展**：`SOURCE_SUGGESTIONS`（分领域直连表）+ `GENERIC_SOURCES`（通用源，可限定可用题型域）都是易扩展的种子表。你有可访问的竞赛题解 URL 时，往表里加一行即可，爬虫逻辑不用改。
- **自动探测**：GitHub raw 自动尝试 `main` / `master` 分支；遇到 Cloudflare 拦截会自动尝试 `curl_cffi`（若安装）。
- **幂等与容错**：已有缓存默认跳过（`--force` 重抓）；某个题型抓取失败或没有可用源时写空缓存（`items: []`），加载端静默跳过，绝不中断。
- **质量诚实约定**：不要用不匹配的源硬填题型，避免给模型注入"标签错配"的假题解。GSM8K（小学应用题）只适合运筹类；本套图谱的高数题型（PDE/拓扑/泛函/抽象代数等）用专门的大学数学题解数据集（见 6.4）填充。

### 6.3 手写缓存（无需爬虫）

不联网也可手写：按 6.1 的 JSON 结构把某题型的几条你觉得有价值的题解放进去即可，`retrieve_kg` 同样会加载。

### 6.4 已集成的真实解题数据源

下图谱已在目标系统 `Challenge-Cup-2026-math-agent/kg_cache/` 配齐 18 个题型的真实解题过程（每条含题干 + 完整解答），当前共 **32757 条**：13 个富类各 2000 条，abstract_algebra 2047 / functional_analysis 2001，math_physics 1732（MATH+StackMathQA），operations_research 1777（MATH 补 886 条），real_analysis 1312，PDE 1200，topology 690。全部来自下述公开可下载的 GitHub 数据集（raw 直连即可获取）：

| 数据源 | 原始仓库 | 覆盖题型 | 说明 |
|---|---|---|---|
| **StackMathQA**（主源） | `github.com/yifanzhang-pro/StackMathQA` | **全部 18 类**（高数题型主力） | math.stackexchange 真实问答 100k，`{Q, A, meta}`；已抓 **128 分片全量**（~10 万条）按题型过滤 |
| **MATH 数据集**（NolanTrem/MATH-Scraper 镜像） | `github.com/NolanTrem/MATH-Scraper` | algebra、linear_algebra、calculus、complex_analysis、geometry、number_theory、combinatorics、graph_theory、probability、operations_research、mathematical_physics | 12507 题（train+test），每题 `{problem, level, type, solution}`，覆盖 7 个 MATH 学科 |
| **ProofNet**（大学数学证明） | `github.com/zhangir-azerbayev/ProofNet` | topology、real_analysis、functional_analysis、abstract_algebra、numerical_analysis | 大学数学证明题，`nl_proof` 为完整证明过程 |
| **Mamo ODE** | `github.com/FreedomIntelligence/Mamo` | differential_equations | ODE 题（`Question`/`Answer`/`Category`） |
| **pde-agent-bench** | `github.com/YusanX/pde-agent-bench` | partial_differential_equations | 241 条 PDE 基准，覆盖 poisson/heat/navier-stokes/helmholtz/stokes/biharmonic/reaction-diffusion/convection-diffusion/linear-elasticity，含方程类型与求解配置 |
| **Science-Star HLE**（人类最后考试） | `github.com/ustc-ai4science/Science-Star` | partial_differential_equations | HLE Physics 分类中含 PDE 关键词的高质题（`question`+`rationale`+`answer`） |
| **odyssey-math** | `github.com/protagolabs/odyssey-math` | algebra、calculus、geometry、probability、graph_theory、abstract_algebra、topology、real_analysis 等 | GPT 高级数学题解，每道含 `question`+`reasoning` |
| **GSM8K**（openai/grade-school-math） | `github.com/openai/grade-school-math` | operations_research | 应用/优化题，`<<...>>` 分步解答 |

> 说明：`HuggingFace`/`AoPS` 等站点在该网络环境下常被墙，MATH 的完整数据集更稳妥的方式是走上述 GitHub 镜像（raw 直连）。

**配套拉取脚本**（放项目开发目录 `dev_backup/`，非提交仓库）：
- `kg_fetch_stackqa.py`：抓 StackMathQA → 按题型过滤填充（`--shards` 抓取分片数、`--per-domain` 每类上限）
- `kg_fetch_math.py`：拉 MATH 数据集 → 按学科映射填充
- `kg_fetch_advanced.py`：拉 ProofNet / Mamo ODE / pde-bench 填高数题型
- `kg_deep_pde.py`：深挖 PDE（pde-agent-bench 全量 + HLE 过滤）
- `kg_augment_odyssey.py`：用 odyssey-math 按题型追加扩充实测
- `kg_fill_missing.py`：一键检测 + 网络恢复后自动补全缺失题型
- `kg_scraper.py`：通用爬虫（SOURCE_SUGGESTIONS / GENERIC_SOURCES 扩展）
- `kg_expand_scarce.py`：稳扫 StackMathQA **全量 128 分片**（网络不稳时逐分片重试/续跑），用 18 类关键词按题型扩充各类真实题解（保留已有，去重追加，`--per-domain` 设上限）

> 这些脚本只在本地生成 `kg_cache/*.json`，图谱运行时 `retrieve_kg` 直接读缓存，不依赖脚本与网络。

---

## 7. 与解题系统的常见集成写法

```python
def inject_kg_into_prompt(problem, recognized_domain):
    # recognized_domain 来自你的题型识别器（与上表 key 对齐）
    kg_text = retrieve_kg(recognized_domain)
    if not kg_text:
        return problem, ""          # 识别不到就原样返回，交给兜底领域提示
    prompt = problem + kg_text      # 把方法论并进提示
    return prompt, kg_text
```

---

## 7.1 数学定理知识图谱（theorem_kg.py，独立模块）

除「题型」图谱外，本交付包还附带一个 **数学定理知识图谱** `theorem_kg.py`，用来统一种类繁多的数学定理（约 154 个实体 + 14 个同名异义根）。与题型图谱互补：

- **`knowledge_graph.py`**：按题型给方法论（18 类，解题用哪类方法）
- **`theorem_kg.py`**：按定理名/题目给单条定理知识（表述/前置条件/结论/证明思路）

同样**纯标准库、零依赖、拷文件即用**。运行时只需要同目录下的 `theorem_kg.py` + `theorem_data.py` 两个文件。

### 7.1.1 快速使用

```python
from theorem_kg import theorem_hint, search_theorems, theorem_stats

# ① 统计
st = theorem_stats()   # {'n_theorems':154, 'n_ambig_groups':14, 'by_category':..., 'by_domain':...}

# ② 按题目检索相关定理（自动做同名异义消歧）
k, text = search_theorems(problem, domain="complex_analysis")
# → (命中实体数, 中文提示文本)；直接拼进 prompt 即可

# ③ 也可显式给关键词 + 题目
k, text = theorem_hint("留数定理", problem=problem, domain="complex_analysis")

# ④ 兜底：无命中 / 异常返回 (0, "")
print(theorem_hint(""))
```

### 7.1.2 同名异义消歧（核心特性）

数学定理同名异义严重（如「Cauchy」可分 4 个不同定理）。`theorem_kg` 在 `theorem_data.py` 的 `DISAMBIG_MAP` 里为 14 个同名根（Cauchy/Cayley/Euler/Lagrange/Fourier/Sturm/Heine/Rolle/Green/Darboux/Clairaut/Gram/Sylvester/Haar）建模，按**题型域 + 触发词**评分选出正确实体，命中多候选时输出各候选及其「同名区分」说明。

示例：
- `theorem_hint("柯西不等式", domain="linear_algebra")` → 命中 **柯西-施瓦茨不等式**（内积），不含积分定理
- `theorem_hint("柯西积分定理", domain="complex_analysis")` → 命中 **柯西积分定理**，不含不等式

### 7.1.3 知识推理层（知识加工·推理）

按综述"知识加工"中的**知识推理**环节，`theorem_kg` 基于每个实体的 `related_theorems` 建立关联图，命中某定理时自动 BFS 推出它的**直接关联**与**可间接推导**的定理，作为推理提示注入。用于引导模型由已知定理推理到隐含的关联定理。

```python
from theorem_kg import infer_chain, theorem_hint

# ① 显式推理链：从某定理出发挖关联
for tid, hop in infer_chain("cauchy-integral-theorem", depth=2):
    print(hop, tid)

# ② 检索时自动附带知识推理（theorem_hint 返回文本里含「知识推理：…」行）
k, text = theorem_hint(problem="计算围道积分", domain="complex_analysis")
# → 输出末尾追加如：知识推理：留数定理 ↔ 直接关联：柯西积分定理、柯西积分公式、Laurent 级数
```

例如 `cauchy-integral-theorem` 可推理到 `cauchy-integral-formula`、`residue-theorem`（直接关联），再到 `liouville-theorem`、`laurent-series`（间接推导）。

### 7.1.4 数据结构

`TheoremNode` dataclass 字段：`tid / theorem_en / theorem_cn / aliases / domains / category / statement / preconditions / conclusion / proof_idea / related_theorems / disambiguation / keywords / source_domain`。数据层在 `theorem_data.py`（`THEOREM_DATA` + `DISAMBIG_MAP`），可直接增删实体。

### 7.1.5 接入解题系统

与题型图谱一样，在求解前调用并把返回文本并进 prompt：

```python
def inject_theorem(problem, recognized_domain):
    k, text = search_theorems(problem, domain=recognized_domain)
    return text or ""    # 空则不加，交由题型图谱/其他参考
```

配套脚本：
- `scripts/theorem_extract.py`：从 `knowledge_graph.py` 抽取 77 条原始定理（信息抽取溯源）
- `scripts/theorem_annotations.json`：人工标注/本体化说明（知识融合层）

---

## 8. 常见问题

**Q1. `retrieve_kg` 会不会抛异常 / 拖慢？**
不会。纯内存字典组装、O(1) 查找；任何异常都被捕获并返回 `""`。扩展缓存 `_merge_extension` 读失败也会静默跳过。

**Q2. 我识别出的题型 key 和这张表对不上怎么办？**
`retrieve_kg` 对不存在的 key 返回空串，你的系统只需做好兜底（回到原来的领域提示）。也可以自行把 `all_kg_domains()` 映射到你的题型命名。

**Q3. 我想改方法内容 / 加题型？**
直接在 `_KG_NODES` 里改 / 加 `KGNode` 即可。`python knowledge_graph.py` 可打印每个节点的检索长度做自检。

**Q4. 会和其它文件冲突吗？**
完全独立。唯一副作用是"可选缓存目录"定位；不 import 任何业务代码，可放进任意容器 / 环境。