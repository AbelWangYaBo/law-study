"""解析器测试：HTML（UDI）与 MD（法规总表）格式。"""

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
