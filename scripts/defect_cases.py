"""缺陷测试路径与 case（供用户确认缺陷存在 / 明确不属于使用场景）。

用法: uv run python scripts/defect_cases.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.importer.parsers import parse_md
from app.services.term_extractor import extract_terms
from app.services.tokenizer import tokenize

UDI_HTML = Path("/Volumes/APFS_2/abel/走进先健/医疗器械唯一标识系统规则.html")

ARTICLE_7 = (
    "医疗器械唯一标识包括产品标识和生产标识。产品标识为识别注册人/备案人、医疗器械型号规格和包装的唯一代码；"
    "生产标识由医疗器械生产过程相关信息的代码组成，根据监管和实际应用需求，可包含医疗器械序列号、生产批号、"
    "生产日期、失效日期等。"
)


def case1() -> None:
    """缺陷1：非「X，是指…」句式的核心术语抽不到（第七条 产品标识/生产标识）。"""
    terms = [t["name"] for t in extract_terms([ARTICLE_7])]
    print(f"[case1] 第七条抽取结果: {terms}")
    print("        → 「产品标识」「生产标识」未被抽取：它们是「X为…」「由…组成」句式，v1 规则只覆盖「，是指」")
    print()


def case2() -> None:
    """缺陷2：jieba 兜底粒度——未入术语表的短语被切成多块，拼句变碎。"""
    tokens = tokenize("根据《医疗器械监督管理条例》，制定本规则。", {})
    print(f"[case2] 无词典时「医疗器械监督管理条例」分词: {[t['t'] for t in tokens if '器械' in t['t'] or '条例' in t['t']]}")
    print("        → 该法规名被切成 2 块（医疗器械/管理条例），拼句时是 2 个词块而非整词")
    print()


def case3() -> None:
    """缺陷3：MD 导入时「第X条 」前缀剥离为条名（label），首段不含条号。"""
    md = "第一条 为了测试，制定本法。"
    parsed = parse_md(md)
    print(f"[case3] MD「{md}」→ 条名={parsed['articles'][0][1]!r}, 首段={parsed['articles'][0][2][0]!r}")
    print("        → 条号从段落文本移入 label（与 HTML 的 h2/p 结构对齐），段落正文不含「第一条」字样")
    print()


def case4() -> None:
    """缺陷4：UDI 文内无英文缩写、无简称句式，abbreviation/short_name 通路在本文无命中。"""
    from bs4 import BeautifulSoup

    html = UDI_HTML.read_text(encoding="utf-8")
    paras = [p.get_text() for s in BeautifulSoup(html, "html.parser").find_all("section")
             for p in s.find_all("p") if p.get_text(strip=True)]
    types = {t["term_type"] for t in extract_terms(paras)}
    print(f"[case4] UDI 全文抽取到的术语类型: {types}")
    print("        → 只有 definition；简称/缩写规则已实现但本文无对应句式（保密法「以下简称保密」可命中）")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("缺陷测试 case（参数内嵌，供确认）")
    print("=" * 60)
    case1()
    case2()
    case3()
    case4()
