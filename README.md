# 法规学习系统（law-study）

面向法规背诵与理解的学习工具：术语字典、分词拼句背诵、AI 解读、法规知识图谱。

## 快速开始

```bash
# 1. 首次建库（Alembic 迁移）
uv run alembic upgrade head

# 2. 导入法规（幂等，可反复执行）
uv run python scripts/import_law.py "/path/to/法规.html"

# 3. 配置 AI（可选，用于 AI 解读/场景分析）
cp .env.example .env   # 填 AI_BASE_URL / AI_API_KEY / AI_MODEL

# 4. 一键启动（自动构建前端）
./run.sh               # http://127.0.0.1:8790
```

## 开发模式

```bash
# 后端（只监听 app/ 源码目录，避免扫描 data/）
uv run uvicorn app.main:app --reload --reload-dir app --port 8790

# 前端（另开终端，代理 /api 到 8790）
cd web && npm run dev   # http://localhost:5174
```

## 功能

| 模块 | 说明 |
|---|---|
| 阅读 | 全文展示（原文一字不差），术语自动高亮（悬停看定义），每条可触发 AI 解读 / 场景分析（缓存，可重新生成）；GMP 条文上带「检查项 N」「相关标准 N」标签，点击跳到对应的检查指导原则条目或标准 |
| 拼句背诵 | 条款段落分词打乱 → 点击词块组句 / 拖拽调序 → 组满自动逐词判分；从第一条到最后一条逐段推进，进度标记 |
| 术语字典 | 从「X，是指…」「（以下简称"X"）」「中文名（ABBR）」规则抽取；拼句时术语整词出现不拆分 |
| 知识图谱 | 法规层级树（引用关系为父子）、法规引用图、术语共现图 |
| 检查指导原则 | `/inspect`：医疗器械 GMP 六份检查指导原则（通用、无菌、植入性、体外诊断试剂、定制式义齿、独立软件）的检查项全文，可按条款、风险等级筛选，点条款号回到阅读页 |
| 标准地图 | `/standards`：与器械 GMP、药品 GMP 各章条对应的国家标准、医药行业标准、药典通则、计量技术规范，按法规和章浏览，显示现行状态与代替关系；文档版见 `docs/gmp-standards-map.md` |

## 导入格式

- **HTML**：`<section><h2>第X条</h2><p>…</p></section>` 结构（如 医疗器械唯一标识系统规则.html）
- **MD**：法规总表格式（YAML 元数据 + `第X条` 切条，空行分段；章/节标题不论纯文本、加粗还是斜体都跳过）。没有「第X条」的附录按数字编号（1.1、2.1.1）切条；第一条之前、章标题之后不带条号的内容按章各成一条

同一法规重复导入按名称**原位更新**（幂等）：法规与条款 ID 不变，文本未变的段落保留原 ID，已生成的解读和练习记录不丢；改了文字的段落、换了内容的条款删旧建新（其练习记录、解读一并清除）。

## 测试

```bash
uv run pytest    # 37 例：解析器/抽取器/分词器/API 端到端/一字不差校验/解读草稿导入/重复导入原位更新/检查项与标准地图的构建（法规总表在本机时另校验真实法规文件）
```

## 静态快照只读模式（GitHub Pages）

后端不可用时前端自动回退读取 `web/public/api-snapshot/` 下的导出快照，顶部显示只读横幅；
阅读 / 拼句背诵（打乱与判分在本地进行）/ 术语字典 / 知识图谱 / **AI 解读与场景分析（只读展示快照中已生成内容）** 均可浏览；练习进度与「重新生成」不可用。

```bash
uv run python scripts/snapshot.py    # 数据库变更后重新导出，随 vite build 拷入 dist
```

AI 解读发布工作流：本地配置 .env 后在阅读页点「AI 解读 / 场景分析」生成（缓存进 readings 表）→ 重跑 snapshot.py（导出 law-N-readings.json）→ push，Pages 即只读展示这些历史解读；本地仍可随时「重新生成」拿新版本。

也可不调模型接口，直接导入写好的解读草稿：一个文件一份，放在 `data/readings-drafts/law-N/a{条款ID}-{interpret|scenario}.md`（正文 markdown），运行 `uv run python scripts/import_readings.py` 入库（同条款同类型已有的跳过；改了草稿要同步入库加 `--update`，只覆盖内容有变化的）。

检查指导原则与标准地图的数据在 `web/public/data/`（`inspection.json`、`standards.json`），随前端一起发布，改动后由 `scripts/build_inspection.py`（解析检查指导原则 md 表格）和 `scripts/build_standards_doc.py`（渲染 `docs/gmp-standards-map.md`）重新生成。

