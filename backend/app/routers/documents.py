import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.dependencies.user import get_current_user
from app.models.document import Document
from app.models.question import Question
from app.models.user import User
from app.schemas.document import CreateLocalDocumentRequest, DocumentResponse
from app.schemas.question import QuestionImportItem, QuestionResponse
from app.services import pdf_parser, s3, vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


def _ingest_to_rag(document_id: uuid.UUID, s3_key: str) -> None:
    """アップロード完了後にバックグラウンドでRAGパイプラインを実行する。

    BackgroundTasks はリクエストセッションが閉じた後に動くため、独自セッションを使う。
    エラーが発生してもレスポンス済みのため例外は握り潰してログに残す。
    """
    try:
        pdf_bytes = s3.get_file_bytes(s3_key)
        chunks = pdf_parser.extract_chunks(pdf_bytes)
        with SessionLocal() as db:
            vector_store.store_chunks(db, document_id, chunks)
        logger.info("RAG ingestion complete: document_id=%s chunks=%d", document_id, len(chunks))
    except Exception:
        logger.exception("RAG ingestion failed: document_id=%s", document_id)


@router.post("", response_model=DocumentResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document_id = uuid.uuid4()
    s3_key = f"documents/{document_id}/{file.filename}"

    s3.upload_file(file, s3_key)

    document = Document(
        id=document_id,
        user_id=current_user.id,
        file_name=file.filename,
        s3_key=s3_key,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(_ingest_to_rag, document.id, s3_key)

    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Document).filter(Document.user_id == current_user.id).all()


@router.post("/local", response_model=DocumentResponse, status_code=201)
def create_local_document(
    req: CreateLocalDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = Document(
        user_id=current_user.id,
        file_name=req.name,
        source_type="local",
        s3_key=None,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/{document_id}/questions/import", response_model=list[QuestionResponse], status_code=201)
def import_questions(
    document_id: uuid.UUID,
    items: list[QuestionImportItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.source_type != "local":
        raise HTTPException(status_code=400, detail="このエンドポイントはローカル問題セット専用です")

    questions = [
        Question(
            document_id=document.id,
            question_type=item.question_type,
            body=item.body,
            answer=item.answer,
            explanation=item.explanation,
            options=item.options,
        )
        for item in items
    ]
    db.add_all(questions)
    db.commit()
    for q in questions:
        db.refresh(q)
    return questions


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.s3_key is not None:
        s3.delete_file(document.s3_key)
    # document_chunks は ON DELETE CASCADE で自動削除される
    db.delete(document)
    db.commit()
