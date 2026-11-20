"""AI 解读 API：生成/取缓存，force 可强制重新生成。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Article, Law, Reading
from ..services.ai_service import generate_reading

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ReadingRequest(BaseModel):
    article_id: int
    kind: str          # interpret / scenario
    force: bool = False


@router.post("/reading")
def reading(req: ReadingRequest, db: Session = Depends(get_db)):
    if req.kind not in ("interpret", "scenario"):
        raise HTTPException(422, "kind 必须是 interpret 或 scenario")
    article = db.get(Article, req.article_id)
    if not article:
        raise HTTPException(404, "条款不存在")
    law = db.get(Law, article.law_id)

    # 缓存：同条款同类型最新一条
    if not req.force:
        cached = (
            db.query(Reading)
            .filter(Reading.article_id == article.id, Reading.kind == req.kind)
            .order_by(Reading.id.desc())
            .first()
        )
        if cached:
            return {"cached": True, "model": cached.model, "content": cached.content}

    content_text = "\n".join(p.text for p in article.paragraphs)
    try:
        content = generate_reading(law.name, article.label, content_text, req.kind)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:  # 上游网关错误
        raise HTTPException(502, f"AI 调用失败: {e}")

    from ..config import settings
    reading = Reading(article_id=article.id, kind=req.kind, model=settings.ai_model, content=content)
    db.add(reading)
    db.commit()
    return {"cached": False, "model": reading.model, "content": reading.content}
