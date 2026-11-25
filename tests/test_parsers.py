"""解析器测试：HTML（UDI）与 MD（法规总表）格式。"""

import re
from pathlib import Path

import pytest

from app.importer.parsers import cn_num_to_int, parse_article_label, parse_html, parse_md

UDI_HTML = Path(__file__).resolve().parent / "fixtures" / "医疗器械唯一标识系统规则.html"

# 内嵌法规总表 md 样例（结构同 保密法.md）
MD_SAMPLE = """---
编号: L10
名称: 测试法
文号发布号: 主席令第1号
效力层级: 法律
发布机关: 全国人大常委会
施行日期: 2024-05-01
---

# 测试法

**目录**

**第一章 总 则**

第一条 为了测试，制定本法。

第二条 测试条款。

第二段同条另一段。

**第二章 附 则**

第十一条 本法自2024年5月1日起施行。
"""


def test_cn_num_to_int():
    assert cn_num_to_int("一") == 1
    assert cn_num_to_int("十八") == 18
    assert cn_num_to_int("六十五") == 65
    assert cn_num_to_int("一百零一") == 101
    assert parse_article_label("第一条") == 1
    assert parse_article_label("第十八条") == 18
    assert parse_article_label("第一条（附）") is None


def test_parse_html_udi():
    """UDI HTML：18 条、条号连续、首条原文精确匹配（一字不差）。"""
    parsed = parse_html(UDI_HTML.read_text(encoding="utf-8"))
    assert parsed["name"] == "医疗器械唯一标识系统规则"
    assert len(parsed["articles"]) == 18
    assert [a[0] for a in parsed["articles"]] == list(range(1, 19))
    assert parsed["articles"][0][1] == "第一条"
    assert parsed["articles"][0][2] == [
        "为规范医疗器械唯一标识系统建设，加强医疗器械全生命周期管理，根据《医疗器械监督管理条例》，制定本规则。"
    ]
    # 第三条 4 个自然段
    assert len(parsed["articles"][2][2]) == 4


def test_parse_md_sample():
    """法规总表 md：YAML 元数据、切条、同条多段、章标题跳过。"""
    parsed = parse_md(MD_SAMPLE)
    assert parsed["name"] == "测试法"
    assert parsed["doc_number"] == "主席令第1号"
    assert parsed["level"] == "法律"
    assert parsed["effective_date"] == "2024-05-01"
    labels = [a[1] for a in parsed["articles"]]
    assert labels == ["第一条", "第二条", "第十一条"]
    assert parsed["articles"][1][2] == ["测试条款。", "第二段同条另一段。"]


def test_parse_md_real_file():
    """真实保密法 md（存在时）：65 条。"""
    p = Path("/Volumes/APFS_3/法规总表/10_法律/中华人民共和国保守国家秘密法.md")
    if not p.exists():
        pytest.skip("参考文件不存在")
    parsed = parse_md(p.read_text(encoding="utf-8"))
    assert parsed["name"] == "中华人民共和国保守国家秘密法"
    assert len(parsed["articles"]) == 65
    assert parsed["articles"][0][2][0].startswith("为了保守国家秘密")
    # 第四条同条两段
    assert len(parsed["articles"][3][2]) == 2


# ---- 章/节标题不入条款 ----

def test_parse_md_skips_headings_in_any_emphasis():
    """章/节标题：纯文本、加粗、斜体三种写法都不入条款。"""
    parsed = parse_md("""---
名称: 测试办法
---

**第一章 总 则**

第一条 为了测试，制定本办法。

第二章 技术发展与治理

第二条 服务规范条款。

*第一节 一般规定*

第三条 另一条款。
""")
    assert [a[1] for a in parsed["articles"]] == ["第一条", "第二条", "第三条"]
    assert [a[2] for a in parsed["articles"]] == [["为了测试，制定本办法。"], ["服务规范条款。"], ["另一条款。"]]


