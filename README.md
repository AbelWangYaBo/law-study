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
| 阅读 | 全文展示（原文一字不差），术语自动高亮（悬停看定义），每条可触发 AI 解读 / 场景分析（缓存，可重新生成） |
| 拼句背诵 | 条款段落分词打乱 → 点击词块组句 / 拖拽调序 → 组满自动逐词判分；从第一条到最后一条逐段推进，进度标记 |
| 术语字典 | 从「X，是指…」「（以下简称"X"）」「中文名（ABBR）」规则抽取；拼句时术语整词出现不拆分 |
| 知识图谱 | 法规层级树（引用关系为父子）、法规引用图、术语共现图 |

## 导入格式

- **HTML**：`<section><h2>第X条</h2><p>…</p></section>` 结构（如 医疗器械唯一标识系统规则.html）
- **MD**：法规总表格式（YAML 元数据 + `第X条` 切条，空行分段，`**第X章**` 跳过）

同一法规重复导入按名称重建（幂等）。

## 测试

```bash
uv run pytest    # 15 例：解析器/抽取器/分词器/API 端到端/一字不差校验
```

## 静态快照只读模式（GitHub Pages）

后端不可用时前端自动回退读取 `web/public/api-snapshot/` 下的导出快照，顶部显示只读横幅；
阅读 / 拼句背诵（打乱与判分在本地进行）/ 术语字典 / 知识图谱均可浏览，AI 解读与练习进度不可用。

```bash
uv run python scripts/snapshot.py    # 数据库变更后重新导出，随 vite build 拷入 dist
```

