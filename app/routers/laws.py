"""法规 API：列表/导入/详情、术语字典。"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..importer.import_service import import_law
from ..models import Article, Law, Paragraph, Reading, Term

router = APIRouter(prefix="/api/laws", tags=["laws"])


class ImportRequest(BaseModel):
    path: str


@router.get("")
def list_laws(db: Session = Depends(get_db)):
    laws = db.query(Law).order_by(Law.id).all()
    return [
        {
            "id": l.id, "name": l.name, "doc_number": l.doc_number,
            "authority": l.authority, "level": l.level, "effective_date": l.effective_date,
            "article_count": len(l.articles), "term_count": len(l.terms),
        }
        for l in laws
    ]


@router.post("/import")
def import_law_api(req: ImportRequest, db: Session = Depends(get_db)):
    try:
        law = import_law(db, Path(req.path))
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"id": law.id, "name": law.name, "article_count": len(law.articles)}


@router.get("/{law_id}")
def law_detail(law_id: int, db: Session = Depends(get_db)):
    """法规详情 + 全部条款段落（阅读视图一次拉全，含分词与术语标记）。"""
    law = db.get(Law, law_id)
    if not law:
        raise HTTPException(404, "法规不存在")
    articles = (
        db.query(Article)
        .filter(Article.law_id == law_id)
        .order_by(Article.order_no)
        .all()
    )
    return {
        "id": law.id, "name": law.name, "doc_number": law.doc_number,
        "authority": law.authority, "level": law.level, "effective_date": law.effective_date,
        "articles": [
            {
                "id": a.id, "order_no": a.order_no, "label": a.label,
                "paragraphs": [
                    {"id": p.id, "order_no": p.order_no, "text": p.text, "tokens": p.tokens}
                    for p in a.paragraphs
                ],
            }
            for a in articles
        ],
    }


@router.get("/{law_id}/terms")
def law_terms(law_id: int, db: Session = Depends(get_db)):
    """术语字典。"""
    if not db.get(Law, law_id):
        raise HTTPException(404, "法规不存在")
    terms = db.query(Term).filter(Term.law_id == law_id).order_by(Term.id).all()
    article_labels = {a.id: a.label for a in db.query(Article).filter(Article.law_id == law_id).all()}
    return [
        {
            "id": t.id, "name": t.name, "term_type": t.term_type,
            "full_name": t.full_name, "definition": t.definition,
            "article_id": t.article_id, "article_label": article_labels.get(t.article_id, ""),
        }
        for t in terms
    ]


@router.get("/{law_id}/readings")
def law_readings(law_id: int, db: Session = Depends(get_db)):
    """已生成的 AI 解读/场景分析（含历史，按条款排序）。"""
    if not db.get(Law, law_id):
        raise HTTPException(404, "法规不存在")
    rows = (
        db.query(Reading, Article)
        .join(Article, Reading.article_id == Article.id)
        .filter(Article.law_id == law_id)
        .order_by(Article.order_no, Reading.id)
        .all()
    )
    return [
        {
            "article_id": r.article_id, "article_label": a.label, "article_order": a.order_no,
            "kind": r.kind, "model": r.model, "content": r.content,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        }
        for r, a in rows
    ]


@router.get("/{law_id}/fulltext")
def law_fulltext(law_id: int, db: Session = Depends(get_db)):
    """全文校验导出：段落原文拼接（用于一字不差核对）。"""
    if not db.get(Law, law_id):
        raise HTTPException(404, "法规不存在")
    paras = (
        db.query(Paragraph)
        .join(Article)
        .filter(Article.law_id == law_id)
        .order_by(Article.order_no, Paragraph.order_no)
        .all()
    )
    return {"paragraphs": [p.text for p in paras]}
