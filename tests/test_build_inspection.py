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
