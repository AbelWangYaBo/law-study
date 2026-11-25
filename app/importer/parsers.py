"""法规文件解析：HTML（UDI 展示格式）与 MD（法规总表格式）。

统一输出：{name, doc_number, authority, level, effective_date, articles: [(order_no, label, [段落])]}
"""

import re
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

_CN_DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CN_UNITS = {"十": 10, "百": 100, "千": 1000}
_ARTICLE_LABEL_RE = re.compile(r"^第([零一二三四五六七八九十百千]+)条$")


def cn_num_to_int(cn: str) -> int:
    """中文数字转整数（支持到千位，如 六十五 → 65，一百零一 → 101）。"""
    total, num = 0, 0
    for ch in cn:
        if ch in _CN_DIGITS:
            num = _CN_DIGITS[ch]
        elif ch in _CN_UNITS:
            unit = _CN_UNITS[ch]
            total += (num or 1) * unit
            num = 0
    return total + num


def parse_article_label(label: str) -> int | None:
    """「第一条」→ 1；不合法返回 None。"""
    m = _ARTICLE_LABEL_RE.match(label.strip())
    return cn_num_to_int(m.group(1)) if m else None


def parse_html(html: str) -> dict:
    """解析 UDI 展示格式 HTML：section/h2 为条，p 为段落。"""
    soup = BeautifulSoup(html, "html.parser")
    name = soup.find("h1").get_text(strip=True) if soup.find("h1") else soup.title.get_text(strip=True)
    articles = []
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if not h2:
            continue
        label = h2.get_text(strip=True)
        order_no = parse_article_label(label)
        paragraphs = [p.get_text() for p in section.find_all("p") if p.get_text(strip=True)]
        if order_no is not None and paragraphs:
            articles.append((order_no, label, paragraphs))
    return {"name": name, "doc_number": "", "authority": "", "level": "规范性文件", "effective_date": "", "articles": articles}


_MD_ARTICLE_RE = re.compile(r"^第([零一二三四五六七八九十百千]+)条")
# 章/节/部分标题：可带 markdown 强调符（**…** / *…*），标题里没有句读，长度有限
_MD_HEADING_RE = re.compile(r"^(?:\*\*|__|\*|_)?第[零一二三四五六七八九十百千]+[章节部分][^。；，：？！]{0,40}?(?:\*\*|__|\*|_)?$")
# 没有「第X条」的文件（如器械 GMP 附录）按数字编号切条：二级编号 1.1，三级编号 2.1.1
_MD_CLAUSE_RE = re.compile(r"^(\d+\.\d+)(?![\d.])\s*(.*)$")
_MD_SUBCLAUSE_RE = re.compile(r"^(\d+\.\d+\.\d+)(?![\d.])\s*(.*)$")


def _next_line(lines: list[str], i: int) -> str:
    """第 i 行之后第一个非空行（去掉 markdown 强调符）。"""
    return next((x.strip().lstrip("*") for x in lines[i + 1:] if x.strip()), "")


def _chapter_label(heading: str) -> str:
    """章标题 → 条款名：「第一章  范  围」「**第一章 总 则**」→「第一章 范围」。"""
    m = re.match(r"^(第[零一二三四五六七八九十百千]+[章部分])[ 　]*(.*)$", heading.strip().strip("*").strip())
    title = re.sub(r"\s+", "", m.group(2))
    return m.group(1) + (f" {title}" if title else "")


def chapter_ranges(md_text: str) -> list[dict]:
    """「章标题 → 该章的条号列表」。标题规范成「第三章 机构与人员」（去掉排版空格），没有条目的章不输出。"""
    ranges: list[dict] = []
    articles: list[int] = []
    for raw in md_text.splitlines():
        s = raw.strip().strip("*").strip()
        if re.match(r"^第[零一二三四五六七八九十百千]+章", s) and not re.search(r"[。；，：？！]", s):
            articles = []
            ranges.append({"title": _chapter_label(s), "articles": articles})
            continue
        a = _MD_ARTICLE_RE.match(s)
        if a and ranges:
            articles.append(cn_num_to_int(a.group(1)))
    return [r for r in ranges if r["articles"]]


def parse_md(md_text: str) -> dict:
    """解析法规总表 md：YAML 元数据 + 「第X条」切条（没有的按数字编号或按章切分），空行分段。

    第一条之前、章标题之后的无条号内容按章各成一条，条号为负数，排在正式条文之前。
    """
    meta = {}
    body = md_text
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            body = parts[2]

    name = str(meta.get("名称", "")).strip()
    doc_number = str(meta.get("文号发布号", "") or "").strip()
    authority = str(meta.get("发布机关", "") or "").strip()
    level = str(meta.get("效力层级", "") or "").strip()
    effective_date = str(meta.get("施行日期", "") or "").strip()

    lines = body.splitlines()
    stripped_lines = [line.strip() for line in lines]
    n_articles = sum(bool(_MD_ARTICLE_RE.match(s)) for s in stripped_lines)
    n_clauses = sum(bool(_MD_SUBCLAUSE_RE.match(s) or _MD_CLAUSE_RE.match(s)) for s in stripped_lines)
    # 没有「第X条」的文件按数字编号切条
    clause_mode = n_articles == 0 and n_clauses > 0

    articles: list[tuple[int, str, list[str]]] = []
    current: tuple[int, str, list[str]] | None = None
    started = False            # 是否已出现「第X条」
    preamble = 0               # 第一条之前、章标题之后的无条号内容按章成条，共有几条
    pending_chapter = ""       # 第一条之前最近见到的章标题
    for i, stripped in enumerate(stripped_lines):
        if not stripped:
            continue
        m = None
        if clause_mode:
            m = _MD_SUBCLAUSE_RE.match(stripped)
            if not m:
                m = _MD_CLAUSE_RE.match(stripped)
                # 二级编号：后面紧跟同组的三级编号时只是小节标题（如「2.1 人员」）
                if m and _next_line(lines, i).startswith(m.group(1) + "."):
                    continue
        elif not clause_mode:
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
                started = True
            continue
        if _MD_HEADING_RE.match(stripped):
            # 第一条之前、章标题之后的无条号内容按这一章成条（如原料药附录前三章、取样附录）
            if not started and re.match(r"^(?:\*\*|__|\*|_)?第[零一二三四五六七八九十百千]+[章部分]", stripped):
                if current:
                    articles.append(current)
                    current = None
                pending_chapter = _chapter_label(stripped)
            continue  # 章/节/部分标题不入条款
        if stripped.startswith(("#", ">", "**目录")):
            continue  # 标题、引用块不入条款
        if current:
            current[2].append(stripped)
        elif pending_chapter:
            current = (0, pending_chapter, [stripped])
            preamble += 1
    if current:
        articles.append(current)
    # 按章成条的无条号内容排在第一条之前：条号用负数，不与正式条号冲突
    for k in range(preamble):
        _, label, paras = articles[k]
        articles[k] = (k - preamble, label, paras)

    if not name:
        h1 = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        name = h1.group(1).strip() if h1 else Path("未命名法规").stem

    return {
        "name": name,
        "doc_number": doc_number,
        "authority": authority,
        "level": level,
        "effective_date": effective_date,
        "articles": [a for a in articles if a[2]],
    }


def parse_file(path: str | Path) -> dict:
    """按扩展名选择解析器。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".html", ".htm"):
        return parse_html(text)
    return parse_md(text)
