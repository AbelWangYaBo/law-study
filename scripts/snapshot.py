"""导出静态快照：把数据库内容按前端所需 API 形态导出为 JSON。

用于 GitHub Pages 等纯静态托管：前端检测不到后端时自动回退读取快照（只读模式）。
生成位置 web/public/api-snapshot/，随 vite build 一并拷入 dist。

用法: uv run python scripts/snapshot.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.main import app

OUT_DIR = Path(__file__).resolve().parent.parent / "web" / "public" / "api-snapshot"


def main() -> None:
    client = TestClient(app)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def dump(name: str, data) -> None:
        path = OUT_DIR / f"{name}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {path.name}  ({path.stat().st_size} bytes)")

    laws = client.get("/api/laws").json()
    if not laws:
        raise SystemExit("数据库为空，请先导入法规：uv run python scripts/import_law.py <法规.html|md>")
    dump("laws", laws)
    for law in laws:
        law_id = law["id"]
        dump(f"law-{law_id}", client.get(f"/api/laws/{law_id}").json())
        dump(f"law-{law_id}-terms", client.get(f"/api/laws/{law_id}/terms").json())
        dump(f"law-{law_id}-readings", client.get(f"/api/laws/{law_id}/readings").json())
        dump(f"graph-term-graph-{law_id}", client.get(f"/api/graph/term-graph?law_id={law_id}").json())
    dump("graph-law-tree", client.get("/api/graph/law-tree").json())
    dump("graph-relations", client.get("/api/graph/relations").json())
    print(f"快照导出完成：{len(laws)} 部法规 → {OUT_DIR}")


if __name__ == "__main__":
    main()
