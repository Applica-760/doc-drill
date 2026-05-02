import uuid

from pgvector.sqlalchemy import Vector
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


def search(db: Session, query: str, top_k: int = 10) -> list[str]:
    """クエリに類似するチャンクテキストを返す（コサイン距離昇順）。"""
    query_vec = emb_service.embed(query)
    rows = db.scalars(
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
        .limit(top_k)
    ).all()
    return [r.chunk_text for r in rows]
