# GMP 内容、检查指导原则与标准地图 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把器械 GMP、药品 GMP 全套（最新版逐条解读、旧版备查）做进法规学习系统，新增「检查指导原则」「标准地图」两个页面并与 GMP 条文互链。

**Architecture:** 法规沿用现有流水线（`import_law` 原位入库 → 解读草稿 → `import_readings.py` → `snapshot.py`）。检查项与标准是只读数据，由脚本生成为 `web/public/data/*.json`，前端用相对路径读取，本地动态模式和 Pages 快照模式读同一份文件，不新增表和接口。互链靠「法规名 + 条号或编号」：阅读页条款标题旁显示「检查项 N」「相关标准 N」，另外两个页面可跳回阅读页并滚动到对应条款。

**Tech Stack:** Python 3.12 + uv、FastAPI、SQLAlchemy、pytest；Vue 3 + Vite + vue-router（hash 路由）+ marked；页面实测用 CDP 工具 `scripts/cdp.mjs`（DevTools 协议连接本机 Chrome）。

**规范：** [设计规范](../specs/2026-11-25-gmp-content-and-standards-design.md)

---

## 文件结构

| 文件 | 职责 | 动作 |
|---|---|---|
| `scripts/cdp.mjs` | 用 CDP 打开网页：渲染后的 HTML、可见文本、截图、执行脚本 | 新建 |
| `app/importer/parsers.py` | MD 解析：新增「部分 + 数字编号」切条；新增 `chapter_ranges` | 修改 |
| `tests/test_parsers.py` | 解析器测试 | 修改 |
| `scripts/build_inspection.py` | 检查指导原则 md 表格 → `inspection.json` | 新建 |
| `tests/test_build_inspection.py` | 上者的测试 | 新建 |
| `scripts/build_standards_doc.py` | 标准地图文档渲染 + 刷新「章 → 条款范围」 | 新建 |
| `tests/test_build_standards_doc.py` | 上者的测试 | 新建 |
| `web/public/data/inspection.json` | 检查指导原则静态数据 | 生成 |
| `web/public/data/standards.json` | 标准地图静态数据（页面与文档的唯一数据源） | 生成并维护 |
| `docs/gmp-versions.md` | GMP 版本清单 | 新建 |
| `docs/gmp-standards-map.md` | 标准地图文档（由 JSON 渲染） | 生成 |
| `web/src/data.js` | 静态数据读取（带缓存） | 新建 |
| `web/src/main.js` | 路由 | 修改 |
| `web/src/App.vue` | 导航、法规选择器分组 | 修改 |
| `web/src/views/Reader.vue` | 条款锚点、数量标签、跳转滚动、历史版本隐藏解读按钮 | 修改 |
| `web/src/views/InspectView.vue` | 检查指导原则页 | 新建 |
| `web/src/views/StandardsView.vue` | 标准地图页 | 新建 |
| `web/src/style.css` | 新页面样式 | 修改 |
| `README.md` | 功能与数据说明 | 修改 |
| `data/gmp-drafts/` | 调研简报、草稿、校验脚本（不入库） | 运行数据 |
| 法规总表 `/Volumes/APFS_3/法规总表/`（仓库外） | 补抓/更正 GMP 全文、更新标准卡；改动前备份到 `data/source-backup-20261125-gmp/` | 外部数据 |

通用约定：测试命令都在项目根目录用 `uv run pytest …`；提交信息沿用仓库风格（「类别：一句话」，不加署名尾注）。

---

## 阶段 0：调研与版本核对

| 任务 | 内容 | 产出（`data/gmp-drafts/`，不入库） | 状态 |
|---|---|---|---|
| 0.1 器械 GMP 版本地图 | 核实 2025 年版正文、五个附录、2014 年版旧规范、六份检查指导原则的版本与来源；把缺失的全文补进法规总表并与官方原文比对 | `device-gmp-version-map.md` | 已启动 |
| 0.2 药品 GMP 版本地图 | 核实正文与全部附录的现行版本（重点：无菌药品附录 2026 年修订、药用辅料与药包材附录、中药饮片附录征求意见稿）；补抓缺失或过时的全文 | `pharma-gmp-version-map.md` | 已启动 |
| 0.3 器械 GMP 标准调研（管理类章节） | 第一、二、三、六、七、八、十二、十三、十四章相关的国标、行标、计量规范；复核法规总表已有标准卡 | `standards-device-mgmt.md`、`.json` | 已启动 |
| 0.4 器械 GMP 标准调研（厂房、生产、质控类章节） | 第四、五、九、十、十一章及无菌、植入性附录相关的标准、药典通则 | `standards-device-prod.md`、`.json` | 已启动 |
| 0.5 药品 GMP 标准调研 | 药典、药用辅料与药包材标准、洁净室与检验标准、药品 GMP 指南 | `standards-pharma.md`、`.json` | 有空位后启动 |
| 0.6 器械 GMP 调研简报 | Task A7 Step 1 | `brief-device-gmp.md` | 0.1 完成后 |
| 0.7 药品 GMP 调研简报 | Task A7 Step 2 | `brief-pharma-gmp.md` | 0.2 完成后 |

- [ ] **每个调研任务完成后的检查**：版本地图每一行都有官方来源 URL；标「未核实」「未获取」的条目单独列出；补抓的全文文件能用解析器切出条款，条数与官方文本一致；标准 JSON 能被 `json.load` 读出、字段齐全。
- [ ] **合并版本清单交用户确认**（Task A4 Step 1）：清单里每个文件标明现行还是旧版，旧版的效力层级写「历史版本」。用户确认之前不导入、不出解读。

---

## 阶段 A：内容入库与解读

### Task A0: CDP 页面工具

**背景：** 页面实测需要真实渲染。按要求，打开网页走 CDP（DevTools 协议）连接本机 Chrome，不用 Playwright、无头模式等带 testing 标识、会被网站拦截的方式；后面所有页面验证都用这个工具。它只是给普通的 Chrome 开一个调试端口（独立用户数据目录），网站看到的就是一个正常打开的浏览器。

**Files:**
- Create: `scripts/cdp.mjs`

- [x] **Step 1: 新建 `scripts/cdp.mjs`**

