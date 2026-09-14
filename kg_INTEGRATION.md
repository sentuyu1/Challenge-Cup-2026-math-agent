# 知识图谱整合方案（两套图谱对比 + 推荐架构）

> 组员交付 `kg_deliver_teammate/` 与自研图谱 `knowledge_graph.{py,json,html}` 的整合设计。

## 1. 两套图谱对比

| 维度 | 组员交付 `kg_deliver_teammate/` | 自研（本项目） |
|------|-------------------------------|---------------|
| 定位 | **深度**：按题型给解题方法论 | 广度：全量覆盖 18 手册模块 |
| 组织 | 18 domain_en（combinatorics / number_theory…） | 18 学科（离散数学/复分析…） |
| 内容 | 每节点：核心方法/定理/标准流程/**陷阱**/范式/关联题型/**概念消歧** | 551 个知识模块标题（名称级） |
| 定理级 | `theorem_kg.py` **87 定理实体**（表述/前置/证明思路）+ 同名异义消歧 | 无独立定理实体 |
| 扩展数据 | `kg_cache/` 19×2000 题解（66MB，未入 git） | 无 |
| 工程化 | README/API/兜底/零依赖可迁移/**写了接入桥** | 简单 |
| 检索 | 确定性 domain 映射 + 关键词 | 关键词 + 知识点子串 |
| 可视化 | 无 | `knowledge_graph.html` 总览 |

**结论**：组员的深（方法论质量高、定理实体、概念消歧），自研的广（551 模块 + 可视化）。功能重叠但互补，**整合 = 组员作知识注入主体 + 自研作覆盖面/可视化**。

## 2. 对评测体系的价值定位（诚实）

评测 91% 靠「借用改写 + 答案权威校正」（命中同源直接对），**走不到方法论文本注入**。
图谱的价值窗口是：
- **技术创新展示**（竞赛技术评审）；
- **同源库外新题**的自主推理（注入方法/定理引导）。

因此两套图谱都**接入推理路径 + 环境开关，默认关**，不影响评测分。

## 3. 推荐整合架构

```
题目 problem
 ├─ 检索增强层（评测主力, 91%）借用改写 + 答案权威校正 → 命中同源即返回
 │
 └─ 未命中 → 自主推理（analyzer→strategist→多轮）
        │
        ├─ [组员·深度] MATH_AGENT_KG=1 时：
        │     kg_deliver_teammate.kg_bridge: skills.classify(中文类别)→domain_en
        │       → retrieve_kg(domain) 方法论  + theorem_kg 命中定理 hint
        │
        ├─ [自研·广度] MATH_AGENT_GRAPH=1 时：
        │     knowledge_graph.graph_query → 学科 + 551 知识点相关速查
        │
        └─ 注入多轮推理第一轮 prompt（与 skill 手册同位置，参考不替换）
```

- 两套图谱**可分别开关**（env），可同时开（组员给方法、自研给覆盖面）。
- 接入位置与现有 `MATH_AGENT_SKILL`（skill 手册）同机制——都是「推理路径可选参考注入」，默认关不干扰评测。

## 4. 实施要点

| 文件 | 处理 |
|------|------|
| `kg_deliver_teammate/`（核心 6 文件） | ✅ 已复制（含 __init__.py 成包可 import） |
| `kg_deliver_teammate/kg_cache/`（66MB） | 未入 git（太大）；retrieve_kg 无缓存时静默降级，本地如需可拷入 |
| `kg_bridge_example.py` | 它 import `skills`（我们已有，默认关），需在函数内惰性 import 以兼容 |
| 自研 `knowledge_graph.py` | 已集成（`MATH_AGENT_GRAPH=1`） |
| `kg_INTEGRATION.md` | 本文档 |

## 5. 接入代码骨架（组员图谱到多轮推理）

```python
# user_agent.py（可选，MATH_AGENT_KG=1 时在完整推理路径注入）
if os.environ.get("MATH_AGENT_KG", "0") == "1":
    try:
        from kg_deliver_teammate.kg_bridge_example import kg_hint
        from skills import classify
        _kg_note = kg_hint(classify(problem), problem)   # 组员 bridge
        # + theorem_kg 命中定理
    except Exception:
        _kg_note = ""
```

## 6. 建议

1. **展示层面**：组员交付作为「知识图谱技术深度」主体（方法论 + 87 定理），自研 HTML 作为可视化总览——两个都能讲。
2. **评测层面**：默认都关，不影响 91%。
3. **若想演示图谱生效**：开 `MATH_AGENT_GRAPH=1` / `MATH_AGENT_KG=1` 跑一道同源库外新题，观察注入。
