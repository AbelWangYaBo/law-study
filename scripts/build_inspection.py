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
