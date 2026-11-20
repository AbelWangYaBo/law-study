"""法规引用关系抽取：「根据/依据/依照《XXX》」。"""

import re

_CITE_RE = re.compile(r"(根据|依据|依照)《([^《》]{2,50})》")


def extract_relations(paragraphs: list[str]) -> list[dict]:
    """返回: [{to_law_name, relation_type}]，同名去重。"""
    seen: dict[str, dict] = {}
    for text in paragraphs:
        for m in _CITE_RE.finditer(text):
            name, verb = m.group(2), m.group(1)
            if name not in seen:
                seen[name] = {"to_law_name": name, "relation_type": "依据" if verb in ("根据", "依据", "依照") else "引用"}
    return list(seen.values())
