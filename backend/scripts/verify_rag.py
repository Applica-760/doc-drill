"""
RAGパイプライン動作確認スクリプト。

コンテナ内で実行:
  docker compose exec backend uv run python scripts/verify_rag.py

前提: alembic upgrade head 済み、BEDROCK_AWS_ACCESS_KEY_ID 設定済み
"""
import uuid

from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.document import Document
from app.models.user import User
from app.services import pdf_parser, vector_store

SAMPLE_TEXT = (
    "pgvectorはPostgreSQLの拡張機能で、ベクトルデータ型と類似検索インデックスを提供する。"
    "HNSWインデックスはANN（近似最近傍）検索に優れており、高次元ベクトルでも高速に動作する。"
    "Bedrock Titan Embed Text v2は1024次元の埋め込みベクトルを生成できる。"
    "RAGパイプラインは、PDF解析 → チャンク分割 → 埋め込み生成 → ベクトルDB保存 → 類似検索の順で動作する。"  # noqa: E501
    "FastAPIのBackgroundTasksを使うと、レスポンスを返した後に非同期でバックグラウンド処理を実行できる。"
) * 4  # 約1100文字 → 複数チャンクに分割されることを確認

_DUMMY_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def main():
    with Session(engine) as db:
        # ダミーユーザー・ドキュメントをセットアップ
        if not db.get(User, _DUMMY_USER_ID):
            db.add(User(id=_DUMMY_USER_ID))
            db.commit()

        doc = Document(
            user_id=_DUMMY_USER_ID,
            file_name="verify_rag_test.pdf",
            source_type="local",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # チャンク分割
        chunks = pdf_parser._split(SAMPLE_TEXT)
        print(f"[1] チャンク数: {len(chunks)}, 先頭チャンク長: {len(chunks[0])}")

        # 埋め込み生成 + 保存
        print("[2] 埋め込み生成・保存中...")
        vector_store.store_chunks(db, doc.id, chunks)
        print("[2] 完了")

        # 類似検索
        print("[3] 類似検索: 'HNSWインデックスとは'")
        results = vector_store.search(db, "HNSWインデックスとは", top_k=3)
        for i, r in enumerate(results):
            print(f"  [{i}] {r[:80]}...")

        # クリーンアップ
        db.delete(doc)
        db.commit()
        print("[完了] パイプライン動作確認 OK")


if __name__ == "__main__":
    main()
