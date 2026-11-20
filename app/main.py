"""FastAPI 入口：API 路由 + 前端静态托管（web/dist）。"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR
from .routers import ai, graph, laws, practice

app = FastAPI(title="法规学习系统")

app.include_router(laws.router)
app.include_router(practice.router)
app.include_router(graph.router)
app.include_router(ai.router)

# 前端构建产物托管（开发时由 vite dev server 提供）
_dist = BASE_DIR / "web" / "dist"
if _dist.is_dir():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        """前端 SPA 兜底：静态文件命中则返回，否则回 index.html。"""
        candidate = _dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_dist / "index.html")
