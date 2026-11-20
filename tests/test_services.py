"""抽取器与分词器测试。"""

from app.services.relation_extractor import extract_relations
from app.services.term_extractor import extract_terms
from app.services.tokenizer import tokenize

TERM_MAP = {"医疗器械唯一标识": 1, "医疗器械唯一标识数据载体": 2}


def test_extract_terms_definition():
    paras = [
        "本规则所称医疗器械唯一标识系统，由医疗器械唯一标识、唯一标识数据载体和唯一标识数据库组成。",
        "医疗器械唯一标识，是指在医疗器械产品或者包装上附载的，由数字、字母或者符号组成的代码。",
        "唯一性，是指医疗器械唯一标识应当与医疗器械识别要求相一致。",
    ]
    terms = {t["name"]: t for t in extract_terms(paras)}
    assert "医疗器械唯一标识" in terms
    assert terms["医疗器械唯一标识"]["term_type"] == "definition"
    assert "唯一性" in terms


def test_extract_terms_short_name_and_abbr():
    paras = [
        "保守国家秘密（以下简称保密）工作适用本法。",
        "医疗器械唯一标识（UDI）是代码。",
    ]
    terms = {t["name"]: t for t in extract_terms(paras)}
    assert terms["保密"]["term_type"] == "short_name"
    assert terms["UDI"]["term_type"] == "abbreviation"
    assert terms["UDI"]["full_name"] == "医疗器械唯一标识"


def test_extract_relations():
    paras = ["根据《医疗器械监督管理条例》，制定本规则。", "依据《中华人民共和国产品质量法》处罚。"]
    rels = {r["to_law_name"]: r["relation_type"] for r in extract_relations(paras)}
    assert rels == {"医疗器械监督管理条例": "依据", "中华人民共和国产品质量法": "依据"}


def test_tokenize_lossless_and_terms():
    """分词无损 + 词典术语不被切碎 + 标点独立 + 字母数字串整体。"""
    text = "医疗器械唯一标识数据载体应当满足自动识别要求，2019年10月1日起施行。"
    tokens = tokenize(text, TERM_MAP)
    # 无损
    assert "".join(t["t"] for t in tokens) == text
    # 长术语优先于前缀术语
    names = [t["t"] for t in tokens]
    assert "医疗器械唯一标识数据载体" in names
    assert "医疗器械唯一标识" not in names  # 不应出现前缀碎片
    tid = next(t for t in tokens if t["t"] == "医疗器械唯一标识数据载体")
    assert tid["term_id"] == 2
    # 标点独立
    assert "，" in names and "。" in names
    # 字母数字串整体
    text2 = "本法自2019年10月1日起施行。"
    tokens2 = tokenize(text2, {})
    assert "2019" in [t["t"] for t in tokens2]
    assert "".join(t["t"] for t in tokens2) == text2


def test_tokenize_empty():
    assert tokenize("", {}) == []
