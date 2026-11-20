# 法规学习系统（law-study）设计

日期：2026-11-20　|　状态：已确认

## 目标

以《医疗器械唯一标识系统规则》（18 条）为首个数据源，构建法规学习系统：

1. **术语字典/实体抽取**：从法规文本规则抽取标识、简称、英文缩写、定义术语，入库成字典
2. **分词器**：词典（实体）优先 + jieba 兜底的混合分词，标点独立成块，分词可无损还原原文
3. **乱序拼句背诵**：按段落分词打乱 → 点击词块组句 + 组句区内拖拽调序 → 自动与原文逐词比对判分；从第一条到最后一条逐条练习，记录进度
4. **AI 解读**：每条两个按钮——AI 解读（要点/角色义务/白话）、实际场景分析（产品经理视角落地动作）；OpenAI 兼容接口，结果缓存可重新生成
5. **法规关联/知识图谱**：法规层级树（法律→行政法规→部门规章→规范性文件）、法规引用图（从「根据/依据《XXX》」抽取）、术语共现图

## 架构

- 后端：FastAPI + SQLAlchemy 2.0 + Alembic + SQLite（`data/law_study.db`），uv 管理
- 前端：Vue 3 + Vite + ECharts 5 + vuedraggable，四个视图（阅读/背诵/字典/图谱），build 后由 FastAPI 托管
- AI：OpenAI 兼容 SDK，`.env` 配 `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL`

## 数据模型

| 表 | 关键字段 | 说明 |
|---|---|---|
| laws | name, doc_number, authority, level, effective_date, source_path, content_hash | 多法规设计，content_hash 防重复导入 |
| articles | law_id, order_no, label | 条（第一条…第十八条） |
| paragraphs | article_id, order_no, text, tokens(JSON) | **原文一字不差**；拼句单元=段落；tokens 为分词缓存（含 term 标记） |
| terms | law_id, name, term_type, full_name, definition, article_id | term_type: definition/short_name/abbreviation |
| relations | from_law_id, to_law_name, to_law_id?, relation_type, article_id | 引用/依据；被引法规未入库时 to_law_id 为空（图谱虚拟节点） |
| readings | article_id, kind, model, content | AI 缓存，kind: interpret/scenario |
| practice_log | paragraph_id, correct, duration_ms | 背诵进度 |

## 实体抽取规则（v1 规则式）

- 定义：`X，是指……`（UDI 第三/八/十七条共 9 个术语）
- 简称：`（以下简称"X"）`（本篇无，通路预留）
- 缩写：`中文名（ABBR）`（本篇无，通路预留）

已知缺口（用户待确认是否属使用场景）：第七条「产品标识」「生产标识」「发码机构」等非「是指」句式，v1 规则抽不到。

## 分词算法

1. 正则切分：汉字串 / 字母数字串 / 标点（标点独立 token）
2. 汉字串：terms 词典按长度降序最大匹配；剩余片段 jieba.cut
3. token 序列拼接 == 原文（无损，测试强校验）

## 已确认决策

1. 拼句含标点块（字面实现，后续可加剥离开关）
2. 判分 = 逐词严格比对，错位标红
3. 导入器同时支持 HTML（UDI 格式）与 MD（法规总表格式）
4. SQLite，数据在 `data/`
5. 导入/建库等一次性任务走独立脚本（`scripts/`），不进应用 lifespan
