"""导入解读草稿到 readings 表：data/readings-drafts/law-*/a{条款ID}-{interpret|scenario}.md。

草稿由 AI 代理或人工撰写，一个文件一份解读（正文为 markdown）。同条款同类型已有解读的跳过，
可反复执行。导入后运行 scripts/snapshot.py 导出到快照。

用法: uv run python scripts/import_readings.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Article, Reading

DRAFTS_DIR = Path(__file__).resolve().parent.parent / "data" / "readings-drafts"
MODEL = "Claude Code (glm-5.4[1m])"
_FILENAME = re.compile(r"^a(\d+)-(interpret|scenario)\.md$")


def import_readings(db, drafts_dir: Path = DRAFTS_DIR) -> int:
    """导入草稿，返回新导入的份数。"""
    existing = {(r[0], r[1]) for r in db.query(Reading.article_id, Reading.kind)}
    todo = []
    for path in sorted(drafts_dir.glob("law-*/a*.md")):
        m = _FILENAME.match(path.name)
        if not m:
            continue
        key = (int(m[1]), m[2])
        if key not in existing:
            todo.append((key, path.read_text(encoding="utf-8").strip()))

    unknown = [key[0] for key, _ in todo if not db.get(Article, key[0])]
    if unknown:
        raise SystemExit(f"草稿对应的条款不存在（法规可能已重新导入，条款 ID 已变）：{unknown}")
    for (article_id, kind), content in todo:
        db.add(Reading(article_id=article_id, kind=kind, model=MODEL, content=content))
    db.commit()
    return len(todo)


def main() -> None:
    db = SessionLocal()
    try:
        n = import_readings(db)
    finally:
        db.close()
    print(f"导入 {n} 份解读 → readings 表；随后运行 uv run python scripts/snapshot.py 导出快照")


if __name__ == "__main__":
    main()
