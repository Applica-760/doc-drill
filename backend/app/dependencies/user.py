import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User

MVP_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.get(User, MVP_USER_ID)
    if user is None:
        raise HTTPException(status_code=500, detail="MVP user not found. Run migrations.")
    return user
