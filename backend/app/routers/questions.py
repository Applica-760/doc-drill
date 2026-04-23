import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.user import get_current_user
from app.models.document import Document
from app.models.question import Question
from app.models.user import User
from app.schemas.question import GenerateQuestionsRequest, QuestionResponse
from app.services import bedrock, knowledge_base
from app.core.config import settings

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("/generate", response_model=list[QuestionResponse], status_code=201)
def generate_questions(
    req: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(Document.id == req.document_id, Document.user_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if settings.bedrock_kb_enabled and document.kb_document_id:
        status = knowledge_base.get_ingestion_status(document.kb_document_id)
        if status != knowledge_base.INGESTION_COMPLETE:
            raise HTTPException(
                status_code=409,
                detail=f"資料のインデックス化が完了していません（状態: {status}）。1〜2分後に再試行してください。",
            )

    try:
        raw_questions = bedrock.generate_questions(document, req.count)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    questions = [
        Question(
            document_id=document.id,
            question_type="short_answer",
            body=q["body"],
            answer=q["answer"],
            explanation=q["explanation"],
        )
        for q in raw_questions
    ]
    db.add_all(questions)
    db.commit()
    for q in questions:
        db.refresh(q)

    return questions


@router.get("", response_model=list[QuestionResponse])
def list_questions(
    document_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Question)
        .join(Document, Question.document_id == Document.id)
        .filter(Document.user_id == current_user.id)
    )
    if document_id is not None:
        query = query.filter(Question.document_id == document_id)
    return query.all()


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = (
        db.query(Question)
        .join(Document, Question.document_id == Document.id)
        .filter(Question.id == question_id, Document.user_id == current_user.id)
        .first()
    )
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question
