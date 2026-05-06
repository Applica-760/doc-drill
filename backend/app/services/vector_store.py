import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services import embeddings as emb_service


def store_chunks(db: Session, document_id: uuid.UUID, chunks: list[str]) -> None:
    """チャンクをベクトル化してDBに保存する。"""
    vectors = emb_service.embed_batch(chunks)
    db.add_all([
        DocumentChunk(
            document_id=document_id,
            chunk_index=i,
            chunk_text=text,
            embedding=vec,
        )
        for i, (text, vec) in enumerate(zip(chunks, vectors))
    ])
    db.commit()


def search(
    db: Session,
    query: str,
    document_id: uuid.UUID | None = None,
    top_k: int = 10,
) -> list[str]:
    """クエリに類似するチャンクテキストを返す（コサイン距離昇順）。"""
    query_vec = emb_service.embed(query)
    stmt = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
        .limit(top_k)
    )
    if document_id is not None:
        stmt = stmt.where(DocumentChunk.document_id == document_id)
    return [r.chunk_text for r in db.scalars(stmt).all()]