```js
// 用本机 Chrome 的 CDP（DevTools 协议）打开网页：取渲染后的 HTML、可见文本、截图，或在页面里执行脚本。
// 不用 Playwright 一类自动化框架：它们启动浏览器时会带 testing 标识，容易被网站拦截。
// 这里只是给普通的 Chrome 开一个调试端口，网站看到的就是一个正常打开的浏览器。
//
// 用法:
//   node scripts/cdp.mjs html <url> [--wait 毫秒]              渲染后的 HTML
//   node scripts/cdp.mjs text <url> [--wait 毫秒]              可见文本
//   node scripts/cdp.mjs shot <url> <输出.png> [--wait 毫秒] [--width 1300] [--height 2200] [--fold 只截可视区域]
//   node scripts/cdp.mjs eval <url> '<js 表达式>' [--wait 毫秒]   输出 { url, value }；表达式可以返回 Promise
//
// 首次运行会用独立的用户数据目录（data/chrome-profile）启动本机 Chrome 并开启调试端口（默认 9333），
// 之后复用这个实例；--port 可换端口。

import { spawn } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

function parseArgs(argv) {
  const [mode, ...rest] = argv
  const opts = { wait: 2500, width: 1300, height: 2200, port: 9333 }
  const positional = []
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === '--fold') { opts.fold = true; continue }
    if (rest[i].startsWith('--')) opts[rest[i].slice(2)] = Number(rest[++i])
    else positional.push(rest[i])
  }
  return { mode, positional, opts }
}

async function ensureChrome(port) {
  const base = `http://127.0.0.1:${port}`
  const alive = () => fetch(`${base}/json/version`).then(r => r.ok, () => false)
  if (await alive()) return base
  mkdirSync(path.join(ROOT, 'data', 'chrome-profile'), { recursive: true })
  spawn(CHROME, [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${path.join(ROOT, 'data', 'chrome-profile')}`,
    '--no-first-run', '--no-default-browser-check', 'about:blank',
  ], { detached: true, stdio: 'ignore' }).unref()
  for (let i = 0; i < 40 && !(await alive()); i++) await new Promise(r => setTimeout(r, 250))
  if (!(await alive())) throw new Error(`Chrome 调试端口 ${port} 没有起来`)
  return base
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl)
    let seq = 0
    const waiting = new Map()
    ws.onopen = () => resolve({
      ws,
      send: (method, params = {}) => new Promise((res, rej) => {
        const id = ++seq
        waiting.set(id, { res, rej })
        ws.send(JSON.stringify({ id, method, params }))
      }),
      waitFor: method => new Promise((res, rej) => {
        const timer = setTimeout(() => { ws.removeEventListener('message', onMessage); rej(new Error(`等待 ${method} 超时`)) }, 30000)
        const onMessage = e => {
          if (JSON.parse(e.data).method === method) { clearTimeout(timer); ws.removeEventListener('message', onMessage); res() }
        }
        ws.addEventListener('message', onMessage)
      }),
    })
    ws.onerror = () => reject(new Error(`连不上 ${wsUrl}`))
    ws.onmessage = e => {
      const msg = JSON.parse(e.data)
      const w = waiting.get(msg.id)
      if (!w) return
      waiting.delete(msg.id)
      msg.error ? w.rej(new Error(`${msg.error.message}（${msg.error.data || ''}）`)) : w.res(msg.result)
    }
  })
}

async function main() {
  const { mode, positional, opts } = parseArgs(process.argv.slice(2))
  const [url, arg2] = positional
  if (!url || !['html', 'text', 'shot', 'eval'].includes(mode)) {
    console.info('用法: node scripts/cdp.mjs <html|text|shot|eval> <url> [参数] [--wait 毫秒] [--width N] [--height N] [--port N]')
    process.exit(2)
  }
  const base = await ensureChrome(opts.port)
  // 每次开一个新标签页，用完关掉
  const target = await fetch(`${base}/json/new?about:blank`, { method: 'PUT' }).then(r => r.json())
  try {
    const cdp = await connect(target.webSocketDebuggerUrl)
    await cdp.send('Page.enable')
    await cdp.send('Runtime.enable')
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: opts.width, height: opts.height, deviceScaleFactor: 1, mobile: false })
    const loaded = cdp.waitFor('Page.loadEventFired')
    await cdp.send('Page.navigate', { url })
    await loaded
    await new Promise(r => setTimeout(r, opts.wait))   // 等前端把数据取回来、渲染完

    const evaluate = async expression => {
      const { result, exceptionDetails } = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
      if (exceptionDetails) throw new Error(exceptionDetails.exception?.description || exceptionDetails.text)
      return result.value
    }
    if (mode === 'shot') {
      const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: !opts.fold })
      writeFileSync(arg2, Buffer.from(data, 'base64'))
      console.log(`截图 → ${arg2}`)
    } else if (mode === 'eval') {
      const value = await evaluate(arg2)
      console.log(JSON.stringify({ url: await evaluate('location.href'), value }, null, 1))
    } else {
      console.log(await evaluate(mode === 'html' ? 'document.documentElement.outerHTML' : 'document.body.innerText'))
    }
    cdp.ws.close()
  } finally {
    await fetch(`${base}/json/close/${target.id}`).catch(() => {})
  }
}

main().catch(e => { console.error(e.message); process.exit(1) })
```

- [x] **Step 2: 验证**

Run:

```bash
npm --prefix web run build 2>&1 | tail -1
(python3 -m http.server 4173 --directory web/dist >/tmp/static.log 2>&1 &) ; sleep 2   # 普通静态服务：/api/* 返回 404，前端才进入快照模式
node scripts/cdp.mjs eval "http://localhost:4173/#/" "({ webdriver: navigator.webdriver, ua: navigator.userAgent, law: document.querySelector('h1')?.textContent.trim() })"
node scripts/cdp.mjs shot "http://localhost:4173/#/" /tmp/reader.png --width 1200 --height 1400
```

Expected: `webdriver` 为 false，`ua` 里没有 `Headless`、`Testing` 字样，`law` 是当前法规名；截图用 Read 工具能看到阅读页。不要用 `vite preview` 做静态模式测试——它把 `/api/*` 也回退成 index.html，前端会误以为后端在线。

- [x] **Step 3: 提交**

```bash
git add scripts/cdp.mjs
git commit -m "工具：用 CDP 打开网页（渲染后 HTML、可见文本、截图、执行脚本）"
```

### Task A1: 解析器支持「部分 + 数字编号」文本

**背景：** 器械 GMP 附录没有「第X条」，结构是「第一部分」+ `1.1`、`2.1.1` 这样的编号。三级编号（`2.1.1`）各成一条；二级编号后面紧跟同组三级编号时只是小节标题（`2.1 人员`），否则是独立条款（`1.1`、`4.1`）。

**Files:**
- Modify: `app/importer/parsers.py`
- Test: `tests/test_parsers.py`

- [x] **Step 1: 写失败的测试**（追加到 `tests/test_parsers.py` 末尾）

```python
def test_parse_md_clause_numbered():
    """没有「第X条」的文件按数字编号切条：三级编号各成一条，二级编号作小节标题时跳过、作独立条款时成条。"""
    parsed = parse_md("""---
名称: 测试附录
---

# 测试附录

第一部分  范围和原则

1.1  本附录适用于测试产品。

第二部分  特殊要求

2.1  人员

2.1.1  人员应当具备与岗位相适应的专业知识。

2.1.2  测试应当由专人负责。

第三部分  术  语

3.1  下列术语的含义是：

测试：指验证活动。

第四部分  附  则

4.1  本附录自2026年1月1日起施行。
""")
    assert [(a[1], a[2]) for a in parsed["articles"]] == [
        ("1.1", ["本附录适用于测试产品。"]),
        ("2.1.1", ["人员应当具备与岗位相适应的专业知识。"]),
        ("2.1.2", ["测试应当由专人负责。"]),
        ("3.1", ["下列术语的含义是：", "测试：指验证活动。"]),
        ("4.1", ["本附录自2026年1月1日起施行。"]),
    ]
    assert [a[0] for a in parsed["articles"]] == [1, 2, 3, 4, 5]
```

- [x] **Step 2: 确认测试失败**

Run: `uv run pytest tests/test_parsers.py::test_parse_md_clause_numbered -q`
Expected: FAIL，断言里 `parsed["articles"]` 为空列表（当前解析器只认「第X条」）。

- [x] **Step 3: 实现**

在 `app/importer/parsers.py` 里把标题正则的 `[章节]` 扩成 `[章节部分]`，并在其后加三个正则和一个辅助函数：

```python
_MD_HEADING_RE = re.compile(r"^(?:\*\*|__|\*|_)?第[零一二三四五六七八九十百千]+[章节部分][^。；，：？！]{0,40}?(?:\*\*|__|\*|_)?$")
# 没有「第X条」的文件（如器械 GMP 附录）按数字编号切条：二级编号 1.1，三级编号 2.1.1
_MD_CLAUSE_RE = re.compile(r"^(\d+\.\d+)(?![\d.])\s*(.*)$")
_MD_SUBCLAUSE_RE = re.compile(r"^(\d+\.\d+\.\d+)(?![\d.])\s*(.*)$")


def _next_line(lines: list[str], i: int) -> str:
    """第 i 行之后第一个非空行（去掉 markdown 强调符）。"""
    return next((x.strip().lstrip("*") for x in lines[i + 1:] if x.strip()), "")
```

把 `parse_md` 里从 `articles: list[...] = []` 到循环结束的部分整体替换为：

```python
    lines = body.splitlines()
    # 没有「第X条」的文件按数字编号切条
    clause_mode = not any(_MD_ARTICLE_RE.match(line.strip()) for line in lines)

    articles: list[tuple[int, str, list[str]]] = []
    current: tuple[int, str, list[str]] | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if clause_mode:
            m = _MD_SUBCLAUSE_RE.match(stripped)
            if not m:
                m = _MD_CLAUSE_RE.match(stripped)
                # 二级编号：后面紧跟同组的三级编号时只是小节标题（如「2.1 人员」）
                if m and _next_line(lines, i).startswith(m.group(1) + "."):
                    continue
        else:
            m = _MD_ARTICLE_RE.match(stripped)
        if m:
            if current:
                articles.append(current)
            if clause_mode:
                rest = m.group(2).strip()
                current = (len(articles) + 1, m.group(1), [rest] if rest else [])
            else:
                label = f"第{m.group(1)}条"
                first_para = stripped[m.end():].strip()
                current = (cn_num_to_int(m.group(1)), label, [first_para] if first_para else [])
            continue
        if _MD_HEADING_RE.match(stripped) or stripped.startswith(("#", ">", "**目录")):
            continue  # 章/节/部分标题、标题、引用块不入条款
        elif current:
            current[2].append(stripped)
    if current:
        articles.append(current)
```

- [x] **Step 4: 确认测试通过**

Run: `uv run pytest -q`
Expected: 28 passed（原 27 例加本例；`test_parse_md_sample` 等原有用例不受影响）。

- [x] **Step 5: 提交**

```bash
git add app/importer/parsers.py tests/test_parsers.py
git commit -m "解析器：没有「第X条」的文件按「部分 + 数字编号」切条"
```

### Task A2: `chapter_ranges`——「章 → 条款范围」

**背景：** 标准按 GMP 章节归类，而章标题不入库。这个函数从 GMP 的 md 全文算出每章包含哪些条号，供标准地图数据和文档使用。

**Files:**
- Modify: `app/importer/parsers.py`
- Test: `tests/test_parsers.py`

- [x] **Step 1: 写失败的测试**（追加到 `tests/test_parsers.py` 末尾，并把顶部 import 改为 `from app.importer.parsers import chapter_ranges, cn_num_to_int, parse_article_label, parse_html, parse_md`）

```python
def test_chapter_ranges():
    """章标题 → 该章的条号；标题去掉排版空格，没有条目的章（如目录）不输出。"""
    md = """---
名称: 测试法
---

**第一章 总 则**

第一条 为了测试。
第二条 测试条款。

**第二章　机构与人员**

第三条 企业应当。

**第三章 附 则**

第四章 另一条。

第三章

第五条 无标题的章。
"""
    assert chapter_ranges(md) == [
        {"title": "第一章 总则", "articles": [1, 2]},
        {"title": "第二章 机构与人员", "articles": [3]},
        {"title": "第三章 附则", "articles": [4]},
        {"title": "第三章", "articles": [5]},
    ]
```

- [x] **Step 2: 确认测试失败**

Run: `uv run pytest tests/test_parsers.py::test_chapter_ranges -q`
Expected: FAIL，`ImportError: cannot import name 'chapter_ranges'`。

- [x] **Step 3: 实现**（加在 `parse_md` 之前）

```python
def chapter_ranges(md_text: str) -> list[dict]:
    """「章标题 → 该章的条号列表」。标题规范成「第三章 机构与人员」（去掉排版空格），没有条目的章不输出。"""
    ranges: list[dict] = []
    articles: list[int] = []
    for raw in md_text.splitlines():
        s = raw.strip().strip("*").strip()
        m = re.match(r"^(第[零一二三四五六七八九十百千]+章)[ 　]*(.*)$", s)
        if m and not re.search(r"[。；，：？！]", s):
            articles = []
            title = re.sub(r"\s+", "", m.group(2))
            ranges.append({"title": m.group(1) + (f" {title}" if title else ""), "articles": articles})
            continue
        a = _MD_ARTICLE_RE.match(s)
        if a and ranges:
            articles.append(cn_num_to_int(a.group(1)))
    return [r for r in ranges if r["articles"]]
```

- [x] **Step 4: 确认测试通过**

Run: `uv run pytest -q`
Expected: 29 passed。

- [x] **Step 5: 提交**

```bash
git add app/importer/parsers.py tests/test_parsers.py
git commit -m "解析器：从法规全文计算「章 → 条款范围」"
```

### Task A3: 清理独立软件附录文件尾部的网页残留

> 实际执行：阶段 0 的器械 GMP 调研代理已清理该文件（连同 2025 年版正文第 132 条之后的同类残留），原件备份在 `data/source-backup-20261125-gmp/`；主控复核解析结果为 37 条、末条 4.2 只有施行日期一段。下面的 Step 1 脚本未执行（执行会覆盖调研代理留的原件备份）。

**背景：** 该文件在最后一条 `4.2` 之后混进了网页页脚（「相关链接」「附件:」「国家药品监督管理局直属单位」…）和一小节「来源与核验」。Task A1 之后这些行会被并进最后一条，入库前必须清掉。来源信息并入 YAML 的「来源说明」。

**Files:**
- Modify（仓库外）: `/Volumes/APFS_3/法规总表/13_规范性文件/医疗器械生产质量管理规范附录 独立软件.md`
- Backup to: `data/source-backup-20261125-gmp/13_规范性文件/`

- [x] **Step 1: 备份并截掉最后一条之后的内容**

Run（项目根目录）:

```bash
uv run python - <<'EOF'
import shutil
from pathlib import Path

rel = "13_规范性文件/医疗器械生产质量管理规范附录 独立软件.md"
src = Path("/Volumes/APFS_3/法规总表") / rel
bak = Path("data/source-backup-20261125-gmp") / rel
bak.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, bak)

lines = src.read_text(encoding="utf-8").splitlines()
cut = next(i for i, l in enumerate(lines) if l.strip().startswith("4.2"))
note = next((l.split("：", 1)[1].strip() for l in lines[cut + 1:] if l.startswith("- 来源")), "")
lines = lines[:cut + 1]
for i, l in enumerate(lines):
    if l.startswith("来源说明:") and note and note not in l:
        lines[i] = l + "；" + note
src.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("已清理，文件现为", len(lines), "行；备份在", bak)
EOF
```

Expected: 输出「已清理，文件现为 102 行」。

- [x] **Step 2: 确认能切出条款**

Run: `uv run python -c "from app.importer.parsers import parse_file; p = parse_file('/Volumes/APFS_3/法规总表/13_规范性文件/医疗器械生产质量管理规范附录 独立软件.md'); print(len(p['articles']), [a[0] for a in p['articles']])"`
Expected: `37 ['1.1', '1.2', '2.1.1', … '2.8.2', '3.1', '4.1', '4.2']`；最后一个条款 `4.2` 只有「本附录自2020年7月1日起施行。」一段。

- [x] **Step 3: 提交**（仓库内无改动，本任务只动仓库外的数据，不产生提交）

### Task A4: 导入 GMP 法规并核对

**前置：** 阶段 0 的两份版本地图已产出，合并成的版本清单已经用户确认。清单里每个文件一行：入库命名、法规总表路径、版本、文号、公布日、施行日、状态（现行/旧版）、新旧对应、官方来源。

**Files:**
- Create: `docs/gmp-versions.md`

- [x] **Step 1: 写版本清单文档**

把 `data/gmp-drafts/device-gmp-version-map.md` 和 `pharma-gmp-version-map.md` 合并成 `docs/gmp-versions.md`：开头两三句说明（版本以何日核实、现行与旧版的处理方式），然后两张表（器械、药品），列同上。没有取到全文的文件也要列，并写明原因。

- [x] **Step 2: 备份数据库**

Run: `cp -p data/law_study.db data/law_study.db.bak-$(date +%Y%m%d-%H%M)`

- [x] **Step 3: 备份数据库后逐个导入**（对清单里的每个文件；旧版也导入，用于备查）

Run: `uv run python scripts/import_law.py "/Volumes/APFS_3/法规总表/<相对路径>"`
Expected: 每个文件输出「导入完成: <名称>」和条款、段落、术语数量。按清单顺序导入：器械 GMP 正文 → 器械附录 → 药品 GMP 正文 → 药品附录 → 旧版。

- [x] **Step 4: 核对不变量**

Run:

```bash
uv run python - <<'EOF'
import re
from sqlalchemy import text
from app.database import SessionLocal
from app.importer.parsers import parse_file
from app.models import Article, Law, Paragraph, Reading

heading = re.compile(r"^\*{0,2}第[一二三四五六七八九十]+[章节部分][ 　]")
db = SessionLocal()
ok = True
def check(label, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(f"  [{'OK' if cond else '失败'}] {label} {detail}")

check("原有 9 部法规解读仍为 724 条", db.query(Reading).count() >= 724)
for law in db.query(Law).order_by(Law.id).all():
    parsed = parse_file(law.source_path)
    src = {o: ps for o, _, ps in parsed["articles"]}
    got = {a.order_no: [p.text for p in a.paragraphs] for a in law.articles}
    check(f"law {law.id} {law.name[:16]} 与源文件一字不差", src == got, f"{len(src)} 条")
    leaks = [p.text for p in db.query(Paragraph).join(Article).filter_by(law_id=law.id) if heading.match(p.text)]
    check(f"law {law.id} 无标题段残留", not leaks)
    for p in db.query(Paragraph).join(Article).filter_by(law_id=law.id):
        if "".join(t["t"] for t in p.tokens) != p.text:
            check(f"law {law.id} 分词无损", False); break
for name, sql in {
    "解读→条款": "SELECT COUNT(*) FROM readings WHERE article_id NOT IN (SELECT id FROM articles)",
    "练习记录→段落": "SELECT COUNT(*) FROM practice_logs WHERE paragraph_id NOT IN (SELECT id FROM paragraphs)",
    "引用→法规": "SELECT COUNT(*) FROM relations WHERE from_law_id NOT IN (SELECT id FROM laws)",
}.items():
    check(f"无孤儿：{name}", db.execute(text(sql)).scalar() == 0)
print("结论:", "全部通过" if ok else "存在失败项")
db.close()
EOF
```

Expected: 每一行都是 `[OK]`，最后一行「结论: 全部通过」。任何「失败」都要先查明原因再继续。

- [x] **Step 5: 提交**

```bash
git add docs/gmp-versions.md
git commit -m "文档：GMP 版本清单（器械 2025 版、药品 2010 修订版及全部附录）"
```

### Task A5: 法规选择器分组

**背景：** 加上 GMP 全套后法规有三十多部，平铺的下拉框不好找。按「法律法规 / 质量管理规范 / 历史版本」分组，分组由法规名推导。

**Files:**
- Modify: `web/src/App.vue`

- [x] **Step 1: 实现**

`<script setup>` 第一行的 import 改为 `import { computed, provide, ref, watch } from 'vue'`，并在 `watch(currentLawId, …)` 之后、三个 `provide` 之前加入:

```js
// 法规多了以后按三类分组显示；分组由法规名推导，不新增字段
const groups = computed(() => {
  const g = { law: [], gmp: [], history: [] }
  for (const l of laws.value) {
    if (l.name.includes('已被替代')) g.history.push(l)
    else if (l.name.includes('质量管理规范')) g.gmp.push(l)
    else g.law.push(l)
  }
  return [
    { label: '法律法规', list: g.law },
    { label: '质量管理规范', list: g.gmp },
    { label: '历史版本（备查）', list: g.history },
  ].filter(x => x.list.length)
})
```

模板里 `<select>` 内部的 `<option v-for="l in laws" …>` 一行替换为:

```html
        <optgroup v-for="g in groups" :key="g.label" :label="g.label">
          <option v-for="l in g.list" :key="l.id" :value="l.id">{{ l.name }}</option>
        </optgroup>
```

- [x] **Step 2: 构建并确认**

Run: `npm --prefix web run build 2>&1 | tail -3`
Expected: `✓ built in …`，无报错。

- [x] **Step 3: 提交**

```bash
git add web/src/App.vue
git commit -m "前端：法规选择器按法律法规 / 质量管理规范 / 历史版本分组"
```

### Task A6: 阅读页——历史版本隐藏解读按钮、条款锚点、跳转滚动、关联数量标签

**背景：** 三件事一起做，因为都改 `Reader.vue`。(1) 快照模式下整部法规没有解读时（历史版本）不再显示解读按钮；(2) 每条条款加锚点，从别的页面跳回来能滚动到位；(3) 条款标题旁显示「检查项 N」「相关标准 N」，数量来自两份静态数据（Task B、C 生成；文件不存在时不显示标签）。

**Files:**
- Create: `web/src/data.js`
- Modify: `web/src/views/Reader.vue`
- Modify: `web/src/style.css`

- [x] **Step 1: 新建 `web/src/data.js`**（读取函数，加上两个新页面共用的辅助函数：法规简称、条号转中文、跳转到阅读页）

```js
// 静态数据（检查指导原则、标准地图）：本地与 Pages 读同一份 JSON，路径相对于页面，与 api-snapshot 一致
import { inject } from 'vue'
import { useRouter } from 'vue-router'

const cache = {}

export function loadData(name) {
  if (!cache[name]) {
    cache[name] = fetch(`data/${name}.json`).then(resp => {
      if (!resp.ok) throw new Error(`数据缺失: data/${name}.json`)
      return resp.json()
    })
  }
  return cache[name]
}

export const GMP = '医疗器械生产质量管理规范'

// 「医疗器械生产质量管理规范附录 无菌医疗器械」→「无菌医疗器械附录」；《规范》本身 →「规范」
export const shortName = name => {
  if (name === GMP) return '规范'
  const appendix = name.match(/^医疗器械生产质量管理规范附录 (.+)$/)?.[1]
  return appendix ? appendix + '附录' : name
}

const DIGITS = '零一二三四五六七八九'
export function cnNum(n) {   // 3 → 三，110 → 一百一十
  if (n < 10) return DIGITS[n]
  if (n < 20) return '十' + (n % 10 ? DIGITS[n % 10] : '')
  if (n < 100) return DIGITS[Math.floor(n / 10)] + '十' + (n % 10 ? DIGITS[n % 10] : '')
  const rest = n % 100
  return DIGITS[Math.floor(n / 100)] + '百' + (rest ? (rest < 10 ? '零' + DIGITS[rest] : rest < 20 ? '一' + cnNum(rest) : cnNum(rest)) : '')
}

// 跳到阅读页的某一条：?article=条号 或 ?clause=编号
export function useOpenLaw() {
  const laws = inject('laws')
  const currentLawId = inject('currentLawId')
  const router = useRouter()
  return (law, query) => {
    const target = laws.value.find(l => l.name === law)
    if (!target) return
    currentLawId.value = target.id
    router.push({ path: '/', query })
  }
}
```

- [x] **Step 2: 改写 `Reader.vue` 的 `<script setup>`**（`toggleReading`、`regenerate`、`renderMd`、`kindLabel` 四个定义原样保留，放在 `scrollToTarget` 之后）

```vue
<script setup>
import { computed, inject, nextTick, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { api } from '../api'
import { loadData } from '../data'

const currentLawId = inject('currentLawId')
const snapshot = inject('snapshot', false)
const route = useRoute()
const detail = ref(null)
const termsById = ref({})
const readings = reactive({})   // key: `${articleId}:${kind}`
const storedReadings = ref({})  // 快照/后端已有解读，key 同上（取最新一条）
const hasReadings = ref(false)
const inspectCount = reactive({})    // 条号或编号 → 检查项数
const standardsCount = reactive({})  // 条号或编号 → 相关标准数

const law = computed(() => detail.value)
// 快照模式下整部法规没有解读时（如历史版本），不显示解读按钮
const showReadings = computed(() => !snapshot || hasReadings.value)
// 编号类法规（如 GMP 附录）按「2.1.1」这样的编号定位，其余按条号
const clauseMode = computed(() => /^\d+\.\d+/.test(law.value?.articles?.[0]?.label || ''))
const linkQuery = a => (clauseMode.value ? { law: currentLawId.value, clause: a.label } : { law: currentLawId.value, article: a.order_no })
const inspectCountOf = a => inspectCount[a.order_no] || inspectCount[a.label] || 0
const standardsCountOf = a => standardsCount[a.order_no] || standardsCount[a.label] || 0

async function load() {
  detail.value = await api.lawDetail(currentLawId.value)
  const terms = await api.lawTerms(currentLawId.value)
  termsById.value = Object.fromEntries(terms.map(t => [t.id, t]))
  try {
    const rs = await api.lawReadings(currentLawId.value)
    const map = {}
    for (const r of rs) map[`${r.article_id}:${r.kind}`] = r   // 后写覆盖 = 最新
    storedReadings.value = map
    hasReadings.value = rs.length > 0
  } catch { /* 老后端或快照缺失：无历史解读 */ hasReadings.value = false }
  await Promise.all([loadInspectCount(), loadStandardsCount()])
  await nextTick()
  scrollToTarget()
}
load()

// 检查指导原则：按「法规名 + 条号或编号」数每条条款对应几个检查项
async function loadInspectCount() {
  try {
    const { docs } = await loadData('inspection')
    for (const d of docs) for (const it of d.items) {
      const keys = it.refs.filter(r => r.law === law.value.name).flatMap(r => [...r.articles, ...r.clauses])
      for (const k of new Set(keys)) inspectCount[k] = (inspectCount[k] || 0) + 1
    }
  } catch { /* 没有检查指导原则数据 */ }
}

// 标准地图：标准映射到整章的，算进该章每一条
async function loadStandardsCount() {
  try {
    const { chapters, standards } = await loadData('standards')
    const chapterArticles = (lawName, title) => chapters.find(c => c.law === lawName && c.title === title)?.articles || []
    for (const s of standards) {
      const keys = s.gmp.filter(g => g.law === law.value.name)
        .flatMap(g => [...g.articles, ...g.chapters.flatMap(t => chapterArticles(g.law, t))])
      for (const k of new Set(keys)) standardsCount[k] = (standardsCount[k] || 0) + 1
    }
  } catch { /* 没有标准地图数据 */ }
}

// 从检查指导原则页、标准地图页跳转过来：?article=条号 或 ?clause=编号，滚动到对应条款
function scrollToTarget() {
  const clause = String(route.query.clause || '')
  const target = Number(route.query.article) || law.value.articles.find(a => a.label === clause)?.order_no
  if (target) document.getElementById(`art-${target}`)?.scrollIntoView({ block: 'start' })
}
```

- [x] **Step 3: 改 `Reader.vue` 模板里条款卡片的开头**

把 `<div v-for="a in law.articles" :key="a.id" class="card" style="margin-bottom:14px;">` 及其后 `<h2>` 到两个 `<button>` 的那段，替换为:

```html
    <div v-for="a in law.articles" :key="a.id" :id="`art-${a.order_no}`" class="card" style="margin-bottom:14px;">
      <div style="display:flex; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:8px;">
        <h2 class="serif" style="margin:0; font-size:18px; letter-spacing:.1em;">{{ a.label }}</h2>
        <router-link v-if="inspectCountOf(a)" class="link-chip" :to="{ path: '/inspect', query: linkQuery(a) }">检查项 {{ inspectCountOf(a) }}</router-link>
        <router-link v-if="standardsCountOf(a)" class="link-chip" :to="{ path: '/standards', query: linkQuery(a) }">相关标准 {{ standardsCountOf(a) }}</router-link>
        <span style="flex:1"></span>
        <template v-if="showReadings">
          <button :title="snapshot ? '展示快照中已生成的解读' : ''" @click="toggleReading(a, 'interpret')">AI 解读</button>
          <button :title="snapshot ? '展示快照中已生成的场景分析' : ''" @click="toggleReading(a, 'scenario')">场景分析</button>
        </template>
      </div>
```

两个标签现在指向还不存在的路由 `/inspect`、`/standards`；数据文件不存在时数量为 0、标签不显示，所以本任务可以先提交。

- [x] **Step 4: 加样式**（追加到 `web/src/style.css` 末尾）

```css
/* 条款标题旁的关联标签（检查项 / 相关标准） */
.link-chip {
  padding: 2px 10px; border-radius: 12px; font-size: 12px; text-decoration: none;
  color: #7a6335; background: #f6efdd; border: 1px solid #e3d5b3;
}
.link-chip:hover { background: #efe3c6; }
```

- [x] **Step 5: 构建、起预览、无头浏览器实测**

Run:

```bash
npm --prefix web run build 2>&1 | tail -2
(python3 -m http.server 4173 --directory web/dist >/tmp/static.log 2>&1 &) ; sleep 2
node scripts/cdp.mjs eval "http://localhost:4173/#/" "({ anchors: document.querySelectorAll('[id^=\"art-\"]').length, chips: document.querySelectorAll('.link-chip').length, groups: document.querySelectorAll('optgroup').length })"
node scripts/cdp.mjs shot "http://localhost:4173/#/" /tmp/reader.png --width 1200 --height 1800
```

Expected: 构建成功；`anchors` 等于当前法规的条款数（锚点都渲染了）；`chips` 是 0（还没有数据）；`groups` 是 2 或 3（分组生效）。用 Read 工具看 `/tmp/reader.png`，页面没有错位。

- [x] **Step 6: 提交**

```bash
git add web/src/data.js web/src/views/Reader.vue web/src/style.css
git commit -m "前端：阅读页条款锚点与关联数量标签，历史版本在快照模式下不显示解读按钮"
```

### Task A7: 撰写前的调研简报

**背景：** 解读里「新旧对照」「现场检查怎么查」「相关标准」「与器械 GMP 的对照」四节都需要核实过的素材。前两份简报由调研代理产出（版本地图完成之后启动，并发不超过 4），后两份由脚本从数据生成。

**Files**（均不入库）:
- Create: `data/gmp-drafts/brief-device-gmp.md`、`data/gmp-drafts/brief-pharma-gmp.md`（调研代理产出）
- Create: `data/gmp-drafts/inspection-by-article.md`（脚本产出，Task B1 生成 `inspection.json` 之后才有；B1 提前到本任务之前执行）

- [x] **Step 1: 启动「器械 GMP 调研简报」代理**

产出 `data/gmp-drafts/brief-device-gmp.md`，须覆盖：
1. 2025 年版的官方解读要点（药监局政策解读、培训材料）：为什么修订、主要变化、实施过渡安排。
2. **新旧对照表**：2014 年版 84 条 ↔ 2025 年版 132 条，逐条写「新版条号 ← 旧版条号，关系（新增 / 改写 / 沿用 / 拆分 / 合并）」。以两版原文逐条比对得出，注明是比对结论。
3. 五个附录的定位、与正文的关系、要点。
4. 检查动态：新版施行后的飞行检查、典型缺陷、处罚案例（真实、可溯源；当事人用泛称）。
5. 与 GB/T 42061（ISO 13485）、GB/T 42062 的关系。
6. 撰写提示：容易写错的点。

- [x] **Step 2: 启动「药品 GMP 调研简报」代理**

产出 `data/gmp-drafts/brief-pharma-gmp.md`，须覆盖：
1. 正文与全部附录的章节结构、各自定位；2025—2026 年附录更新的要点。
2. **章节对照表**：药品 GMP 各章 ↔ 器械 GMP（2025 年版）各章的对应关系，以及整体差异（如药品独有的物料与产品、委托生产与委托检验）。
3. 《药品GMP指南》、中国药典（现行版）与 GMP 的关系，相关通则。
4. 药品 GMP 检查中的典型缺陷与案例（真实、可溯源，当事人用泛称）。
5. 撰写提示：容易写错的点、器械企业对照学习时该看什么。

- [x] **Step 3: 生成「每条条款对应的检查项」**

Run（Task B1 完成后）:

```bash
uv run python - <<'EOF'
import json
from collections import defaultdict
from pathlib import Path

data = json.loads(Path("web/public/data/inspection.json").read_text(encoding="utf-8"))
by = defaultdict(list)
for d in data["docs"]:
    for it in d["items"]:
        for r in it["refs"]:
            for n in r["articles"]:
                by[(r["law"], n)].append(it)
            for c in r["clauses"]:
                by[(r["law"], c)].append(it)
GMP = "医疗器械生产质量管理规范"
title = lambda law: "《规范》" if law == GMP else "《" + law.replace("附录 ", "附录：") + "》"
out = ["# 每条 GMP 条款对应的检查项（由 inspection.json 生成）", ""]
for (law, key), items in sorted(by.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
    name = title(law)
    out += [f"## {name} {key}", ""]
    for it in items:
        out.append(f"- {it['clause']}（{it['level']}）{it['content']}")
    out.append("")
Path("data/gmp-drafts/inspection-by-article.md").write_text("\n".join(out), encoding="utf-8")
print(len(by), "条条款有对应检查项")
EOF
```

Expected: 输出条数大于 150；文件里每个条号下列出条款号、风险等级和检查内容。

### Task A8: 导出条文素材，先做试点批次

**Files**（不入库）:
- Create: `data/readings-drafts/law-<ID>-articles.md`（每部新法规一份）
- Create: `data/gmp-drafts/_validate_gmp.py`（校验脚本）

- [x] **Step 1: 导出条文素材**

Run:

```bash
uv run python - <<'EOF'
from pathlib import Path
from app.database import SessionLocal
from app.models import Law

out = Path("data/readings-drafts")
db = SessionLocal()
for law in db.query(Law).order_by(Law.id).all():
    path = out / f"law-{law.id}-articles.md"
    if path.exists():
        continue
    lines = [f"# 《{law.name}》",
             f"law_id={law.id}｜文号：{law.doc_number or '无'}｜发布机关：{law.authority or '未知'}｜效力层级：{law.level or '未知'}｜施行日期：{law.effective_date or '未知'}",
             "格式：`## [id=条款ID] 条款名`，其下为条文原文段落（一字不差）", ""]
    for a in law.articles:
        lines.append(f"## [id={a.id}] {a.label}")
        lines.extend(p.text for p in a.paragraphs)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"law {law.id}: {law.name} | {len(law.articles)} 条")
db.close()
EOF
```

Expected: 列出所有法规；已有的 9 部不会重复导出。

- [x] **Step 2: 写校验脚本 `data/gmp-drafts/_validate_gmp.py`**

以 `data/readings-drafts/_validate.py` 为底，把 `REQUIRED` 改成按法规族区分（通过命令行参数指定族：`device` 或 `pharma`）：

```python
REQUIRED = {
    "device": {
        "interpret": ["## 本条要点", "## 关键角色与义务", "## 白话解读", "## 记忆锚点"],
        "scenario": ["## 落地场景", "## 对产品经理意味着什么", "## 现场检查怎么查", "## 相关标准", "## 风险提示"],
    },
    "pharma": {
        "interpret": ["## 本条要点", "## 关键角色与义务", "## 白话解读", "## 记忆锚点"],
        "scenario": ["## 落地场景", "## 与器械 GMP 的对照", "## 对产品经理意味着什么", "## 相关标准", "## 风险提示"],
    },
}
```

`BANNED` 增加真实公司名；其余检查（缺失、标题顺序、HTML、占位、引用超出条数）不变。用法：`uv run python data/gmp-drafts/_validate_gmp.py device 10 11`。

- [x] **Step 3: 试点批次**

按附录「撰写规则」启动 1 个撰写代理，范围是器械 GMP 第十条至第二十九条（约 20 条，覆盖质量保证、机构与人员）。完成后：
1. 跑校验脚本，要求 0 问题。
2. 人工抽读 4 份（两条解读、两条场景分析），逐项确认：新旧对照与简报一致、现场检查引用的条款号与风险等级在 `inspection.json` 里能找到、相关标准只用了标准简报里的条目、没有真实公司名。
3. 不合格就改撰写规则并重跑试点；合格才进入 Task A9。

### Task A9: 批量生成解读

> 实际执行：规则放在 `data/gmp-drafts/WRITING-RULES.md`（试点反馈已并入：篇幅按正文计、专项版检查项取舍、参考的触发条件、新旧对照与宣贯口径冲突的处理、开工前先看目录），提示词只给范围；检查项改用 `_inspection_for.py <起始条款ID> <结束条款ID>` 查；分批方案在 `data/gmp-drafts/_batches.tsv`（每批 9–32 条）。试点（器械 GMP 第十至二十九条）抽检结论：新旧对照 20 条全部与简报一致，检查项引用 39 处、标准号 62 处均可在数据里找到，校验 0 问题。

> 实际执行（续）：账户同时只能跑 2–3 个代理（4 个即 429），另有 5 小时使用上限（错误码 1308），到限后所有代理中断，重置后用 SendMessage 恢复。因此改为每批一份素材（`_batch_material.py <法规ID> <起> <止>` → `data/gmp-drafts/_materials/`，撰写代理只读规则和这一份）、分批方案改用 `_batches_v2.tsv`（law 11–31 共 45 批、每批 9–38 条）、每批完成即存档：校验 → `_crosscheck.py <法规ID>` → `import_readings.py`（改过的草稿加 `--update`）→ `snapshot.py` → 提交推送 → `_progress.py`。
>
> 进度（2026-11-26 09:00 止；abel 要换模型，暂停在这里）。已写完、校验 0 问题、入库并上线（c8b4ca0）的：器械 GMP 正文 132 条和五个附录（无菌 52、植入性 72、体外诊断试剂 67、定制式义齿 35、独立软件 37）共 395 条、790 份；药品 GMP 正文 313 条、626 份；无菌药品附录 81 条、162 份；原料药附录 2 条、4 份。合计 812 条、1624 份（原有 724 份之外）。**剩余 633 条、1266 份、29 批**：
>
> - 素材已生成的 20 批（362 条），素材在 `data/gmp-drafts/_materials/`：原料药后半 `law-18-1173-1193`（已有 4 份，规则是已有文件跳过）；确认与验证 `law-19-1194-1220`、`law-19-1221-1246`，另有 `law-19-2018-2019`（第二十四、二十五条因重导 ID 靠后，给写前半的代理一并写）；计算机化系统 `law-20-1247-1270`；放射性药品 `law-21-1271-1292`、`law-21-1293-1314`；取样 `law-25-1451-1459`；生化药品 `law-26-1460-1481`、`law-26-1482-1503`；中药制剂 `law-22-1315-1336`、`law-22-1337-1358`；中药饮片 `law-23-1359-1386`、`law-23-1387-1414`；医用氧 `law-24-1415-1450`；临床试验用药品 `law-27-1504-1529`、`law-27-1530-1554`。
> - 等第四组标准调研（生物制品、血液制品、药用辅料、药包材）的 9 批（253 条）：任务说明在 `data/gmp-drafts/_research_prompts.md` 的「任务 D」，产出 `standards-pharma-appendices-d.json/.md`，合并之后才生成素材。
>
> 标准调研进度：`standards.json` 共 409 项。器械五个附录、药品 11 个附录都已补上映射，只剩第四组（药品生物制品、血液制品、药用辅料、药包材）。
>
> 换模型后续跑的方法：
> 1. 撰写代理的提示词只给范围：角色句（今天日期、直接执行不分派）→ 「先完整阅读撰写规则」`data/gmp-drafts/WRITING-RULES.md` → 法规族 / 法规名 / 法规ID / 条款ID 范围与份数 / 写入目录 / 素材路径 / 自检命令 → 一两句针对该段的提示。药品附录类的提示见 Task A9 下 2026-11-25 晚的几次启动记录（对照器械附录要先核对条款号；A/B/C/D 级与 100/10 000/100 000 级不换算）。
> 2. 每批完成即存档：`_validate_gmp.py <device|pharma> <法规ID>` → `_crosscheck.py <法规ID>` → `scripts/import_readings.py --update` → `scripts/snapshot.py`（输出只取末行）→ 本地提交 → 推送 → `_progress.py`。
> 3. 并发：同时不超过 3 个代理，**启动前先用 ListAgents 数在跑的**（11-25 晚数错过一次，并发到 4 个立刻被限速）；调研代理请求最密，最好同一时间只带 1 个撰写代理；被 429（1302 短时或 1308 五小时上限）打断的代理用 SendMessage 恢复，保留上下文。
> 4. 第四组调研产出后：`_check_standards.py` → `_merge_standards.py /tmp/x.json` 试合并比对 → `_merge_standards.py` → `scripts/build_standards_doc.py` → `uv run pytest -q` → 备份 `/Volumes/APFS_3/法规总表.csv`（在法规总表目录的上一级）→ `_update_cards.py`（先预览再 `--apply`）→ 刷新 `_standards_existing.tsv` → `_batch_material.py` 生成素材。
> 5. 全部写完后的收尾见 Task C5（README 已补，还需完整验证、计划勾选、记忆更新）。
>
> 今晚查实并修掉的问题，续跑时别再踩：确认与验证附录曾漏切第二十五条（源文件 PDF 残留字符，解析器已修，重导后第二十四、二十五条 id 是 2018、2019）；命令和源码里绝不输入不可见的字面字符；同一条标准的说明在器械、药品两边共用，合并脚本现在会给跨法规追加的说明带上法规名。
>
> 已更正的数据错误：GB/T 25915.1-2021 在植入性附录的映射条款号整体错后一位（改为 2.2.2~2.2.8、2.2.11）；药典通则 0261 的用途说明把检查指导原则 4.7.6 的注写成了附录 2.3.3 的规定（附录条文只写「满足产品质量要求」），法规总表 `GMP 标准地图.md` 同步更正，原件备份在 `data/source-backup-20261125-gmp/14_标准_国标行标/`。

**规则：** 每个撰写代理 15–20 条；同时运行的代理不超过 4 个；只对清单里标「现行」的文件生成，旧版不生成；每批完成即跑校验脚本。

- [ ] **Step 1: 分批启动**（器械 GMP 正文 → 器械附录 → 药品 GMP 正文 → 药品附录），每批的汇报必须写明：写入文件数、缺失或跳过的条款、需要主控注意的事实风险。
- [ ] **Step 2: 全量校验**

Run: `uv run python data/gmp-drafts/_validate_gmp.py device <器械类法规ID…> && uv run python data/gmp-drafts/_validate_gmp.py pharma <药品类法规ID…>`
Expected: 每部法规「应有 N 份」与实际一致，问题 0 项。
- [ ] **Step 3: 抽检与修正**：每部法规随机抽 2 份人工阅读；处理各批汇报里的事实风险；统计「未在条文/简报中找到的引文」并排除误引。

### Task A10: 导入解读、导出快照、测试、构建、推送

- [ ] **Step 1: 导入解读**

Run: `uv run python scripts/import_readings.py`
Expected: 「导入 N 份解读 → readings 表」，N 等于草稿文件数。

- [ ] **Step 2: 核对数据库**

每部现行版法规：条款数 × 2 = 解读数；每条恰好一份 interpret、一份 scenario；旧版解读数为 0；原有 9 部的 724 条解读的 id → 条款映射不变。

- [ ] **Step 3: 导出快照并核对**

Run: `uv run python scripts/snapshot.py | tail -1`
Expected: 「快照导出完成：N 部法规」；抽查 `web/public/api-snapshot/law-<ID>-readings.json` 条数正确。
- [ ] **Step 4: 测试与构建**

Run: `uv run pytest -q && npm --prefix web run build 2>&1 | tail -1`
Expected: 全部 passed；`✓ built`。
- [ ] **Step 5: 敏感信息扫描**

Run: `grep -lE '/Users/|/Volumes/|Abel|先健|走进' web/public/api-snapshot/*.json web/public/data/*.json 2>/dev/null`
Expected: 无输出。
- [ ] **Step 6: 提交并推送**

```bash
ls data/law_study.db.bak-*      # 确认导入前的数据库备份还在
git add web/public/api-snapshot/
git commit -m "数据：器械 GMP、药品 GMP 全套入库并生成逐条解读，更新静态快照"
git push origin main
gh run watch $(gh run list --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status
```

Expected: Pages 部署 success。核对线上 `law-<ID>-readings.json` 条数与本地一致。

- [ ] **Step 7: 向用户汇报阶段 1 结果**（入库清单、解读数量、抽检结论、遗留问题），再进入阶段 B。

---

## 阶段 B：检查指导原则

**执行时机：** Task B1 要在 Task A7 之前完成（解读里的「现场检查怎么查」依赖 `inspection.json`）；Task B2、B3 在阶段 A 推送之后做。

### Task B1: 检查指导原则表格 → `inspection.json`

**背景：** 法规总表里 6 份检查指导原则各有一张六列表格：章节、序号、条款、内容、风险等级、规范条款。章节列为空的行沿用上一行；`<br>` 是换行；风险等级用星号（`***` 关键、`**` 主要、`*` 一般）；最后一列在通用版叫「《规范》条款」，在专项版叫「规范条款/附录条款」，引用附录时用 `《无菌附录》2.7.5` 这样的编号。

**Files:**
- Create: `scripts/build_inspection.py`
- Test: `tests/test_build_inspection.py`
- Generate: `web/public/data/inspection.json`

- [x] **Step 1: 写失败的测试** `tests/test_build_inspection.py`

```python
"""检查指导原则表格解析：条款引用、章节补全、风险等级。"""

from scripts.build_inspection import GMP, parse_inspection_md, parse_refs

APPENDIX = "医疗器械生产质量管理规范附录 无菌医疗器械"
IMPLANT = "医疗器械生产质量管理规范附录 植入性医疗器械"


def test_parse_refs_merges_by_law_and_inherits_prefix():
    """按法规合并；不带前缀的编号沿用同格内最近的法规；条号区间展开；前缀后可以换行。"""
    cell = "《规范》第十条至第十二条；《无菌附录》2.2.2、2.2.10<br>2.3.1；《植入附录》<br>2.7.5"
    refs, unparsed = parse_refs(cell, {"无菌附录": APPENDIX, "植入附录": IMPLANT})
    assert unparsed == []
    assert refs == [
        {"law": GMP, "articles": [10, 11, 12], "clauses": []},
        {"law": APPENDIX, "articles": [], "clauses": ["2.2.2", "2.2.10", "2.3.1"]},
        {"law": IMPLANT, "articles": [], "clauses": ["2.7.5"]},
    ]


def test_parse_refs_reports_unreadable_text():
    """识别不了的字样进 unparsed；不认识的附录名不会被当成《规范》。"""
    refs, unparsed = parse_refs("《规范》第三条见附件说明；《未知附录》1.1", {})
    assert refs == [{"law": GMP, "articles": [3], "clauses": []}]
    assert unparsed == ["见附件说明", "《未知附录》1.1"]


SAMPLE = """---
名称: 测试检查指导原则
文号发布号: 国药监械管〔2026〕99号
施行日期: 2026-11-01
官方链接: https://example.test/99
---

# 测试检查指导原则

| 章节 | 序号 | 条款 | 内容 | 风险等级 | 规范条款/附录条款 |
| --- | --- | --- | --- | --- | --- |
| 第一章<br>总则 | 1 | 1.1.1 | 企业应当建立质量管理体系。 | *** | 《规范》第三条 |
|  | 2 | 1.2.1 | 风险管理应当贯穿全过程。 | ** | 《规范》第四条；《无菌附录》2.1.1 |
| 第二章质量保证 | 3 | 2.1.1 | 企业应当建立质量目标。 | * | 《规范》第七条 |
| 第五章 | 4 | 5.1.1 | 设备应当满足要求。 | * | 《规范》第十七条 |
"""


def test_parse_inspection_md():
    """文档信息取自 YAML；空章节沿用上一行；缺标题的章用规范的章标题补全；星号映射风险等级。"""
    doc, problems = parse_inspection_md(SAMPLE, "t", "测试", "测试范围", {"无菌附录": APPENDIX}, {"第五章": "第五章 设备"})
    assert problems == []
    assert (doc["name"], doc["doc_number"], doc["effective_date"], doc["source"]) == (
        "测试", "国药监械管〔2026〕99号", "2026-11-01", "https://example.test/99")
    first, second, third, fourth = doc["items"]
    assert (first["chapter"], first["level"], first["refs"]) == ("第一章 总则", "关键", [{"law": GMP, "articles": [3], "clauses": []}])
    assert second["chapter"] == "第一章 总则"
    assert second["refs"] == [{"law": GMP, "articles": [4], "clauses": []}, {"law": APPENDIX, "articles": [], "clauses": ["2.1.1"]}]
    assert second["level"] == "主要"
    assert third["chapter"] == "第二章 质量保证" and third["level"] == "一般"
    assert fourth["chapter"] == "第五章 设备"
```

- [x] **Step 2: 确认测试失败**

Run: `uv run pytest tests/test_build_inspection.py -q`
Expected: ERROR，`ModuleNotFoundError: No module named 'scripts.build_inspection'`。

- [x] **Step 3: 新建 `scripts/build_inspection.py`**

```python
"""把法规总表里的医疗器械 GMP 检查指导原则（md 表格）转成前端用的静态数据。

每个检查项带「《规范》条款」「《附录》条款」引用，前端据此在 GMP 条文和检查项之间互链。
解析不了的引用会打印出来并让脚本以非零状态退出，必须人工过目。

用法: uv run python scripts/build_inspection.py [法规总表目录]
输出: web/public/data/inspection.json
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.importer.parsers import chapter_ranges, cn_num_to_int

KB_DEFAULT = Path("/Volumes/APFS_3/法规总表")
OUT = Path(__file__).resolve().parent.parent / "web" / "public" / "data" / "inspection.json"

GMP = "医疗器械生产质量管理规范"
APPENDIX = "医疗器械生产质量管理规范附录 "
GMP_MD = "13_规范性文件/医疗器械生产质量管理规范.md"
# (id, 名称, 适用范围, 法规总表里的文件, 「《X附录》」写法 → 附录法规名)
DOCS = [
    ("general", "医疗器械生产质量管理规范检查指导原则", "通用",
     "13_规范性文件/医疗器械生产质量管理规范现场检查指导原则.md", {}),
    ("sterile", "医疗器械生产质量管理规范无菌医疗器械检查指导原则", "无菌医疗器械",
     "13_规范性文件/医疗器械生产质量管理规范 - 无菌医疗器械现场检查指导原则.md",
     {"无菌附录": APPENDIX + "无菌医疗器械"}),
    ("implant", "医疗器械生产质量管理规范植入性医疗器械检查指导原则", "植入性医疗器械",
     "13_规范性文件/医疗器械生产质量管理规范 - 植入性医疗器械现场检查指导原则.md",
     {"植入附录": APPENDIX + "植入性医疗器械"}),
    ("ivd", "医疗器械生产质量管理规范体外诊断试剂检查指导原则", "体外诊断试剂",
     "20_指导原则/体外诊断试剂/医疗器械生产质量管理规范体外诊断试剂检查指导原则（2026）.md",
     {"体外诊断试剂附录": APPENDIX + "体外诊断试剂"}),
    ("denture", "医疗器械生产质量管理规范定制式义齿检查指导原则", "定制式义齿",
     "20_指导原则/口腔器械/医疗器械生产质量管理规范定制式义齿检查指导原则（2026）.md",
     {"义齿附录": APPENDIX + "定制式义齿"}),
    ("software", "医疗器械生产质量管理规范独立软件检查指导原则", "独立软件",
     "20_指导原则/其他指导原则/医疗器械生产质量管理规范独立软件检查指导原则（2026）.md",
     {"独立软件附录": APPENDIX + "独立软件"}),
]
LEVELS = {"***": "关键", "**": "主要", "*": "一般"}

_SEP = re.compile(r"(?:<br\s*/?>|[\s;；,，、])+")
_REF_TOKEN = re.compile(
    r"(?:《(?P<law>[^《》]+)》)?(?:\s|<br\s*/?>)*(?:"                     # 可带「《规范》」「《无菌附录》」前缀，前缀后可能换行
    r"第(?P<a1>[零一二三四五六七八九十百零]+)条(?:至第(?P<a2>[零一二三四五六七八九十百零]+)条)?"   # 条号，可写区间
    r"|(?P<clause>\d+(?:\.\d+)+))"                                       # 附录的数字编号
)


