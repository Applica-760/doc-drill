import os
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.user import MVP_USER_ID
from app.main import app
from app.models.base import Base
from app.models.user import User
# app.main の import チェーン（routers → models）で全モデルが Base.metadata に登録済み

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/doc_drill_test",
)


@pytest.fixture(scope="session")
def test_engine():
    """テスト用DBエンジン。セッション開始時にDBとテーブルを作成し、終了時に削除する。"""
    url = make_url(TEST_DATABASE_URL)

    # デフォルトDB(postgres)に接続してテスト用DBが存在しない場合に作成する
    admin_engine = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": url.database},
        ).fetchone()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin_engine.dispose()

    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)

    # MVP ユーザーをコミット済みで挿入する（ロールバックされない）
    with Session(engine) as session:
        if not session.get(User, MVP_USER_ID):
            session.add(User(id=MVP_USER_ID))
            session.commit()

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """各テスト後にロールバックしてDBを汚染しない。

    outer transaction を張り、Session には join_transaction_mode="create_savepoint" を
    指定することで Session の commit が SAVEPOINT として発行される。
    テスト終了時に outer transaction をロールバックして全変更を取り消す。
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    # NOTE: Session(bind=...) は SA 2.1 で削除予定だが 2.0.x では動作する
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """get_db をテスト用セッションに差し替えた TestClient。"""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def dummy_pdf() -> BytesIO:
    return BytesIO(b"%PDF-1.4 dummy content for testing")


@pytest.fixture
def mock_s3(mocker):
    """app.services.s3._s3 をモックする。"""
    import app.services.s3 as s3_module

    mock = mocker.MagicMock()
    mocker.patch.object(s3_module, "_s3", mock)
    mock.upload_fileobj.return_value = None
    mock.delete_object.return_value = {}
    mock.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"%PDF-1.4 dummy"))
    }
    return mock


@pytest.fixture
def mock_kb_ingest(mocker):
    """knowledge_base.ingest_document をモックする。"""
    return mocker.patch(
        "app.services.knowledge_base.ingest_document",
        return_value=None,
    )
