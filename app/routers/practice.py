"""背诵练习 API：打乱词块、判分记录、进度。"""

import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Article, Law, Paragraph, PracticeLog

router = APIRouter(prefix="/api/practice", tags=["practice"])


@router.get("/paragraphs/{paragraph_id}/shuffle")
def shuffle_paragraph(paragraph_id: int, db: Session = Depends(get_db)):
    """返回打乱后的词块（保证与原序不同，长度>1 时）。"""
    para = db.get(Paragraph, paragraph_id)
    if not para:
        raise HTTPException(404, "段落不存在")
    blocks = [dict(t) for t in para.tokens]
    if len(blocks) > 1:
        original = [b["t"] for b in blocks]
        for _ in range(20):
            random.shuffle(blocks)
            if [b["t"] for b in blocks] != original:
                break
    return {"paragraph_id": para.id, "text_length": len(para.text), "blocks": blocks}


class CheckRequest(BaseModel):
    paragraph_id: int
    tokens: list[str]
    duration_ms: int = 0


@router.post("/check")
def check_answer(req: CheckRequest, db: Session = Depends(get_db)):
    """逐词严格比对判分并记录练习日志。"""
    para = db.get(Paragraph, req.paragraph_id)
    if not para:
        raise HTTPException(404, "段落不存在")
    expected = [t["t"] for t in para.tokens]
    got = req.tokens
    detail = [
        {"t": got[i] if i < len(got) else None, "expected": expected[i],
         "ok": i < len(got) and got[i] == expected[i]}
        for i in range(max(len(got), len(expected)))
    ]
    correct = got == expected
    db.add(PracticeLog(paragraph_id=para.id, correct=correct, duration_ms=req.duration_ms))
    db.commit()
    return {"correct": correct, "detail": detail}


@router.get("/progress")
def progress(law_id: int, db: Session = Depends(get_db)):
    """每段最新练习状态（段落级：任一次拼对即为已通过）。"""
    if not db.get(Law, law_id):
        raise HTTPException(404, "法规不存在")
    paras = (
        db.query(Paragraph)
        .join(Article)
        .filter(Article.law_id == law_id)
        .order_by(Article.order_no, Paragraph.order_no)
        .all()
    )
    logs = db.query(PracticeLog).filter(
        PracticeLog.paragraph_id.in_([p.id for p in paras])
    ).all()
    passed = {log.paragraph_id for log in logs if log.correct}
    attempted = {log.paragraph_id for log in logs}
    return {
        "paragraphs": [
            {
                "id": p.id, "article_id": p.article_id, "order_no": p.order_no,
                "status": "passed" if p.id in passed else ("attempted" if p.id in attempted else "new"),
            }
            for p in paras
        ],
        "total": len(paras), "passed": len(passed), "attempted": len(attempted - passed),
    }
