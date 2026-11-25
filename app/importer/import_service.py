"""导入服务：解析 → 入库 → 抽取术语/引用 → 全段落分词缓存。

幂等：同名法规重复导入时原位更新——条款按条号对应，文本未变的段落保留原行，
已生成的解读和练习记录不丢；换了的条款、段落删旧建新。
"""

import difflib
import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import Article, Law, Paragraph, PracticeLog, Reading, Relation, Term
from ..services.relation_extractor import extract_relations
from ..services.term_extractor import extract_terms
from ..services.tokenizer import tokenize
from .parsers import parse_file


def import_law(db: Session, path: str | Path) -> Law:
    """导入法规文件并完成术语/引用抽取与分词缓存，返回 Law。"""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"文件不存在: {path}")

    parsed = parse_file(path)
    if not parsed["articles"]:
        raise ValueError(f"未解析到任何条款: {path}")

    all_text = "\n".join(p for _, _, paras in parsed["articles"] for p in paras)
    content_hash = hashlib.sha256(all_text.encode("utf-8")).hexdigest()

    # 幂等：同名法规原位更新
    law = db.query(Law).filter(Law.name == parsed["name"]).first()
    if not law:
        law = Law(name=parsed["name"])
        db.add(law)
    law.doc_number = parsed["doc_number"]
    law.authority = parsed["authority"]
    law.level = parsed["level"]
    law.effective_date = parsed["effective_date"]
    law.source_path = str(path)
    law.source_format = "html" if path.suffix.lower() in (".html", ".htm") else "md"
    law.content_hash = content_hash
    db.flush()

    # 条款按条号对应：正文仍是同一条的原位对齐段落，换了的删旧建新
    remaining = {a.order_no: a for a in law.articles}
    article_by_label: dict[str, Article] = {}
    for order_no, label, paras in parsed["articles"]:
        article = remaining.get(order_no)
        if article is not None and _same_article(article, paras):
            del remaining[order_no]
        else:
            article = Article(law_id=law.id, order_no=order_no)
            db.add(article)
        article.label = label
        db.flush()
        article_by_label[label] = article
        _sync_paragraphs(db, article, paras)
    for article in remaining.values():
        _sync_paragraphs(db, article, [])  # 段落连同练习记录一起删
        db.query(Reading).filter(Reading.article_id == article.id).delete()
        db.delete(article)
    db.flush()

    # 术语抽取：从全文段落抽取，关联来源条款（术语首次出现的条）
    db.query(Term).filter(Term.law_id == law.id).delete()
    terms: list[Term] = []
    for order_no, label, paras in parsed["articles"]:
        for t in extract_terms(paras):
            terms.append(Term(law_id=law.id, name=t["name"], term_type=t["term_type"],
                              full_name=t["full_name"], definition=t["definition"],
                              article_id=article_by_label[label].id))
    db.add_all(terms)
    db.flush()

    # 引用关系：to_law_id 若库中已有同名法规则关联
    db.query(Relation).filter(Relation.from_law_id == law.id).delete()
    for order_no, label, paras in parsed["articles"]:
        for r in extract_relations(paras):
            to_law = db.query(Law).filter(Law.name == r["to_law_name"]).first()
            db.add(Relation(from_law_id=law.id, to_law_id=to_law.id if to_law else None,
                            to_law_name=r["to_law_name"], relation_type=r["relation_type"],
                            article_id=article_by_label[label].id))
    db.flush()

    # 分词缓存：实体词典优先，term_id 标记命中术语
    term_map = {t.name: t.id for t in terms}
    for para in db.query(Paragraph).join(Article).filter(Article.law_id == law.id).all():
        para.tokens = tokenize(para.text, term_map)

    db.commit()
    db.refresh(law)
    return law


def _same_article(article: Article, paras: list[str]) -> bool:
    """新旧条款正文是否仍是同一条：改错字、增删段算，换了一条不算（防改版条号位移后错挂解读）。"""
    old = "\n".join(p.text for p in article.paragraphs)
    return difflib.SequenceMatcher(None, old, "\n".join(paras), autojunk=False).ratio() >= 0.5


def _sync_paragraphs(db: Session, article: Article, texts: list[str]) -> None:
    """按顺序对齐条款段落：文本未变的保留原行（练习记录随之保留），其余删旧建新。"""
    rows = list(article.paragraphs)
    kept: list[Paragraph] = []
    matcher = difflib.SequenceMatcher(a=[r.text for r in rows], b=texts, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            kept += rows[i1:i2]
            continue
        for row in rows[i1:i2]:
            db.query(PracticeLog).filter(PracticeLog.paragraph_id == row.id).delete()
            db.delete(row)
        kept += [Paragraph(article_id=article.id, text=text) for text in texts[j1:j2]]
    for order_no, row in enumerate(kept, 1):
        row.order_no = order_no
        db.add(row)
