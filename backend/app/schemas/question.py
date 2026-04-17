import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── 問題生成リクエスト ──────────────────────────────────────────────────────

class GenerateQuestionsRequest(BaseModel):
    document_id: uuid.UUID
    count: int = Field(default=5, ge=1, le=20)


# ── 問題形式（discriminated union で将来の形式追加に対応） ─────────────────

class ShortAnswerQuestion(BaseModel):
    """短答式問題。MVPで実装する唯一の形式。"""
    question_type: Literal["short_answer"]
    body: str
    answer: str
    explanation: str
    options: None = None


# 将来の拡張例（実装時にここに追加する）:
# class MultipleChoiceQuestion(BaseModel):
#     question_type: Literal["multiple_choice"]
#     body: str
#     answer: str        # 正解の選択肢ラベル
#     explanation: str
#     options: dict      # {"choices": ["A. ...", "B. ...", "C. ...", "D. ..."]}

QuestionDetail = Annotated[
    ShortAnswerQuestion,
    # | MultipleChoiceQuestion,  # 追加時はここに足す
    Field(discriminator="question_type"),
]


# ── DBレコードのレスポンス ──────────────────────────────────────────────────

class QuestionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    question_type: str
    body: str
    answer: str
    explanation: str
    options: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
