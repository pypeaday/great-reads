from pydantic import BaseModel, EmailStr, Field, conint
from typing import Optional
from datetime import datetime
from .models import BookStatus


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None
    status: BookStatus = Field(default=BookStatus.TO_READ)
    rating: Optional[conint(ge=0, le=3)] = None  # Rating from 0-3


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[BookStatus] = None
    rating: Optional[conint(ge=0, le=3)] = None


class Book(BookBase):
    id: int
    user_id: int
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    email: Optional[str] = None
