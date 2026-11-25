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
