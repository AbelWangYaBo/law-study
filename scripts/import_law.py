"""导入法规文件入库（幂等，可反复执行）。

用法: uv run python scripts/import_law.py <法规文件路径.html|.md>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.importer.import_service import import_law
from app.models import Article, Paragraph, Term


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    path = Path(sys.argv[1]).expanduser()
    db = SessionLocal()
    try:
        law = import_law(db, path)
        n_articles = db.query(Article).filter(Article.law_id == law.id).count()
        n_paras = db.query(Paragraph).join(Article).filter(Article.law_id == law.id).count()
        n_terms = db.query(Term).filter(Term.law_id == law.id).count()
        print(f"导入完成: {law.name}")
        print(f"  条款 {n_articles} 条 / 段落 {n_paras} 段 / 术语 {n_terms} 个")
    finally:
        db.close()


if __name__ == "__main__":
    main()