def parse_refs(cell: str, targets: dict[str, str]) -> tuple[list[dict], list[str]]:
    """条款引用 → ([{law, articles, clauses}], 解析不了的片段)。

    不带前缀的条号、编号沿用同格内最近的法规；「《X附录》」按 targets 找附录，其余不带「附录」的一律指《规范》。
    """
    refs: dict[str, dict] = {}
    unparsed: list[str] = []
    law = None
    pos = 0
    for m in _REF_TOKEN.finditer(cell):
        gap = _SEP.sub("", cell[pos:m.start()])
        if gap:
            unparsed.append(gap)
        pos = m.end()
        if m.group("law"):
            name = m.group("law").strip()
            law = targets.get(name, None if "附录" in name else GMP)
        if law is None:
            unparsed.append(m.group(0))
            continue
        entry = refs.setdefault(law, {"law": law, "articles": [], "clauses": []})
        if m.group("a1"):
            first = cn_num_to_int(m.group("a1"))
            last = cn_num_to_int(m.group("a2") or m.group("a1"))
            entry["articles"] += [n for n in range(first, last + 1) if n not in entry["articles"]]
        elif m.group("clause") not in entry["clauses"]:
            entry["clauses"].append(m.group("clause"))
    rest = _SEP.sub("", cell[pos:])
    if rest:
        unparsed.append(rest)
    return list(refs.values()), unparsed


