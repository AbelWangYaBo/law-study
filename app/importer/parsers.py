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


def parse_md(md_text: str) -> dict:
    """解析法规总表 md：YAML 元数据 + 「第X条」切条（没有「第X条」的按数字编号切条），空行分段。"""
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
