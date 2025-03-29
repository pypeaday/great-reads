from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class BookStatus(enum.Enum):
    TO_READ = "To Read"
    READING = "Currently Reading"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    DNF = "Did Not Finish"


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    permissions = Column(Text)  # JSON string of permissions
    created_at = Column(DateTime, nullable=False)

    # Relationships
    users = relationship("User", back_populates="role_info")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))  # Full name
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    last_login = Column(DateTime)
    role = Column(
        String(20), ForeignKey("roles.name"), default="user", nullable=False
    )  # References role.name

    # Relationships
    books = relationship("Book", back_populates="user")
    role_info = relationship("Role", back_populates="users")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    status = Column(SQLEnum(BookStatus), nullable=False, default=BookStatus.TO_READ)
    notes = Column(Text)
    start_date = Column(DateTime)
    completion_date = Column(DateTime)
    rating = Column(Integer)  # 0-3 rating system
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="books")