def parse_inspection_md(md_text: str, doc_id: str, name: str, scope: str, targets: dict[str, str],
                        chapter_titles: dict[str, str]) -> tuple[dict, list[str]]:
    """一份检查指导原则 → (文档信息 + items, 解析不了的引用清单)。"""
    parts = md_text.split("---", 2)
    meta = (yaml.safe_load(parts[1]) if md_text.startswith("---") and len(parts) >= 3 else {}) or {}
    lines = md_text.splitlines()
    header = next(i for i, l in enumerate(lines) if l.strip().startswith("|") and "风险等级" in l)
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines[header:] if l.strip().startswith("|")]
    problems: list[str] = []
    items: list[dict] = []
    chapter = ""
    for cells in rows[1:]:
        if len(cells) != len(rows[0]) or not cells[1].isdigit():
            continue
        chapter = re.sub(r"\s+", " ", re.sub(r"<br\s*/?>", " ", cells[0] or chapter)).strip()
        chapter = re.sub(r"^(第[一二三四五六七八九十]+章)(?=\S)", r"\1 ", chapter)   # 「第二章质量保证」→「第二章 质量保证」
        m = re.match(r"^(第[一二三四五六七八九十]+章)$", chapter)   # 只写了章号、没写标题的，用规范的章标题补全
        if m:
            chapter = chapter_titles.get(m.group(1), chapter)
        refs, unparsed = parse_refs(cells[5], targets)
        if unparsed:
            problems.append(f"{name} 第{cells[1]}项「{cells[2]}」: {' / '.join(unparsed)}（原文：{cells[5]}）")
        items.append({
            "no": int(cells[1]), "clause": cells[2], "chapter": chapter,
            "content": re.sub(r"<br\s*/?>", " ", cells[3]),
            "level": LEVELS[cells[4]], "refs": refs, "refs_raw": cells[5],
        })
    return {
        "id": doc_id, "name": name, "scope": scope,
        "doc_number": str(meta.get("文号发布号", "") or ""),
        "effective_date": str(meta.get("施行日期", "") or ""),
        "source": str(meta.get("官方链接", "") or ""),
        "items": items,
    }, problems


