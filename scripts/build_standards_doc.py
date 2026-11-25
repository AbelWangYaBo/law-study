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
        positional = [a for a in sys.argv[1:] if not a.startswith("--")]
        kb = Path(positional[0]).expanduser() if positional else KB_DEFAULT
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
