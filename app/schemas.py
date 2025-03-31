from datetime import datetime

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
from pydantic import conint

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
    email: str | None = None


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    notes: str | None = None
    status: BookStatus = Field(default=BookStatus.TO_READ)
    rating: conint(ge=0, le=3) | None = None  # Rating from 0-3


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    title: str | None = Field(None, min_length=1, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    status: BookStatus | None = None
    rating: conint(ge=0, le=3) | None = None


class Book(BookBase):
    id: int
    user_id: int
    start_date: datetime | None = None
    completion_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    email: str | None = None