def main() -> None:
    kb = Path(sys.argv[1]).expanduser() if len(sys.argv) == 2 else KB_DEFAULT
    titles = {c["title"].split(" ")[0]: c["title"] for c in chapter_ranges((kb / GMP_MD).read_text(encoding="utf-8"))}
    docs, problems = [], []
    for doc_id, name, scope, rel, targets in DOCS:
        doc, bad = parse_inspection_md((kb / rel).read_text(encoding="utf-8"), doc_id, name, scope, targets, titles)
        docs.append(doc)
        problems += bad
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generated_at": date.today().isoformat(), "docs": docs}, ensure_ascii=False, indent=1), encoding="utf-8")
    items = sum(len(d["items"]) for d in docs)
    print(f"导出 {len(docs)} 份检查指导原则、{items} 个检查项 → {OUT}")
    print(f"带条款引用的检查项 {sum(1 for d in docs for it in d['items'] if it['refs'])}/{items}")
    for p in problems:
        print("  解析不了:", p)
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [x] **Step 4: 确认测试通过**

Run: `uv run pytest -q`
Expected: 32 passed。

- [x] **Step 5: 生成数据并处理解析不了的引用**

Run: `uv run python scripts/build_inspection.py`
Expected: 「导出 6 份检查指导原则、1241 个检查项」（200 + 216 + 220 + 212 + 190 + 203），带条款引用的接近全部。若列出「解析不了」的条目且退出码为 1：逐条看原文，按实际写法扩充 `_REF_TOKEN` 或 `parse_refs`（先在测试里加对应样例），直到脚本以 0 退出。
再用下面的命令核对数量与法规名：

```bash
uv run python -c "
import json
d = json.load(open('web/public/data/inspection.json'))
for x in d['docs']:
    laws = sorted({r['law'] for it in x['items'] for r in it['refs']})
    print(x['scope'], len(x['items']), x['doc_number'], x['effective_date'], laws)
"
```

Expected: 6 行；专项版各自引用《规范》和自己的附录；法规名与版本清单里的入库命名完全一致。

- [x] **Step 6: 提交**

```bash
git add scripts/build_inspection.py tests/test_build_inspection.py web/public/data/inspection.json
git commit -m "脚本：医疗器械 GMP 检查指导原则导出为静态数据（含条款引用）"
```

### Task B2: 检查指导原则页

**Files:**
- Modify: `web/src/main.js`、`web/src/App.vue`、`web/src/style.css`
- Create: `web/src/views/InspectView.vue`

- [x] **Step 1: 路由与导航**

`web/src/main.js`：加 `import InspectView from './views/InspectView.vue'`，在 `routes` 的知识图谱一行后面加 `{ path: '/inspect', name: 'inspect', component: InspectView },`。
`web/src/App.vue`：导航里知识图谱的 `<router-link>` 之后加 `<router-link to="/inspect">检查指导原则</router-link>`。

- [x] **Step 2: 新建 `web/src/views/InspectView.vue`**

```vue
<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { cnNum, loadData, shortName, useOpenLaw } from '../data'

const route = useRoute()
const openLaw = useOpenLaw()

const data = ref(null)
const error = ref('')
loadData('inspection').then(d => { data.value = d }).catch(e => { error.value = String(e.message || e) })

const LEVELS = ['关键', '主要', '一般']
const LEVEL_CLASS = { 关键: 'high', 主要: 'mid', 一般: 'low' }
const docId = ref('all')
const chapter = ref('')
const levels = ref([...LEVELS])
const keyword = ref('')

// 进入时按某法规的某一条筛选：?law=<法规ID>&article=<条号> 或 &clause=<编号>
const lawName = computed(() => laws.value.find(l => l.id === Number(route.query.law))?.name || '')
const article = computed(() => Number(route.query.article) || 0)
const clause = computed(() => String(route.query.clause || ''))
const matchesTarget = it => !lawName.value || it.refs.some(r => r.law === lawName.value
  && ((article.value && r.articles.includes(article.value)) || (clause.value && r.clauses.includes(clause.value))))

const scopedDocs = computed(() => (data.value?.docs || []).map(d => ({ ...d, items: d.items.filter(matchesTarget) })))
const docs = computed(() => scopedDocs.value.filter(d => docId.value === 'all' || d.id === docId.value))
const chapters = computed(() => [...new Set(docs.value.flatMap(d => d.items.map(it => it.chapter)))])
const items = computed(() => docs.value
  .flatMap(d => d.items.map(it => ({ ...it, scope: d.scope })))
  .filter(it => !chapter.value || it.chapter === chapter.value)
  .filter(it => levels.value.includes(it.level))
  .filter(it => !keyword.value || `${it.clause} ${it.content}`.includes(keyword.value)))

</script>

<template>
  <div>
    <div class="card" style="margin-bottom:16px;">
      <h1 class="serif" style="margin:0 0 6px; font-size:20px; letter-spacing:.08em;">医疗器械 GMP 检查指导原则（2026 版）</h1>
      <div class="muted">每个检查项对应哪条规范、哪条附录，风险等级多高。读 GMP 条文时点「检查项」就会跳到这里。</div>
      <template v-if="data">
        <div class="filters">
          <button v-for="d in [{ id: 'all', scope: '全部', items: scopedDocs.flatMap(x => x.items) }, ...scopedDocs]" :key="d.id"
                  :class="{ primary: docId === d.id }" @click="docId = d.id; chapter = ''">{{ d.scope }} {{ d.items.length }}</button>
        </div>
        <div class="filters">
          <select v-model="chapter">
            <option value="">全部章节</option>
            <option v-for="c in chapters" :key="c" :value="c">{{ c }}</option>
          </select>
          <label v-for="lv in LEVELS" :key="lv" class="check"><input v-model="levels" type="checkbox" :value="lv" /> {{ lv }}</label>
          <input v-model="keyword" placeholder="搜索条款号或检查内容" style="flex:1; min-width:180px;" />
        </div>
        <div v-if="lawName && (article || clause)" class="muted" style="margin-top:8px;">
          只看《{{ lawName }}》{{ clause || `第${cnNum(article)}条` }} 的检查项，<router-link to="/inspect">查看全部</router-link>
        </div>
      </template>
    </div>

    <div v-if="error" class="card error-box">{{ error }}</div>
    <div v-else-if="!data" class="card muted">加载中…</div>
    <table v-else class="data-table card">
      <thead>
        <tr><th>条款</th><th>范围</th><th>风险</th><th>章节</th><th>检查内容</th><th>对应条款</th></tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="`${it.scope}-${it.no}`">
          <td class="nowrap">{{ it.clause }}</td>
          <td class="nowrap">{{ it.scope }}</td>
          <td class="nowrap"><span class="level-badge" :class="LEVEL_CLASS[it.level]">{{ it.level }}</span></td>
          <td class="nowrap">{{ it.chapter }}</td>
          <td>{{ it.content }}</td>
          <td class="nowrap">
            <template v-for="r in it.refs" :key="r.law">
              <a v-for="n in r.articles" :key="`${r.law}-${n}`" class="ref" href="#" @click.prevent="openLaw(r.law, { article: n })">{{ shortName(r.law) }} 第{{ cnNum(n) }}条</a>
              <a v-for="c in r.clauses" :key="`${r.law}-${c}`" class="ref" href="#" @click.prevent="openLaw(r.law, { clause: c })">{{ shortName(r.law) }} {{ c }}</a>
            </template>
            <span v-if="!it.refs.length" class="muted">{{ it.refs_raw }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="data && !items.length" class="card muted">没有符合条件的检查项。</div>
  </div>
</template>
```

