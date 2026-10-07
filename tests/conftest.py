import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from database import get_db
from main import app


# 每个测试用一个全新的 SQLite 内存库，跑完即销毁，完全不碰 MySQL
@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 内存库要固定在同一个连接上，否则下一次查表会丢
    )
    SQLModel.metadata.create_all(test_engine)  # 在测试库里建表

    # 把接口依赖的 get_db 换成测试库
    def override_get_db():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)  # 不用 with，避免触发连 MySQL 的启动流程

    app.dependency_overrides.clear()
