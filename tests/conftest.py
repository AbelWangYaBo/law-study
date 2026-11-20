"""测试夹具：独立临时库 + TestClient。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.database import Base, get_db
from app.main import app

UDI_HTML = "/Volumes/APFS_2/abel/走进先健/医疗器械唯一标识系统规则.html"


@pytest.fixture
def db_session(tmp_path):
    """每个测试独立 SQLite 临时库。"""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db_session):
    """覆盖 get_db 依赖的 TestClient。"""
    def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