- [x] **Step 3: 样式**（追加到 `web/src/style.css` 末尾；并给 `.topbar` 加 `flex-wrap: wrap;`、`.topbar nav` 加 `flex-wrap: wrap;`，导航项多了会换行）

```css
/* 检查指导原则 / 标准地图 */
.filters { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 12px; }
.filters select, .filters input {
  font: inherit; font-size: 14px; padding: 6px 10px;
  border: 1px solid var(--line); border-radius: 8px; background: var(--paper); color: var(--ink);
}
.filters .check { font-size: 14px; color: var(--ink-2); }
.data-table.card { padding: 0; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td {
  border-bottom: 1px solid var(--line); padding: 8px 10px;
  font-size: 14px; text-align: left; vertical-align: top;
}
.data-table th { background: #faf8f2; color: var(--ink-2); font-weight: 600; white-space: nowrap; }
.data-table td.nowrap { white-space: nowrap; }
.data-table a.ref { display: block; color: var(--accent); text-decoration: none; font-size: 13px; }
.level-badge { display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 12px; }
.level-badge.high { background: #fdeeee; color: var(--bad); }
.level-badge.mid { background: #f6efdd; color: #7a6335; }
.level-badge.low { background: #eaf3ea; color: var(--ok); }
```

- [x] **Step 4: 构建并实测互链**

Run:

```bash
npm --prefix web run build 2>&1 | tail -2
GMP_ID=$(uv run python -c "from app.database import SessionLocal; from app.models import Law; print(SessionLocal().query(Law).filter_by(name='医疗器械生产质量管理规范').first().id)")
node scripts/cdp.mjs eval "http://localhost:4173/#/inspect" "document.querySelectorAll('a.ref').length"
node scripts/cdp.mjs eval "http://localhost:4173/#/inspect?law=$GMP_ID&article=3" "({ note: document.querySelector('.muted[style]')?.textContent.trim(), refs: document.querySelectorAll('a.ref').length })"
node scripts/cdp.mjs eval "http://localhost:4173/#/?law=$GMP_ID&article=3" "document.querySelectorAll('.link-chip').length"
node scripts/cdp.mjs shot "http://localhost:4173/#/inspect" /tmp/inspect.png --width 1300 --height 2200
```

Expected: 第一个数是一千多（全部检查项的条款链接）；第二个数明显变小，`note` 是「只看《医疗器械生产质量管理规范》第三条 的检查项，查看全部」；第三个数大于 0（阅读页 GMP 条款标题旁有「检查项 N」标签）。静态服务若已停，先按 Task A6 Step 5 的命令重新启动。用 Read 工具看 `/tmp/inspect.png`，排版正常。

- [x] **Step 4b: 实测点击跳转**

Run: `node scripts/cdp.mjs eval "http://localhost:4173/#/inspect?law=$GMP_ID&article=3" "new Promise(r => { document.querySelector('a.ref').click(); setTimeout(() => r({ hash: location.hash, scrollY: Math.round(scrollY), active: document.querySelector('#art-3 h2')?.textContent.trim() }), 2500) })"`

Expected: `hash` 是 `#/`（阅读页），`active` 是「第三条」，`scrollY` 大于 0（滚动到了该条）。

- [x] **Step 5: 提交并推送**

```bash
git add web/src/main.js web/src/App.vue web/src/style.css web/src/views/InspectView.vue
git commit -m "前端：检查指导原则页，按文档、章节、风险等级筛选并可跳转到 GMP 条款"
git push origin main
```

---

## 阶段 C：标准地图

**执行时机：** 标准调研的三份 JSON（器械管理类、器械生产类、药品）到齐后开始；Task C1 的 `standards.json` 要在 Task A8（试点解读）之前完成，解读里的「相关标准」依赖它。页面部分在阶段 B 之后做。

### Task C1: 标准数据整理成 `standards.json`

**背景：** 三份调研 JSON 的字段结构相同，合并成页面和文档的唯一数据源；法规名、章标题必须与入库的法规完全一致，否则页面上对不上号。

**Files:**
- Generate: `web/public/data/standards.json`
- Input（不入库）: `data/gmp-drafts/standards-device-mgmt.json`、`standards-device-prod.json`、`standards-pharma.json`

- [x] **Step 1: 合并**

Run:

```bash
uv run python - <<'EOF'
import json
from pathlib import Path

FIELDS = ["number", "name", "kind", "status", "effective_date", "replaces", "international", "themes", "gmp",
          "usage", "outputs", "access", "url", "note"]
src = Path("data/gmp-drafts")
by_number, standards, problems = {}, [], []
for name in ["standards-device-mgmt.json", "standards-device-prod.json", "standards-pharma.json"]:
    path = src / name
    if not path.exists():
        problems.append(f"缺文件 {name}")
        continue
    for s in json.loads(path.read_text(encoding="utf-8")):
        missing = [k for k in FIELDS if k not in s]
        if missing or not s.get("number") or not s.get("name"):
            problems.append(f"{name}: {s.get('number')} 缺字段 {missing}")
            continue
        if s["number"] in by_number:                      # 两份调研都收录了：映射取并集
            by_number[s["number"]]["gmp"] += [g for g in s["gmp"] if g not in by_number[s["number"]]["gmp"]]
            continue
        by_number[s["number"]] = {k: s[k] for k in FIELDS}
        standards.append(by_number[s["number"]])
laws = [
    {"name": "医疗器械生产质量管理规范", "short": "医疗器械 GMP（2025 年第 107 号）",
     "kb_path": "13_规范性文件/医疗器械生产质量管理规范.md"},
    {"name": "药品生产质量管理规范（2010年修订）", "short": "药品 GMP（2010 年修订）",
     "kb_path": "13_规范性文件/药品生产质量管理规范.md"},
]
data = {"generated_at": "2026-11-25", "laws": laws, "chapters": [], "standards": standards}
out = Path("web/public/data/standards.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(standards)} 项标准；{len(problems)} 个问题")
for p in problems:
    print("  ", p)
EOF
```

Expected: 「N 项标准；0 个问题」。有问题就回到对应调研结果里补字段。

- [x] **Step 2: 刷新「章 → 条款范围」**（Task C2 的脚本写好后执行）

Run: `uv run python scripts/build_standards_doc.py --refresh-chapters`
Expected: `chapters` 里出现器械 GMP 的 15 章和药品 GMP 的 14 章，每章带条号范围。

- [x] **Step 3: 核对法规名与章标题**

Run:

```bash
uv run python - <<'EOF'
import json
from app.database import SessionLocal
from app.models import Law

data = json.loads(open("web/public/data/standards.json", encoding="utf-8").read())
law_names = {l.name for l in SessionLocal().query(Law).all()}
titles = {(c["law"], c["title"]) for c in data["chapters"]}
bad = []
for s in data["standards"]:
    for g in s["gmp"]:
        if g["law"] not in law_names:
            bad.append((s["number"], "法规名对不上", g["law"]))
        for t in g["chapters"]:
            if (g["law"], t) not in titles:
                bad.append((s["number"], "章标题对不上", g["law"], t))
print(len(data["standards"]), "项标准，", len(data["chapters"]), "章；对不上的映射", len(bad), "处")
for b in bad[:30]:
    print("  ", b)
EOF
```

Expected: 「对不上的映射 0 处」。有就对回 `standards.json` 改法规名或章标题（改完重跑 Step 1 会覆盖，所以要么改调研 JSON 再合并，要么在 Step 1 之后只改 `standards.json`）。

### Task C2: 标准地图文档渲染 + 刷新章条范围

**Files:**
- Create: `scripts/build_standards_doc.py`
- Test: `tests/test_build_standards_doc.py`
- Generate: `docs/gmp-standards-map.md`

- [x] **Step 1: 写失败的测试** `tests/test_build_standards_doc.py`

```python
"""标准地图文档渲染：按章归并、按条款归并、未归入章节的部分。"""

from scripts.build_standards_doc import chapter_standards, render_doc

GMP = "医疗器械生产质量管理规范"
PHARMA = "药品生产质量管理规范（2010年修订）"


def _std(number, gmp):
    return {"number": number, "name": number + " 名称", "kind": "推荐性国家标准", "status": "现行",
            "effective_date": "2021-01-01", "replaces": [], "international": "", "themes": [], "gmp": gmp,
            "usage": "培训", "outputs": "培训记录", "access": "", "url": "", "note": ""}


DATA = {
    "generated_at": "2026-11-25",
    "laws": [{"name": GMP, "short": "医疗器械 GMP"}],
    "chapters": [
        {"law": GMP, "title": "第三章 机构与人员", "articles": [10, 11]},
        {"law": GMP, "title": "第四章 厂房与设施", "articles": [12]},
    ],
    "standards": [
        _std("GB/T 1-2020", [{"law": GMP, "chapters": ["第三章 机构与人员"], "articles": []}]),
        _std("GB/T 2-2020", [{"law": GMP, "chapters": [], "articles": [11]}]),
        _std("GB/T 3-2020", [{"law": PHARMA, "chapters": [], "articles": [5]}]),
    ],
}


def test_chapter_standards_matches_by_chapter_or_article():
    third = DATA["chapters"][0]
    assert [s["number"] for s in chapter_standards(DATA["standards"], GMP, third)] == ["GB/T 1-2020", "GB/T 2-2020"]
    assert chapter_standards(DATA["standards"], GMP, DATA["chapters"][1]) == []


def test_render_doc():
    doc = render_doc(DATA)
    assert "## 医疗器械 GMP" in doc
    assert "### 第三章 机构与人员（第10–11条，2 项标准）" in doc
    assert "| GB/T 1-2020 | GB/T 1-2020 名称 |" in doc
    assert "### 第四章 厂房与设施（第12条，0 项标准）" in doc and "无直接对应标准。" in doc
    tail = doc.split("## 未归入 GMP 章节的标准")[1]
    assert "GB/T 3-2020" in tail and "GB/T 1-2020" not in tail
```

- [x] **Step 2: 确认测试失败**

Run: `uv run pytest tests/test_build_standards_doc.py -q`
Expected: ERROR，`ModuleNotFoundError: No module named 'scripts.build_standards_doc'`。

- [x] **Step 3: 新建 `scripts/build_standards_doc.py`**

```python
"""由标准地图数据渲染文档，并从 GMP 源文件刷新「章 → 条款范围」。

web/public/data/standards.json 是标准地图页面和文档的唯一数据源。
--refresh-chapters 按法规总表里的 GMP 全文重算 chapters（章标题 + 条号范围）并写回 JSON。

用法:
  uv run python scripts/build_standards_doc.py [--refresh-chapters] [法规总表目录]
输出: docs/gmp-standards-map.md
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.importer.parsers import chapter_ranges

KB_DEFAULT = Path("/Volumes/APFS_3/法规总表")
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "public" / "data" / "standards.json"
OUT = ROOT / "docs" / "gmp-standards-map.md"
HEADERS = ["标准号", "名称", "类型", "状态", "实施日期", "代替", "对应国际标准", "用在哪一步", "产出记录", "获取渠道", "来源"]


def chapter_standards(standards: list[dict], law: str, chapter: dict) -> list[dict]:
    """映射到整章的，或映射到该章任一条款的标准。"""
    articles = set(chapter["articles"])
    return [s for s in standards if any(
        g["law"] == law and (chapter["title"] in g["chapters"] or articles.intersection(g["articles"]))
        for g in s["gmp"])]


def _cell(value) -> str:
    text = value if isinstance(value, str) else "、".join(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _row(values: list) -> str:
    return "| " + " | ".join(_cell(v) for v in values) + " |"


def _range(articles: list) -> str:
    if len(articles) == 1:
        return f"第{articles[0]}条"
    if articles[-1] - articles[0] == len(articles) - 1:      # 连续条号：第10–11条
        return f"第{articles[0]}–{articles[-1]}条"
    return f"第{articles[0]}条–第{articles[-1]}条"


def render_doc(data: dict) -> str:
    out = [
        "# GMP 国家标准地图", "",
        f"生成日期：{data.get('generated_at', '')}。数据源：`web/public/data/standards.json`，与系统内的「标准地图」页面同源。", "",
        "## 怎么用", "",
        "- 按 GMP 的章找标准：每章下面列出支撑该章要求的标准，以及它用在哪一步、产出什么记录。",
        "- 标准状态以官方渠道核实的结果为准；「即将实施」的要看清实施日期，提前完成切换。",
        "- 标准全文多数受版权保护：国家标准可在国家标准全文公开系统在线阅读或购买，行业标准需购买。", "",
    ]
    used = set()
    for law in data["laws"]:
        out += [f"## {law['short']}", "", f"法规全称：《{law['name']}》", ""]
        for ch in [c for c in data["chapters"] if c["law"] == law["name"]]:
            rows = chapter_standards(data["standards"], law["name"], ch)
            used.update(s["number"] for s in rows)
            out += [f"### {ch['title']}（{_range(ch['articles'])}，{len(rows)} 项标准）", ""]
            if not rows:
                out += ["无直接对应标准。", ""]
                continue
            out += ["| " + " | ".join(HEADERS) + " |", "|" + "---|" * len(HEADERS)]
            for s in rows:
                source = f"[链接]({s['url']})" if s["url"] else ""
                out.append(_row([s["number"], s["name"], s["kind"], s["status"], s["effective_date"], s["replaces"],
                                 s["international"], s["usage"], s["outputs"], s["access"], source]))
            out.append("")
    rest = [s for s in data["standards"] if s["number"] not in used]
    out += [f"## 未归入 GMP 章节的标准（{len(rest)} 项）", "",
            "服务于附录、跨章使用，或尚未映射到具体章节的标准。", ""]
    if rest:
        out += ["| " + " | ".join(HEADERS[:-1] + ["关联法规"]) + " |", "|" + "---|" * len(HEADERS)]
        for s in rest:
            related = "、".join(sorted({g["law"] for g in s["gmp"]}))
            out.append(_row([s["number"], s["name"], s["kind"], s["status"], s["effective_date"], s["replaces"],
                             s["international"], s["usage"], s["outputs"], s["access"], related]))
        out.append("")
    return "\n".join(out)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if "--refresh-chapters" in sys.argv:
        kb = KB_DEFAULT
        positional = [a for a in sys.argv[1:] if not a.startswith("--")]
        if positional:
            kb = Path(positional[0]).expanduser()
        data["chapters"] = [
            {"law": law["name"], **ch}
            for law in data["laws"]
            for ch in chapter_ranges((kb / law["kb_path"]).read_text(encoding="utf-8"))
        ]
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT.write_text(render_doc(data), encoding="utf-8")
    print(f"标准地图文档 → {OUT}（{len(data['standards'])} 项标准，{len(data['chapters'])} 章）")


if __name__ == "__main__":
    main()
```

