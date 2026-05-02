import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateLocalDocumentRequest(BaseModel):
    name: str


class DocumentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_name: str
    source_type: str
    s3_key: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
