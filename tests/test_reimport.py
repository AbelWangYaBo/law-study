"""重复导入：同名法规原位更新，法规/条款/段落 ID 与解读、练习记录不丢。"""

from pathlib import Path

from bs4 import BeautifulSoup

from app.importer.import_service import import_law
from app.models import Article, Law, Paragraph, PracticeLog, Reading, Relation, Term

UDI_HTML = Path(__file__).resolve().parent / "fixtures" / "医疗器械唯一标识系统规则.html"


def _rewritten(tmp_path, edit) -> Path:
    """复制 UDI 样例并改写，返回新文件路径。"""
    soup = BeautifulSoup(UDI_HTML.read_text(encoding="utf-8"), "html.parser")
    edit(soup)
    path = tmp_path / "改写.html"
    path.write_text(str(soup), encoding="utf-8")
    return path


def _structure(db, law) -> tuple:
    """法规 ID → [(条款 ID, [段落 ID])]，以及术语、引用关系条数。"""
    return (
        law.id,
        [(a.id, [p.id for p in a.paragraphs]) for a in law.articles],
        db.query(Term).filter(Term.law_id == law.id).count(),
        db.query(Relation).filter(Relation.from_law_id == law.id).count(),
    )


def test_reimport_same_file_changes_nothing(db_session):
    """原文件重复导入：ID 结构、术语、引用关系全部不变，解读和练习记录仍挂在原条款/段落上。"""
    law = import_law(db_session, UDI_HTML)
    reading = Reading(article_id=law.articles[0].id, kind="interpret", model="m", content="解读")
    log = PracticeLog(paragraph_id=law.articles[0].paragraphs[0].id, correct=True)
    db_session.add_all([reading, log])
    db_session.commit()
    before = _structure(db_session, law)

    again = import_law(db_session, UDI_HTML)

    assert _structure(db_session, again) == before
    assert db_session.query(Law).count() == 1
    assert db_session.get(Reading, reading.id).article_id == again.articles[0].id
    assert db_session.get(PracticeLog, log.id).paragraph_id == again.articles[0].paragraphs[0].id


def test_reimport_edits_paragraphs_in_place(db_session, tmp_path):
    """源文件改了段落：未变的段落保留原 ID，改写的换新行，删掉的连同练习记录一起删，分词随之更新。"""
    law = import_law(db_session, UDI_HTML)
    kept_id = law.articles[1].paragraphs[0].id      # 第二条：未改动
    removed = law.articles[2].paragraphs[-1]        # 第三条末段：将被删除
    db_session.add_all([PracticeLog(paragraph_id=removed.id, correct=True), PracticeLog(paragraph_id=kept_id, correct=True)])
    db_session.commit()
    article_ids = [a.id for a in law.articles]
    revised = law.articles[0].paragraphs[0].text.replace("制定本规则。", "制定本规则（修订）。")

    def edit(soup):
        sections = soup.find_all("section")
        sections[0].find_all("p")[0].string = revised
        added = soup.new_tag("p")
        added.string = "新增段落。"
        sections[1].append(added)
        sections[2].find_all("p")[-1].decompose()

    again = import_law(db_session, _rewritten(tmp_path, edit))

    assert again.id == law.id
    assert [a.id for a in again.articles] == article_ids
    assert [p.text for p in again.articles[0].paragraphs] == [revised]
    assert again.articles[1].paragraphs[0].id == kept_id
    assert [p.text for p in again.articles[1].paragraphs][-1] == "新增段落。"
    assert len(again.articles[2].paragraphs) == 3
    assert [log.paragraph_id for log in db_session.query(PracticeLog).all()] == [kept_id]
    assert "".join(t["t"] for t in again.articles[0].paragraphs[0].tokens) == revised


def test_reimport_replaced_article_drops_stale_readings(db_session, tmp_path):
    """改版后条号位移：同一编号下已是另一条内容时视为新条款——旧解读清除，不错挂到新内容上。"""
    law = import_law(db_session, UDI_HTML)
    replaced_id = law.articles[1].id      # 第二条：单段，将被整条换成无关内容
    other_ids = [a.id for i, a in enumerate(law.articles) if i != 1]
    db_session.add(Reading(article_id=replaced_id, kind="interpret", model="m", content="旧条的解读"))
    db_session.commit()

    def edit(soup):
        soup.find_all("section")[1].find("p").string = "换成了完全不同的另一条规定，原文一字不留。"

    again = import_law(db_session, _rewritten(tmp_path, edit))

    assert len(again.articles) == 18
    assert again.articles[1].id != replaced_id
    assert again.articles[1].paragraphs[0].text == "换成了完全不同的另一条规定，原文一字不留。"
    assert db_session.query(Reading).all() == []
    assert [a.id for i, a in enumerate(again.articles) if i != 1] == other_ids


def test_reimport_added_and_removed_articles(db_session, tmp_path):
    """源文件增删了条款：其余条款 ID 不变，被删条款的段落与解读一并清除，不残留孤儿行。"""
    law = import_law(db_session, UDI_HTML)
    removed, kept = law.articles[-1], law.articles[0]
    db_session.add_all([
        Reading(article_id=removed.id, kind="interpret", model="m", content="旧解读"),
        Reading(article_id=kept.id, kind="interpret", model="m", content="保留的解读"),
    ])
    db_session.commit()
    removed_id = removed.id

    def edit(soup):
        soup.find_all("section")[-1].decompose()
        soup.append(BeautifulSoup('<section><h2>第十九条</h2><p>新增条款的段落。</p></section>', "html.parser"))

    again = import_law(db_session, _rewritten(tmp_path, edit))

    assert again.id == law.id
    assert [a.label for a in again.articles][-1] == "第十九条"
    assert again.articles[0].id == kept.id
    assert [r.content for r in db_session.query(Reading).all()] == ["保留的解读"]
    assert db_session.query(Article).count() == 18
    assert db_session.query(Paragraph).filter(Paragraph.article_id == removed_id).count() == 0