- [x] **Step 4: 确认测试通过并生成文档**

Run: `uv run pytest -q && uv run python scripts/build_standards_doc.py --refresh-chapters`
Expected: 34 passed；输出「标准地图文档 → …/docs/gmp-standards-map.md（N 项标准，29 章）」（器械 15 章 + 药品 14 章）。打开文档抽查两章，表格列对齐、没有断行。

- [x] **Step 5: 提交**

```bash
git add scripts/build_standards_doc.py tests/test_build_standards_doc.py web/public/data/standards.json docs/gmp-standards-map.md
git commit -m "数据：GMP 相关标准地图（页面与文档同源）及文档渲染脚本"
```

### Task C3: 标准地图页

**Files:**
- Modify: `web/src/main.js`、`web/src/App.vue`、`web/src/style.css`
- Create: `web/src/views/StandardsView.vue`

- [x] **Step 1: 路由与导航**

`web/src/main.js`：加 `import StandardsView from './views/StandardsView.vue'`，在 `/inspect` 一行后面加 `{ path: '/standards', name: 'standards', component: StandardsView },`。
`web/src/App.vue`：导航里检查指导原则的 `<router-link>` 之后加 `<router-link to="/standards">标准地图</router-link>`。

- [x] **Step 2: 新建 `web/src/views/StandardsView.vue`**

```vue
<script setup>
import { computed, inject, ref } from 'vue'
import { useRoute } from 'vue-router'
import { cnNum, loadData, shortName, useOpenLaw } from '../data'

const route = useRoute()
const laws = inject('laws')
const openLaw = useOpenLaw()

const data = ref(null)
const error = ref('')
loadData('standards').then(d => { data.value = d }).catch(e => { error.value = String(e.message || e) })

const STATUS_CLASS = { 现行: 'low', 即将实施: 'mid', 已废止: 'high' }
const lawFilter = ref('')       // '' = 全部
const keyword = ref('')

// 进入时只列某法规某一条相关的标准：?law=<法规ID>&article=<条号> 或 &clause=<编号>
const lawName = computed(() => laws.value.find(l => l.id === Number(route.query.law))?.name || '')
const article = computed(() => Number(route.query.article) || 0)
const clause = computed(() => String(route.query.clause || ''))
const chapters = computed(() => data.value?.chapters || [])
const chapterArticles = (law, title) => chapters.value.find(c => c.law === law && c.title === title)?.articles || []

const matched = computed(() => (data.value?.standards || []).filter(s => {
  if (lawName.value) {
    const hit = s.gmp.some(g => g.law === lawName.value && (
      g.articles.includes(article.value) || g.articles.includes(clause.value)
      || g.chapters.some(t => article.value && chapterArticles(g.law, t).includes(article.value))))
    if (!hit) return false
  }
  return !keyword.value || `${s.number} ${s.name} ${s.themes.join(' ')} ${s.usage}`.includes(keyword.value)
}))

const scopeLaw = computed(() => lawName.value || lawFilter.value)
const rangeText = articles => (articles.length > 1 ? `第${articles[0]}–${articles[articles.length - 1]}条` : `第${articles[0]}条`)
// 分节：指定了法规就按它的章排列，没指定就合成一节
const sections = computed(() => {
  if (!scopeLaw.value) return [{ title: '全部标准', note: '', standards: matched.value }]
  const used = new Set()
  const out = chapters.value.filter(c => c.law === scopeLaw.value).map(ch => {
    const list = matched.value.filter(s => s.gmp.some(g => g.law === scopeLaw.value
      && (g.chapters.includes(ch.title) || g.articles.some(n => ch.articles.includes(n)))))
    list.forEach(s => used.add(s.number))
    return { title: ch.title, note: rangeText(ch.articles), standards: list }
  })
  const rest = matched.value.filter(s => !used.has(s.number))
  if (rest.length) out.push({ title: '其他相关标准', note: '服务于附录、跨章使用，或未映射到具体章节', standards: rest })
  return out
})

// 点章标题跳到该章第一条
function openChapter(law, title) {
  const first = chapterArticles(law, title)[0]
  if (first) openLaw(law, { article: first })
}
</script>

<template>
  <div>
    <div class="card" style="margin-bottom:16px;">
      <h1 class="serif" style="margin:0 0 6px; font-size:20px; letter-spacing:.08em;">GMP 标准地图</h1>
      <div class="muted">支撑 GMP 各章要求的国家标准、行业标准、计量规范：用在哪一步、产出什么记录、现行状态和替代关系。</div>
      <template v-if="data">
        <div class="filters">
          <select v-if="!lawName" v-model="lawFilter">
            <option value="">全部法规</option>
            <option v-for="l in data.laws" :key="l.name" :value="l.name">{{ l.short }}</option>
          </select>
          <input v-model="keyword" placeholder="搜索标准号、名称、主题或用途" style="flex:1; min-width:200px;" />
        </div>
        <div v-if="lawName" class="muted" style="margin-top:8px;">
          只看《{{ lawName }}》{{ clause || (article ? `第${cnNum(article)}条` : '') }} 相关的标准，<router-link to="/standards">查看全部</router-link>
        </div>
      </template>
    </div>

    <div v-if="error" class="card error-box">{{ error }}</div>
    <div v-else-if="!data" class="card muted">加载中…</div>
    <template v-else>
      <section v-for="sec in sections" :key="sec.title" class="card" style="margin-bottom:16px; padding:16px 22px;">
        <h2 class="serif" style="margin:0 0 10px; font-size:17px;">
          {{ sec.title }}
          <span v-if="sec.note" class="muted" style="font-size:13px; margin-left:10px;">{{ sec.note }} · {{ sec.standards.length }} 项</span>
        </h2>
        <div v-if="!sec.standards.length" class="muted">无直接对应标准。</div>
        <table v-else class="data-table">
          <thead><tr><th>标准</th><th>状态</th><th>用途</th><th>对应条款</th></tr></thead>
          <tbody>
            <tr v-for="s in sec.standards" :key="s.number">
              <td style="min-width:220px;">
                <a v-if="s.url" :href="s.url" target="_blank" rel="noopener" class="std-no">{{ s.number }}</a>
                <b v-else class="std-no">{{ s.number }}</b>
                <div>{{ s.name }}</div>
                <div class="muted">
                  {{ s.kind }}<template v-if="s.international"> · {{ s.international }}</template><template v-if="s.effective_date"> · {{ s.status }} {{ s.effective_date }}</template>
                </div>
                <div v-if="s.replaces.length" class="muted">代替：{{ s.replaces.join('、') }}</div>
              </td>
              <td class="nowrap">
                <span class="level-badge" :class="STATUS_CLASS[s.status] || 'mid'">{{ s.status }}</span>
                <div class="muted" style="margin-top:4px;">{{ s.access }}</div>
              </td>
              <td style="min-width:260px;">
                {{ s.usage }}
                <div v-if="s.outputs" class="muted">产出：{{ s.outputs }}</div>
                <div v-if="s.note" class="muted">提示：{{ s.note }}</div>
              </td>
              <td class="nowrap">
                <template v-for="g in s.gmp" :key="g.law">
                  <a v-for="c in g.chapters" :key="`${g.law}-${c}`" class="ref" href="#" @click.prevent="openChapter(g.law, c)">{{ shortName(g.law) }} {{ c }}</a>
                  <a v-for="n in g.articles" :key="`${g.law}-${n}`" class="ref" href="#"
                     @click.prevent="openLaw(g.law, typeof n === 'string' ? { clause: n } : { article: n })">{{ shortName(g.law) }} {{ typeof n === 'string' ? n : `第${cnNum(n)}条` }}</a>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
      <div v-if="!matched.length" class="card muted">没有符合条件的标准。</div>
    </template>
  </div>
</template>
```

- [x] **Step 3: 样式**（追加到 `web/src/style.css` 末尾）

```css
.std-no { font-weight: 600; color: var(--ink); text-decoration: none; }
.data-table a.std-no:hover { color: var(--accent); }
```

- [x] **Step 4: 构建并实测**

Run:

```bash
npm --prefix web run build 2>&1 | tail -2
GMP_ID=$(uv run python -c "from app.database import SessionLocal; from app.models import Law; print(SessionLocal().query(Law).filter_by(name='医疗器械生产质量管理规范').first().id)")
node scripts/cdp.mjs eval "http://localhost:4173/#/standards" "({ sections: document.querySelectorAll('section').length, rows: document.querySelectorAll('tbody tr').length })"
node scripts/cdp.mjs eval "http://localhost:4173/#/standards?law=$GMP_ID&article=7" "({ note: [...document.querySelectorAll('.muted')].map(x => x.textContent.trim()).find(t => t.startsWith('只看')), rows: document.querySelectorAll('tbody tr').length })"
node scripts/cdp.mjs eval "http://localhost:4173/#/?law=$GMP_ID&article=7" "[...document.querySelectorAll('#art-7 .link-chip')].map(x => x.textContent.trim())"
node scripts/cdp.mjs eval "http://localhost:4173/#/standards?law=$GMP_ID&article=7" "new Promise(r => { document.querySelector('td a.ref').click(); setTimeout(() => r({ hash: location.hash, active: document.querySelector('#art-7 h2')?.textContent.trim() }), 2500) })"
node scripts/cdp.mjs shot "http://localhost:4173/#/standards" /tmp/standards.png --width 1300 --height 2200
```

Expected: 全部页面有若干节、行数等于标准数；按第三条（示例用第 7 条）筛选后 `note` 是「只看《医疗器械生产质量管理规范》第七条 相关的标准，查看全部」且行数变少；阅读页第七条标题旁的标签里有「相关标准 N」；点击条款链接后回到阅读页 `#/`、`active` 是「第七条」。用 Read 工具看 `/tmp/standards.png`。

- [x] **Step 5: 提交并推送**

```bash
git add web/src/main.js web/src/App.vue web/src/style.css web/src/views/StandardsView.vue
git commit -m "前端：标准地图页，按 GMP 章节浏览标准并可跳转到条款"
git push origin main
```

### Task C4: 更新法规总表的标准卡，放入标准地图文档

> 实际执行：脚本为 `data/gmp-drafts/_update_cards.py`（先预览再 `--apply`）。与下面 Step 2 的差别：状态比较按语义归一（「现行有效」与「现行」不算差异），只有真过时的才改；同时更正施行日期；文件名对整个「标准号 名称」做斜杠替换；年份取标准号里的公布年份。实际结果：新建 143 张（GB25–GB38、S32–S118、YY01–YY40、Z10–Z11），更正状态 2 张、施行日期 4 张，总表 CSV 追加 143 行。

**背景：** 法规总表里已有 62 张标准卡，调研发现有的状态过时；还有一批 GMP 强相关的标准没有卡。卡片由 `standards.json` 生成，已有的卡只改状态；法规总表不受 git 管理，改动前备份。总表 CSV（`/Volumes/APFS_3/法规总表.csv`，20 列）同步追加新卡的行。

**Files**（均在仓库外）:
- Modify/Create: `/Volumes/APFS_3/法规总表/14_标准_国标行标/*.md`
- Create: `/Volumes/APFS_3/法规总表/14_标准_国标行标/GMP 标准地图.md`
- Modify: `/Volumes/APFS_3/法规总表.csv`、`/Volumes/APFS_3/法规总表/00_管理/国标缺口清单.md`
- Backup to: `data/source-backup-20261125-gmp/`

- [x] **Step 1: 备份会被改到的文件**

Run: `mkdir -p data/source-backup-20261125-gmp/14_标准_国标行标 && cp -p /Volumes/APFS_3/法规总表/14_标准_国标行标/*.md data/source-backup-20261125-gmp/14_标准_国标行标/ && cp -p /Volumes/APFS_3/法规总表.csv /Volumes/APFS_3/法规总表/00_管理/国标缺口清单.md data/source-backup-20261125-gmp/`

- [x] **Step 2: 由 `standards.json` 生成缺失的卡、更正过时的状态**

