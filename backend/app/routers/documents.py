import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.user import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services import s3

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

    # NOTE: S3アップロード成功後にDB書き込みが失敗すると、S3にファイルだけ残る孤立データが生まれる。
    # MVPでは許容するが、本番化の際はトランザクション補償（S3ロールバック or 定期クリーンアップ）が必要。
    document = Document(
        id=document_id,
        user_id=current_user.id,
        file_name=file.filename,
        s3_key=s3_key,
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

    s3.delete_file(document.s3_key)
    db.delete(document)
    db.commit()
