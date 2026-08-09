from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str


class User(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True