```bash
uv run python - <<'EOF'
import csv, json, re
from pathlib import Path

KB = Path("/Volumes/APFS_3/法规总表")
CARDS = KB / "14_标准_国标行标"
data = json.loads(Path("web/public/data/standards.json").read_text(encoding="utf-8"))
doc = Path("docs/gmp-standards-map.md").read_text(encoding="utf-8")

# 现有卡：标准号 → (路径, YAML 文本)
cards = {}
for p in sorted(CARDS.glob("*.md")):
    text = p.read_text(encoding="utf-8")
    head = text.split("---", 2)[1] if text.startswith("---") else ""
    m = re.search(r"^文号发布号:\s*(\S+)", head, re.M)
    if m:
        cards[m.group(1)] = (p, head)

def next_id(prefix):
    used = [int(m.group(1)) for (p, head) in cards.values() for m in [re.search(rf"^编号:\s*{prefix}(\d+)\s*$", head, re.M)] if m]
    n = max(used, default=0) + 1
    return f"{prefix}{n:02d}"

LEVEL = {"强制性国家标准": "国家标准（强制性）", "推荐性国家标准": "国家标准（推荐性）",
         "指导性技术文件": "国家标准（指导性技术文件）", "行业标准": "行业标准"}
GMP = "医疗器械生产质量管理规范"
short = lambda law: law.replace(GMP, "《医疗器械生产质量管理规范》")

created, fixed = [], []
for s in data["standards"]:
    number = re.sub(r"[ /]", "_", s["number"])
    if s["number"] in cards:
        p, head = cards[s["number"]]
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^状态:\s*(.+)$", head, re.M)
        if m and m.group(1).strip() != s["status"] and s["kind"] in LEVEL:
            p.write_text(text.replace(m.group(0), f"状态: {s['status']}", 1), encoding="utf-8")
            fixed.append((s["number"], m.group(1).strip(), s["status"]))
        continue
    if s["kind"] not in LEVEL:          # 药典通则、工程建设标准、计量规范不是国标行标卡的范畴
        continue
    prefix = "Z" if s["kind"] == "指导性技术文件" else ("GB" if "强制性" in s["kind"] else "S")
    card_id = next_id(prefix)
    related = "\n".join(f"- 支撑：{short(g['law'])}{' ' + '、'.join(g['chapters']) if g['chapters'] else ''}"
                       f"{'（' + '、'.join('第%s条' % n for n in g['articles']) + '）' if g['articles'] else ''}"
                       for g in s["gmp"]) or "- 与 GMP 的对应关系待补充"
    card = f"""---
编号: {card_id}
名称: {s['name']}
文号发布号: {s['number']}
效力层级: {LEVEL[s['kind']]}
领域: 产品质量
发布机关: 
年份: {s['effective_date'][:4]}
公布日期: 
施行日期: {s['effective_date']}
状态: {s['status']}
优先级: P2
场景标签: 生产、标准
官方链接: {s['url']}
全文状态: 信息卡（暂不提供在线预览）
来源说明: 由 GMP 标准地图整理生成（数据源 law-study/web/public/data/standards.json），状态经官方渠道核实
核验日期: 2026-11-25
---

# {s['name']}（{s['number']}）

> **一句话要点**：{s['usage']}

## 标准信息卡

| 项目 | 内容 |
|---|---|
| 标准号 | {s['number']} |
| 中文名称 | {s['name']} |
| 属性 | {s['kind']} |
| 实施日期 | {s['effective_date']} |
| 标准状态 | {s['status']} |
| 对应国际标准 | {s['international'] or '未标注'} |

## 替代关系

- {'代替：' + '、'.join(s['replaces']) if s['replaces'] else '未检索到被代替的标准'}

## 与 GMP 的关系

{related}

- 用在哪一步：{s['usage']}
- 产出记录：{s['outputs'] or '见标准原文'}
- 获取渠道：{s['access'] or '见官方链接'}
"""
    path = CARDS / f"{number} {s['name']}.md"
    path.write_text(card, encoding="utf-8")
    cards[s["number"]] = (path, card.split("---", 2)[1])
    created.append((card_id, s["number"], path.name))

# 标准地图文档的副本
(CARDS / "GMP 标准地图.md").write_text(
    "---\n编号: MAP01\n名称: GMP 标准地图\n效力层级: 学习资料\n领域: 产品质量\n状态: 现行有效\n优先级: P1\n场景标签: 生产、标准\n"
    "来源说明: 由 law-study 的 web/public/data/standards.json 渲染，页面与文档同源\n核验日期: 2026-11-25\n---\n\n" + doc,
    encoding="utf-8")
print(f"新建标准卡 {len(created)} 张；更正状态 {len(fixed)} 张")
for x in created: print("  新建", x)
for x in fixed: print("  更正", x)

# 总表 CSV 追加新卡的行（20 列，与表头一致）
csv_path = KB.parent / "法规总表.csv"
with csv_path.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))
header = rows[0]
known = {r[2] for r in rows[1:] if len(r) > 2}
with csv_path.open("a", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    for card_id, number, fname in created:
        if number in known:
            continue
        s = next(x for x in data["standards"] if x["number"] == number)
        row = [""] * len(header)
        for col, value in {"编号": card_id, "名称": s["name"], "文号/发布号": number, "效力层级": LEVEL[s["kind"]],
                           "领域": "产品质量", "施行日期": s["effective_date"], "状态": s["status"],
                           "一句话要点": s["usage"], "场景标签": "生产、标准", "本地全文": f"14_标准_国标行标/{fname}",
                           "官方链接": s["url"], "核验状态": "已核验（2026-11-25）", "适用范围/摘要": s["usage"],
                           "获取渠道": s["access"], "全文可得性": "信息卡"}.items():
            row[header.index(col)] = value
        w.writerow(row)
print("总表 CSV 已追加")
EOF
```

Expected: 「新建标准卡 N 张；更正状态 M 张」并逐张列出；用 Read 工具抽查 2 张新卡的格式与现有卡一致。`发布机关`、`公布日期` 两项生成卡里是空的，在汇报里说明，由用户决定是否补。

- [x] **Step 3: 在管理记录里登记**

在 `/Volumes/APFS_3/法规总表/00_管理/国标缺口清单.md` 末尾追加一节「## 落地记录（GMP 标准地图，2026-11-25）」，列出新卡的编号与标准号、更正状态的卡（原状态 → 新状态）、标准地图文档的路径。

- [x] **Step 4: 提交**（仓库内无改动，不产生提交）

### Task C5: 收尾——README、完整验证、推送

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 README**

功能表加两行（检查指导原则、标准地图）；「静态快照只读模式」一段补上 `web/public/data/` 两个静态数据文件及生成命令；测试数改成当前数量；「导入格式」补一句 GMP 附录按数字编号切条。

- [ ] **Step 2: 完整验证**

Run:

```bash
uv run pytest -q
npm --prefix web run build 2>&1 | tail -1
grep -lE '/Users/|/Volumes/|Abel|先健|走进' web/public/api-snapshot/*.json web/public/data/*.json docs/gmp-*.md
```

Expected: 全部 passed；`✓ built`；第三条命令无输出。
动态模式实测：`./run.sh` 起服务后，用 `node scripts/cdp.mjs eval "http://127.0.0.1:8790/#/inspect" "…"` 和 `/standards` 各跑一次，结果与静态模式一致（服务启动后记得停掉）。

- [ ] **Step 3: 提交并推送，核对线上**

```bash
git add README.md
git commit -m "文档：检查指导原则与标准地图的使用说明"
git push origin main
gh run watch $(gh run list --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status
node scripts/cdp.mjs eval "https://abelwangyabo.github.io/law-study/#/standards" "({ rows: document.querySelectorAll('tbody tr').length, banner: !!document.querySelector('.snapshot-banner') })"
node scripts/cdp.mjs eval "https://abelwangyabo.github.io/law-study/#/inspect" "document.querySelectorAll('a.ref').length"
```

Expected: Pages 部署 success；线上两个页面都有数据，快照横幅显示。

---

## 附录 A：撰写规则（原样交给每个解读代理）

### A.1 通用规则

1. **忠于条文**：解读对象是条文原文。主体、条件、时限、数字一律以条文为准；条文之外的事实（新旧版本差异、检查要点、标准、案例）只能来自下面列出的素材或本次检索确认的来源，否则不写。
2. **读者**：血管介入支架类医疗器械生产企业的产品经理（注册人角色；产品含植入性器械、无菌器械、含软件的器械），负责合规工作。一律用泛称（企业、注册人、产品经理、经销商、医院），不得出现任何真实公司名、产品名、人名。
3. **形式**：纯 markdown，中文引号，段落之间空一行，不写 HTML，不用代码围栏；直接给内容，不出现「作为 AI」「根据检索」这类措辞。
4. **文件**：每条两份，`data/readings-drafts/law-<法规ID>/a{条款ID}-{interpret|scenario}.md`，条款 ID 不足 4 位左边补 0。
5. **篇幅**：与条文信息量匹配。GMP 条文比法律长，解读一般 200–600 字，场景分析一般 300–900 字。
6. **工具**：工具调用串行；每 3–5 个文件合并成一次写入（一条 Bash 里用带引号的 heredoc）。补充检索不超过 4 次、间隔 2 秒；需要用浏览器打开网页时用 `node scripts/cdp.mjs text "<url>"`（CDP 连接本机 Chrome），不要用 Playwright、无头 Chrome。
7. **参考**：用到了条文之外的联网信息时，文件末尾加 `## 参考`，逐条写「来源名称：URL」。

### A.2 模板（二级标题，顺序固定；标「有则写」的没有内容就不写）

**器械类**（器械 GMP 正文与五个附录）

| 文件 | 小节 |
|---|---|
| `a…-interpret.md` | `## 本条要点`、`## 关键角色与义务`、`## 白话解读`、`## 新旧对照`（仅有旧版的文件写）、`## 记忆锚点`、`## 参考`（有则写） |
| `a…-scenario.md` | `## 落地场景`、`## 对产品经理意味着什么`、`## 现场检查怎么查`、`## 相关标准`、`## 风险提示`、`## 参考`（有则写） |

**药品类**（药品 GMP 正文与附录）

| 文件 | 小节 |
|---|---|
| `a…-interpret.md` | 同器械类 |
| `a…-scenario.md` | `## 落地场景`、`## 与器械 GMP 的对照`、`## 对产品经理意味着什么`、`## 相关标准`、`## 风险提示`、`## 参考`（有则写） |

各小节的写法：

- **本条要点 / 关键角色与义务 / 白话解读 / 记忆锚点**：与现有 9 部法规的解读一致——要点一两句；角色与义务用表格（主体 | 义务/责任）；白话解读点出限定词和易错处；记忆锚点按条文行文串联关键词、并列项口诀、与相邻条文对比。
- **新旧对照**：写明「沿用 2014 年版第X条」「改写自 2014 年版第X条，变化是…」「新增」「由 2014 年版第X条、第Y条合并」。只按简报里的新旧对照表写，不自行推断。附录本身版本没变的，不写此节。
- **现场检查怎么查**：列出该条对应的检查项——条款号、风险等级（关键/主要/一般）、一句话检查内容；通用版和专项版都覆盖时注明「通用版 + 植入性专项」等；没有对应检查项的写「现行检查指导原则未对本条单列检查项」。
- **相关标准**：只列映射到该条或该章的标准——标准号、名称、用在哪一步、产出什么记录；没有的写「暂无直接对应标准」。标准号、状态以素材为准。
- **与器械 GMP 的对照**：写「对应《医疗器械生产质量管理规范》第X条」，并说清异同；器械 GMP 没有对应要求的写「器械 GMP 无直接对应要求，可借鉴的是…」。
- **落地场景**（药品类）：先用一两句写药品场景，再写器械企业可以迁移的做法。
- **风险提示**：结合检查、飞检中的典型缺陷（只用简报里核实过的真实案例，当事人用泛称）和法规后果；罚款、处罚条款必须有来源。

### A.3 每批交给代理的素材

| 素材 | 路径 |
|---|---|
| 条文原文 | `data/readings-drafts/law-<法规ID>-articles.md` |
| 调研简报（新旧对照表、检查动态、易错点） | `data/gmp-drafts/brief-device-gmp.md`、`brief-pharma-gmp.md` |
| 每条对应的检查项（器械类） | `data/gmp-drafts/inspection-by-article.md` |
| 标准 | `web/public/data/standards.json`（按 `gmp` 字段里的条号、章标题找） |
| 条款 ID 范围 | 在任务里直接给出 |

## 附录 B：执行顺序与并发

```
A0 → A1 → A2                         解析器与工具
阶段 0 调研（与上面并行，最多 4 个代理）
B1                                   检查项数据（A7 要用）
A3 → A4（版本清单经用户确认后）→ A5 → A6
C1 → C2                              标准数据（A8 要用）
A7 → A8 → A9 → A10（推送）            解读
B2（推送）→ C3（推送）→ C4 → C5（推送）  页面与知识库
```

同时运行的子代理不超过 4 个；被限流中断的代理用 SendMessage 恢复。阶段 1 的解读量约 2000 份，按器械 GMP 正文 → 器械附录 → 药品 GMP 正文 → 药品附录的顺序分批，每批 15–20 条。

## 附录 C：验收清单

- [ ] 自动化：`uv run pytest -q` 全部通过（预计 34 例）。
- [ ] 内容：每部现行版法规与源文件逐条逐段一字不差；每条现行版条款恰好一份解读和一份场景分析；旧版解读数为 0；原有 9 部的 724 条解读映射不变。
- [ ] 解读：`_validate_gmp.py` 0 问题；每部法规抽读 2 份；敏感信息扫描无命中。
- [ ] 版本：`docs/gmp-versions.md` 里每个文件都有官方来源，状态经用户确认。
- [ ] 检查指导原则：`inspection.json` 6 份文档、1241 个检查项；解析不了的引用为 0；页面筛选、搜索、跳转实测通过。
- [ ] 标准地图：`standards.json` 的法规名、章标题与库内一致（对不上的映射 0 处）；`docs/gmp-standards-map.md` 由脚本渲染；页面实测通过；法规总表标准卡已更新并备份。
- [ ] 界面：静态模式（`python3 -m http.server`）和动态模式（`./run.sh`）各测一遍；法规选择器三组；历史版本在快照模式下没有解读按钮。
- [ ] 发布：三次推送的 Pages 部署均成功，线上两个新页面有数据。
