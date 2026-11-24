"""解读草稿导入：按文件名入库、幂等、条款不存在时拒绝。"""

from pathlib import Path

import pytest

from app.importer.import_service import import_law
from app.models import Reading
from scripts.import_readings import MODEL, import_readings

UDI_HTML = Path(__file__).resolve().parent / "fixtures" / "医疗器械唯一标识系统规则.html"


def _write_drafts(root, *files):
    drafts = root / "law-1"
    drafts.mkdir(parents=True, exist_ok=True)
    for name, content in files:
        (drafts / name).write_text(content, encoding="utf-8")


def test_import_readings(db_session, client, tmp_path):
    """按文件名 a{条款ID}-{kind}.md 入库，readings 接口可读到。"""
    law = import_law(db_session, UDI_HTML)
    first, second = law.articles[0].id, law.articles[1].id
    _write_drafts(
        tmp_path,
        (f"a{first:04d}-interpret.md", "## 本条要点\n要点"),
        (f"a{second:04d}-scenario.md", "## 落地场景\n场景"),
    )

    assert import_readings(db_session, tmp_path) == 2
    rows = client.get(f"/api/laws/{law.id}/readings").json()
    assert [(r["article_id"], r["kind"], r["content"], r["model"]) for r in rows] == [
        (first, "interpret", "## 本条要点\n要点", MODEL),
        (second, "scenario", "## 落地场景\n场景", MODEL),
    ]


def test_import_readings_idempotent(db_session, tmp_path):
    """同条款同类型已有解读的草稿跳过。"""
    law = import_law(db_session, UDI_HTML)
    article_id = law.articles[0].id
    _write_drafts(tmp_path, (f"a{article_id:04d}-interpret.md", "v1"), (f"a{article_id:04d}-scenario.md", "场景"))
    import_readings(db_session, tmp_path)

    _write_drafts(tmp_path, (f"a{article_id:04d}-interpret.md", "v2"))
    assert import_readings(db_session, tmp_path) == 0
    assert db_session.query(Reading).count() == 2


def test_import_readings_unknown_article(db_session, tmp_path):
    """草稿对应的条款不存在（法规已重新导入）时整批拒绝。"""
    import_law(db_session, UDI_HTML)
    _write_drafts(tmp_path, ("a9999-interpret.md", "要点"))

    with pytest.raises(SystemExit, match="条款不存在"):
        import_readings(db_session, tmp_path)
    assert db_session.query(Reading).count() == 0
