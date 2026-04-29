import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.user import get_current_user
from app.models.document import Document
from app.models.question import Question
from app.models.user import User
from app.schemas.document import CreateLocalDocumentRequest, DocumentResponse
from app.schemas.question import QuestionImportItem, QuestionResponse
from app.services import knowledge_base, s3

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document_id = uuid.uuid4()
    s3_key = f"documents/{document_id}/{file.filename}"

    s3.upload_file(file, s3_key)

    # KB 登録は失敗してもアップロード自体は成功扱いとする。
    # ローカル環境では bedrock_kb_enabled=false のため kb_document_id は常に None。
    # AWS デプロイ時は ingestionJobId が保存される。
    kb_document_id = knowledge_base.ingest_document(s3_key)

    # NOTE: S3アップロード成功後にDB書き込みが失敗すると、S3にファイルだけ残る孤立データが生まれる。
    # MVPでは許容するが、本番化の際はトランザクション補償（S3ロールバック or 定期クリーンアップ）が必要。
    document = Document(
        id=document_id,
        user_id=current_user.id,
        file_name=file.filename,
        s3_key=s3_key,
        kb_document_id=kb_document_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
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
        kb_document_id=None,
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
    # NOTE: S3 から削除しても KB のベクトルデータは残る。
    # AWS デプロイ時は削除後に start_ingestion_job を呼んで再 sync しないと、
    # 削除済み資料の内容が問題生成に混入するリスクがある。MVPでは許容する。
    db.delete(document)
    db.commit()
