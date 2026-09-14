"""build_viz.py — 生成 knowledge_graph.html（可视化总览，内嵌图谱数据，离线可开）。"""
import json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = json.loads((HERE / "knowledge_graph.json").read_text(encoding="utf-8"))

# 内嵌数据
data_json = json.dumps(G, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>数学定理 / 知识图谱</title>
<style>
  body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; margin: 0; background: #f6f8fb; color: #223; }
  header { background: linear-gradient(135deg,#1b3a6b,#2e6fb7); color: #fff; padding: 26px 34px; }
  header h1 { margin: 0; font-size: 24px; } header p { margin: 6px 0 0; opacity: .85; }
  .stat { display: inline-block; margin-right: 22px; }
  .stat b { font-size: 22px; }
  .wrap { padding: 22px 34px; }
  #search { width: 100%; max-width: 720px; padding: 12px 16px; font-size: 15px; border-radius: 8px; border: 1px solid #c6d3e3; }
  .disciplines { display: flex; flex-wrap: wrap; gap: 10px; margin: 18px 0; }
  .dchip { padding: 8px 14px; border-radius: 20px; background: #e7eefb; cursor: pointer; border: 1px solid #c6d8f0; }
  .dchip.active { background: #2e6fb7; color: #fff; }
  .topic-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(210px,1fr)); gap: 10px; }
  .topic { background: #fff; border: 1px solid #e2e9f3; border-left: 4px solid #2e6fb7; border-radius: 6px; padding: 10px 12px; font-size: 13.5px; }
  .topic.hit { background: #fff7e0; border-left-color: #e8a020; }
  .dis-detail { margin-top: 20px; }
  .dis-detail h3 { margin: 0 0 12px; }
  .foot { padding: 18px 34px 30px; color: #688; font-size: 12px; }
</style>
</head>
<body>
<header>
  <h1>📐 数学定理 / 知识图谱</h1>
  <p>从 18 本学科解题技能手册构建 —— 学科 → 知识点（定理/方法/公式），用于解题时定位「该用哪条定理」</p>
  <p style="margin-top:10px">
    <span class="stat">学科 <b id="s_dis"></b></span>
    <span class="stat">知识点节点 <b id="s_node"></b></span>
    <span class="stat">关系边 <b id="s_edge"></b></span>
  </p>
</header>
<div class="wrap">
  <input id="search" placeholder="🔍 输入题目关键词检索相关知识点（如：组合 / prime / 特征值 / residue）…">
  <div id="discs" class="disciplines"></div>
  <div id="detail" class="dis-detail"></div>
</div>
<div class="foot">知识图谱模块 · 构建自 skills_pythonscripts/ 18 学科手册 · 检索注入可经 MATH_AGENT_GRAPH=1 开启</div>

<script>
const G = __DATA__;
const KW = __KEYWORDS__;
let active = null;

document.getElementById("s_dis").textContent = G.disciplines.length;
document.getElementById("s_node").textContent = G.meta.node_count;
document.getElementById("s_edge").textContent = G.meta.edge_count;

function byDisc(d){ return G.nodes.filter(n => n.discipline === d); }

function renderDiscs(){
  const box = document.getElementById("discs");
  box.innerHTML = "";
  G.disciplines.forEach(d => {
    const el = document.createElement("div");
    el.className = "dchip" + (active === d ? " active" : "");
    el.textContent = d + " · " + byDisc(d).length;
    el.onclick = () => { active = d; renderDiscs(); renderDetail(d, ""); };
    box.appendChild(el);
  });
}

function renderDetail(d, query){
  const box = document.getElementById("detail");
  if(!d){ box.innerHTML = "<div style='color:#889'>选择左侧学科查看其知识点；或用上方搜索框定位相关学科。</div>"; return; }
  const q = query.toLowerCase();
  const topics = byDisc(d);
  const nodes = topics.map(t => {
    const hit = q && (t.name.toLowerCase().includes(q) || t.discipline.toLowerCase().includes(q));
    return "<div class='topic" + (hit ? " hit" : "") + "'>" + escape(t.name) + "</div>";
  }).join("");
  box.innerHTML = "<h3>" + escape(d) + "（" + topics.length + " 个知识点）</h3><div class='topic-grid'>" + nodes + "</div>";
}

// 搜索：按学科关键词命中
document.getElementById("search").addEventListener("input", e => {
  const q = e.target.value.trim();
  if(!q){ active = null; renderDiscs(); renderDetail(null,""); return; }
  const hits = [];
  for(const d in KW){ if(KW[d].some(k => q.toLowerCase().includes(k.toLowerCase()))) hits.push(d); }
  const direct = G.nodes.filter(n => n.name.toLowerCase().includes(q.toLowerCase()));
  direct.forEach(n => { if(!hits.includes(n.discipline)) hits.push(n.discipline); });
  // 渲染命中学科 + 具体命中知识点
  renderDiscs();
  const box = document.getElementById("detail");
  box.innerHTML = "<h3>命中学科：" + (hits.length ? hits.join("、") : "（无）") + "</h3>";
  hits.forEach(d => {
    const matched = byDisc(d).filter(t => {
      const tl = t.name.toLowerCase();
      return KW[d].some(k => q.toLowerCase().includes(k.toLowerCase())) || tl.includes(q.toLowerCase());
    });
    const shown = (matched.length ? matched : byDisc(d).slice(0, 6));
    box.innerHTML += "<div style='margin-top:14px'><b>" + escape(d) + "</b><div class='topic-grid'>" +
      shown.map(t => "<div class='topic hit'>" + escape(t.name) + "</div>").join("") + "</div></div>";
  });
});

renderDiscs();
renderDetail(null,"");
</script>
</body>
</html>"""

html = html.replace("__DATA__", data_json)
html = html.replace("__KEYWORDS__", json.dumps({  # 前端搜索用精简词（读不到 python 常量，简单内联）
    "离散数学": ["组合", "递推", "数论", "整除", "素数", "图", "博弈", "graph", "prime", "game", "board", "gcd", "combin", "counting", "permutation"],
    "高等代数": ["矩阵", "行列式", "特征值", "多项式", "matrix", "determinant", "eigenvalue", "linear", "polynomial", "rank"],
    "复分析": ["留数", "柯西", "residue", "contour", "holomorphic", "cauchy", "laurent", "complex", "pole", "conformal"],
    "数学分析": ["极限", "积分", "级数", "收敛", "limit", "integral", "series", "continuous", "derivative", "convergence", "supremum", "taylor"],
    "概率论": ["概率", "随机变量", "期望", "概率", "probability", "random", "expectation", "variance", "distribution", "expectation"],
    "数值分析": ["数值", "差分", "插值", "牛顿", "numerical", "difference", "interpolation", "newton", "finite", "iteration"],
    "偏微分方程": ["偏微分", "热方程", "拉普拉斯", "pde", "heat", "wave", "laplacian", "boundary"],
    "常微分方程": ["常微分", "ode", "differential", "initial value", "bernoulli"],
    "抽象代数": ["群", "环", "域", "同态", "group", "subgroup", "homomorphism", "galois", "sylow", "field", "ideal", "ring", "dihedral"],
    "线性回归": ["回归", "最小二乘", "regression", "least squares", "residual", "ols", "vif"],
    "统计推断": ["估计", "置信", "假设检验", "样本", "estimate", "confidence", "hypothesis", "sample", "likelihood"],
    "随机过程": ["马尔可夫", "布朗", "markov", "brownian", "poisson", "martingale", "random walk"],
    "测度积分": ["测度", "勒贝格", "measure", "lebesgue", "measurable"],
    "拓扑学": ["拓扑", "紧致", "连通", "topolog", "compact", "connected", "homeomorph"],
    "微分几何": ["曲率", "测地线", "流形", "curvature", "geodesic", "manifold", "surface"],
    "泛函分析": ["巴拿赫", "希尔伯特", "算子", "banach", "hilbert", "operator", "functional"],
    "运筹学": ["线性规划", "单纯形", "调度", "linear programming", "simplex", "schedule", "tournament", "optimization", "transportation"],
    "非基础及进阶课程": ["几何", "三角", "凸", "triangle", "polygon", "circumcircle", "chessboard", "geometry", "convex", "angle"]
}, ensure_ascii=False))

out = HERE / "knowledge_graph.html"
out.write_text(html, encoding="utf-8")
print(f"可视化已生成 -> {out}")
