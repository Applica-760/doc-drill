import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_name: str
    s3_key: str
    kb_document_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
