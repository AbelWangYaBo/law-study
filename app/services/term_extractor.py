"""术语抽取（规则式）：定义 / 简称 / 英文缩写。"""

import re

# 「XX，是指……」定义模式（XX 不含句内停顿标点与引号；引号用 “/” 规避字面量歧义）
_DEF_RE = re.compile(r"([^，。；：、（）“”\s]{2,30})，是指([^。；]*)")
# 「（以下简称“X”）」简称模式
_SHORT_RE = re.compile(r"[（(]以下简称[“]?([^“”]{1,30})[”’]?[）)]")
# 「中文名（ABBR）」英文缩写模式
_ABBR_RE = re.compile(r"([一-龥][一-龥0-9]{1,29})[（(]([A-Z][A-Za-z0-9-]{1,15})[）)]")


def extract_terms(paragraphs: list[str]) -> list[dict]:
    """从段落列表抽取术语。

    返回: [{name, term_type, full_name, definition, source_text}]
    同名术语只保留首次出现（先出现的定义优先）。
    """
    found: dict[str, dict] = {}

    def add(name: str, term_type: str, full_name: str = "", definition: str = "") -> None:
        name = name.strip()
        if name and name not in found:
            found[name] = {
                "name": name,
                "term_type": term_type,
                "full_name": full_name,
                "definition": definition.strip("，。；"),
            }

    for text in paragraphs:
        for m in _DEF_RE.finditer(text):
            add(m.group(1), "definition", definition=m.group(2))
        for m in _SHORT_RE.finditer(text):
            add(m.group(1), "short_name", full_name="")
        for m in _ABBR_RE.finditer(text):
            add(m.group(2), "abbreviation", full_name=m.group(1))

    return list(found.values())
