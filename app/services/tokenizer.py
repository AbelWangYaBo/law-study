"""混合分词器：实体词典最大匹配优先 + jieba 兜底，标点独立成块。

不变式："".join(t["t"] for t in tokenize(text, terms)) == text（无损）。
"""

import logging
import re

import jieba

jieba.setLogLevel(logging.WARNING)

# 汉字串 / 字母数字串（含常见半角符号组合）——其余字符（标点、空白）逐个独立
_CHUNK_RE = re.compile(r"[一-龥]+|[A-Za-z0-9/.]+|.")


def _dict_match(seg: str, vocab: list[tuple[str, int]]) -> list[tuple[str, int | None]]:
    """对纯汉字段做词典最大匹配；未匹配部分交给 jieba。

    vocab: [(术语, term_id)] 按术语长度降序。
    返回: [(token, term_id | None)]
    """
    result: list[tuple[str, int | None]] = []
    i, n = 0, len(seg)
    while i < n:
        matched = None
        for name, term_id in vocab:
            if name and seg.startswith(name, i):
                matched = (name, term_id)
                break  # vocab 已按长度降序，首个命中即最长
        if matched:
            result.append(matched)
            i += len(matched[0])
        else:
            # jieba 切到下一个词典可命中位置前——这里简单起见 jieba 逐词前进，
            # 若 jieba 词恰好在 vocab 里（理论少见）也不影响无损性
            piece = seg[i:]
            cut = jieba.lcut(piece)[0] if piece else ""
            if not cut:  # 防御：jieba 不应返回空首词
                cut = seg[i]
            result.append((cut, None))
            i += len(cut)
    return result


def tokenize(text: str, term_map: dict[str, int] | None = None) -> list[dict]:
    """把文本切成 token 序列。

    term_map: {术语名: term_id}，命中词典的 token 带 term_id。
    返回: [{"t": 词, "term_id": int | None}, ...]
    """
    vocab = sorted(
        ((name, tid) for name, tid in (term_map or {}).items() if name),
        key=lambda x: len(x[0]),
        reverse=True,
    )
    tokens: list[dict] = []
    for chunk in _CHUNK_RE.findall(text):
        if re.fullmatch(r"[一-龥]+", chunk):
            for tok, tid in _dict_match(chunk, vocab):
                tokens.append({"t": tok, "term_id": tid})
        else:
            # 字母数字串整体成词，标点/空白独立成块
            tokens.append({"t": chunk, "term_id": None})
    assert "".join(t["t"] for t in tokens) == text, "分词必须无损还原原文"
    return tokens
