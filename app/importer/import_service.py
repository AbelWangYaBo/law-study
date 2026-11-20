"""导入服务：解析 → 入库 → 抽取术语/引用 → 全段落分词缓存。

幂等：同名法规重复导入时删除旧数据重建。
"""

import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import Article, Law, Paragraph, Relation, Term
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

    # 幂等：同名法规删除重建
    old = db.query(Law).filter(Law.name == parsed["name"]).first()
    if old:
        db.delete(old)
        db.flush()

    fmt = "html" if path.suffix.lower() in (".html", ".htm") else "md"
    law = Law(
        name=parsed["name"],
        doc_number=parsed["doc_number"],
        authority=parsed["authority"],
        level=parsed["level"],
        effective_date=parsed["effective_date"],
        source_path=str(path),
        source_format=fmt,
        content_hash=content_hash,
    )
    db.add(law)
    db.flush()

    article_by_label: dict[str, Article] = {}
    for order_no, label, paras in parsed["articles"]:
        article = Article(law_id=law.id, order_no=order_no, label=label)
        db.add(article)
        db.flush()
        article_by_label[label] = article
        for i, text in enumerate(paras, 1):
            db.add(Paragraph(article_id=article.id, order_no=i, text=text, tokens=[]))
    db.flush()

    # 术语抽取：从全文段落抽取，关联来源条款（术语首次出现的条）
    terms: list[Term] = []
    for order_no, label, paras in parsed["articles"]:
        for t in extract_terms(paras):
            terms.append(Term(law_id=law.id, name=t["name"], term_type=t["term_type"],
                              full_name=t["full_name"], definition=t["definition"],
                              article_id=article_by_label[label].id))
    db.add_all(terms)
    db.flush()

    # 引用关系：to_law_id 若库中已有同名法规则关联
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
