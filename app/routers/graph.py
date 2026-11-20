"""知识图谱 API：法规层级/引用树、引用关系图、术语共现图。"""

from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Article, Law, Paragraph, Relation, Term

router = APIRouter(prefix="/api/graph", tags=["graph"])

# 效力层级从高到低
_LEVEL_ORDER = ["法律", "行政法规", "部门规章", "规范性文件"]


def _level_node(level: str) -> dict:
    return {"name": level, "itemStyle": {"color": "#8c8579"}, "children": []}


@router.get("/law-tree")
def law_tree(db: Session = Depends(get_db)):
    """法规父子树：引用关系（被引法规为父）+ 效力层级分组兜底。"""
    laws = db.query(Law).all()
    law_by_id = {l.id: l for l in laws}
    relations = db.query(Relation).all()

    # 节点：库中法规 + 被引法规（虚拟）
    nodes: dict[str, dict] = {}
    for l in laws:
        nodes[l.name] = {"name": l.name, "extra": {"level": l.level, "law_id": l.id, "virtual": False}, "children": []}
    for r in relations:
        target = r.to_law_name
        if target not in nodes:
            nodes[target] = {"name": target, "extra": {"level": "", "law_id": r.to_law_id, "virtual": True}, "children": []}

    # 引用边：to 为父，from 为子
    children_of: dict[str, list[str]] = defaultdict(list)
    has_parent: set[str] = set()
    for r in relations:
        parent = r.to_law_name
        child = law_by_id[r.from_law_id].name
        if child not in has_parent and child != parent:
            children_of[parent].append(child)
            has_parent.add(child)

    def attach(name: str) -> dict:
        node = dict(nodes[name])
        node["children"] = [attach(c) for c in children_of.get(name, [])]
        return node

    # 根：未被引用的节点；库中无引用边的挂效力层级分组
    roots: list[dict] = []
    for name, node in nodes.items():
        if name in has_parent:
            continue
        if node["extra"]["virtual"]:
            roots.append(attach(name))
        else:
            level = node["extra"].get("level") or "其他"
            roots.append({"name": level, "itemStyle": {"color": "#8c8579"}, "children": [attach(name)]})

    # 同层级分组合并
    merged: list[dict] = []
    for r in roots:
        if "itemStyle" in r:  # 分组节点
            same = next((m for m in merged if m["name"] == r["name"]), None)
            if same:
                same["children"].extend(r["children"])
                continue
        merged.append(r)
    return {"name": "法规体系", "children": merged}


@router.get("/relations")
def relation_graph(db: Session = Depends(get_db)):
    """法规引用力导向图。"""
    laws = db.query(Law).all()
    law_by_id = {l.id: l for l in laws}
    relations = db.query(Relation).all()

    node_names: set[str] = {l.name for l in laws}
    for r in relations:
        node_names.add(r.to_law_name)
    level_by_name = {l.name: l.level for l in laws}

    nodes = []
    for name in node_names:
        virtual = name not in level_by_name
        nodes.append({
            "id": name, "name": name,
            "symbolSize": 40 if virtual else 55,
            "category": "被引用法规" if virtual else "已入库法规",
            "level": level_by_name.get(name, ""),
        })
    links = [
        {"source": law_by_id[r.from_law_id].name, "target": r.to_law_name, "value": r.relation_type}
        for r in relations
    ]
    return {"nodes": nodes, "links": links,
            "categories": [{"name": "已入库法规"}, {"name": "被引用法规"}]}


@router.get("/term-graph")
def term_graph(law_id: int, db: Session = Depends(get_db)):
    """术语共现图：同一条款出现的术语连边，节点大小=出现次数。"""
    if not db.get(Law, law_id):
        raise HTTPException(404, "法规不存在")
    terms = db.query(Term).filter(Term.law_id == law_id).all()
    term_by_id = {t.id: t for t in terms}

    # 统计每个条款命中的术语
    articles = db.query(Article).filter(Article.law_id == law_id).all()
    article_label = {a.id: a.label for a in articles}
    article_terms: dict[int, set[int]] = defaultdict(set)  # article_id -> term_id 集合
    occ_count: Counter = Counter()                         # term_id -> 出现次数
    for para in db.query(Paragraph).join(Article).filter(Article.law_id == law_id).all():
        for tok in para.tokens or []:
            tid = tok.get("term_id")
            if tid is not None and tid in term_by_id:
                article_terms[para.article_id].add(tid)
                occ_count[tid] += 1

    nodes = [
        {
            "id": t.name, "name": t.name,
            "symbolSize": 20 + min(occ_count.get(t.id, 0), 20) * 6,
            "definition": t.definition[:60],
        }
        for t in terms
    ]

    # 共现边：同一条款出现过的术语两两连边，宽度=共现条款数
    edge_weight: Counter = Counter()
    for tid_set in article_terms.values():
        ids = sorted(tid_set)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                edge_weight[(ids[i], ids[j])] += 1
    links = [
        {"source": term_by_id[a].name, "target": term_by_id[b].name, "value": w}
        for (a, b), w in edge_weight.items()
    ]
    return {"nodes": nodes, "links": links, "article_labels": article_label}
