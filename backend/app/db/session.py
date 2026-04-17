from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI の Depends() 経由でセッションを注入するジェネレータ。
    リクエスト単位でセッションを生成し、終了時に必ずクローズする。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
