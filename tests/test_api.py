"""API 端到端测试：导入 → 详情 → 打乱 → 判分 → 进度 → 术语 → 图谱 → AI。"""

from pathlib import Path

from app.importer.import_service import import_law

UDI_HTML = Path("/Volumes/APFS_2/abel/走进先健/医疗器械唯一标识系统规则.html")


def _import(db_session):
    return import_law(db_session, UDI_HTML)


def test_import_and_detail(db_session, client):
    law = _import(db_session)
    assert law.name == "医疗器械唯一标识系统规则"

    r = client.get("/api/laws")
    assert r.status_code == 200 and len(r.json()) == 1
    assert r.json()[0]["article_count"] == 18

    detail = client.get(f"/api/laws/{law.id}").json()
    assert len(detail["articles"]) == 18
    first_para = detail["articles"][0]["paragraphs"][0]
    assert first_para["text"].endswith("制定本规则。")
    # 术语标记：第三条首段应含术语 token
    art3 = detail["articles"][2]["paragraphs"][0]
    assert any(t.get("term_id") for t in art3["tokens"])


def test_fulltext_lossless(db_session, client):
    """API 全文与源 HTML 一字不差。"""
    from bs4 import BeautifulSoup

    law = _import(db_session)
    src = [
        p.get_text()
        for s in BeautifulSoup(UDI_HTML.read_text(encoding="utf-8"), "html.parser").find_all("section")
        for p in s.find_all("p") if p.get_text(strip=True)
    ]
    got = client.get(f"/api/laws/{law.id}/fulltext").json()["paragraphs"]
    assert got == src


def test_shuffle_and_check(db_session, client):
    law = _import(db_session)
    detail = client.get(f"/api/laws/{law.id}").json()
    para = detail["articles"][0]["paragraphs"][0]
    original = [t["t"] for t in para["tokens"]]

    # 打乱：内容同集合、顺序不同
    sh = client.get(f"/api/practice/paragraphs/{para['id']}/shuffle").json()
    assert sorted(b["t"] for b in sh["blocks"]) == sorted(original)
    assert [b["t"] for b in sh["blocks"]] != original

    # 正确答案判分
    r = client.post("/api/practice/check", json={"paragraph_id": para["id"], "tokens": original, "duration_ms": 5000}).json()
    assert r["correct"] is True and all(d["ok"] for d in r["detail"])

    # 错误答案判分：首词错位
    wrong = original[::-1]
    r2 = client.post("/api/practice/check", json={"paragraph_id": para["id"], "tokens": wrong}).json()
    assert r2["correct"] is False
    assert r2["detail"][0]["ok"] is False

    # 进度：该段 passed
    prog = client.get(f"/api/practice/progress?law_id={law.id}").json()
    assert prog["total"] == 37 and prog["passed"] == 1
    assert next(p for p in prog["paragraphs"] if p["id"] == para["id"])["status"] == "passed"


def test_terms_and_graph(db_session, client):
    law = _import(db_session)
    terms = client.get(f"/api/laws/{law.id}/terms").json()
    names = [t["name"] for t in terms]
    assert "医疗器械唯一标识" in names and len(terms) == 8
    src = next(t for t in terms if t["name"] == "医疗器械唯一标识")
    assert src["article_label"] == "第三条"

    # 引用图
    g = client.get("/api/graph/relations").json()
    assert any(l["target"] == "医疗器械监督管理条例" for l in g["links"])

    # 法规树
    tree = client.get("/api/graph/law-tree").json()
    assert any("医疗器械监督管理条例" in str(n) for n in tree["children"])

    # 术语共现图
    tg = client.get(f"/api/graph/term-graph?law_id={law.id}").json()
    assert len(tg["nodes"]) == 8
    assert any(l["source"] == "医疗器械唯一标识" for l in tg["links"])


def test_ai_not_configured(db_session, client):
    """未配置 AI 时返回 503 且提示配置。"""
    law = _import(db_session)
    detail = client.get(f"/api/laws/{law.id}").json()
    r = client.post("/api/ai/reading", json={"article_id": detail["articles"][0]["id"], "kind": "interpret"})
    assert r.status_code == 503
    assert "AI_BASE_URL" in r.json()["detail"]


def test_import_idempotent(db_session, client):
    """重复导入：同名重建，仍只有 1 部法规。"""
    _import(db_session)
    _import(db_session)
    laws = client.get("/api/laws").json()
    assert len(laws) == 1 and laws[0]["article_count"] == 18