def test_parse_md_keeps_sentence_starting_with_chapter_word():
    """以「第X章」开头但带句读的正文行不是标题，照常入条款。"""
    parsed = parse_md("""---
名称: 测试办法
---

第一条 为了测试，制定本办法。
第三章规定的制度，自本办法施行之日起执行。
""")
    assert parsed["articles"][0][2] == ["为了测试，制定本办法。", "第三章规定的制度，自本办法施行之日起执行。"]


# ---- 真实法规文件（法规总表在本机时才跑）----

REGULATION_DIR = Path("/Volumes/APFS_3/法规总表")


def _real_md(rel: str) -> str:
    p = REGULATION_DIR / rel
    if not p.exists():
        pytest.skip("法规总表不在本机")
    return p.read_text(encoding="utf-8")


def _article_paras(parsed: dict, label: str) -> list[str]:
    return next(a[2] for a in parsed["articles"] if a[1] == label)


def test_parse_md_real_headings_not_in_articles():
    """真实法规：章/节标题不得混进任何条款的段落。"""
    files = [
        "12_部门规章/生成式人工智能服务管理暂行办法.md",
        "12_部门规章/互联网信息服务深度合成管理规定.md",
        "12_部门规章/互联网信息服务算法推荐管理规定.md",
        "10_法律/中华人民共和国网络安全法.md",
        "10_法律/中华人民共和国个人信息保护法.md",
    ]
    heading = re.compile(r"^\*{0,2}第[一二三四五六七八九十]+[章节][ 　]")
    for rel in files:
        parsed = parse_md(_real_md(rel))
        leaked = [p for _, _, paras in parsed["articles"] for p in paras if heading.match(p)]
        assert leaked == [], f"{rel}: {leaked}"


def test_parse_md_real_lost_paragraphs_restored():
    """真实法规：抓取时丢掉的 5 个段落须在源文件里（内容为官方原文）。"""
    cyb = parse_md(_real_md("10_法律/中华人民共和国网络安全法.md"))
    assert _article_paras(cyb, "第五十条") == [
        "任何个人和组织发送的电子信息、提供的应用软件，不得设置恶意程序，不得含有法律、行政法规禁止发布或者传输的信息。",
        "电子信息发送服务提供者和应用软件下载服务提供者，应当履行安全管理义务，知道其用户有前款规定行为的，应当停止提供服务，采取消除等处置措施，保存有关记录，并向有关主管部门报告。",
    ]
    assert _article_paras(cyb, "第六十九条")[1:] == [
        "有前款行为，造成特别严重影响、特别严重后果的，由有关主管部门处二百万元以上一千万元以下罚款，责令暂停相关业务、停业整顿、关闭网站或者应用程序、吊销相关业务许可证或者吊销营业执照，对直接负责的主管人员和其他直接责任人员处二十万元以上一百万元以下罚款。",
        "电子信息发送服务提供者、应用软件下载服务提供者，不履行本法第五十条第二款规定的安全管理义务的，依照前两款规定处罚。",
    ]

    pipl = parse_md(_real_md("10_法律/中华人民共和国个人信息保护法.md"))
    assert _article_paras(pipl, "第五十二条")[1] == (
        "个人信息处理者应当公开个人信息保护负责人的联系方式，并将个人信息保护负责人的姓名、联系方式等报送履行个人信息保护职责的部门。"
    )
    assert _article_paras(pipl, "第六十五条")[1] == "履行个人信息保护职责的部门应当公布接受投诉、举报的联系方式。"

    label = parse_md(_real_md("13_规范性文件/人工智能生成合成内容标识办法.md"))
    assert _article_paras(label, "第四条")[-1] == "服务提供者提供生成合成内容下载、复制、导出等功能时，应当确保文件中含有满足要求的显式标识。"


def test_parse_md_real_no_split_words():
    """真实法规：电子签名法没有被排版拆开的词（源文件曾为「条 件」「第十七条 规定」）。"""
    parsed = parse_md(_real_md("10_法律/中华人民共和国电子签名法.md"))
    split = re.compile(r"[一-龥] [一-龥]")
    bad = [p for _, _, paras in parsed["articles"] for p in paras if split.search(p)]
    assert bad == []
