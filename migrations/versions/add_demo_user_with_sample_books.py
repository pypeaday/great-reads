"""add_demo_user_with_sample_books

Revision ID: 4f8e9c2d7a5b
Revises: 26becd0618c3
Create Date: 2025-03-31 09:42:37.000000

"""

import enum
import random
from collections.abc import Sequence
from datetime import datetime
from datetime import timedelta

from alembic import op
from passlib.context import CryptContext
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision: str = "4f8e9c2d7a5b"
down_revision: str | None = "26becd0618c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Hash a password for storing."""
    return pwd_context.hash(password)

# Define models for use in the migration
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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    last_login = Column(DateTime)
    theme_preference = Column(String(50), default="gruvbox-dark")
    role = Column(String(20), ForeignKey("roles.name"), default="user", nullable=False)

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    status = Column(SQLEnum(BookStatus), nullable=False, default=BookStatus.TO_READ)
    notes = Column(Text)
    start_date = Column(DateTime)
    completion_date = Column(DateTime)
    rating = Column(Integer)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

# Sample book data
SAMPLE_BOOKS = [
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"title": "1984", "author": "George Orwell"},
    {"title": "Pride and Prejudice", "author": "Jane Austen"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien"},
    {"title": "Brave New World", "author": "Aldous Huxley"},
    {"title": "The Lord of the Rings", "author": "J.R.R. Tolkien"},
    {"title": "Animal Farm", "author": "George Orwell"},
    {"title": "The Alchemist", "author": "Paulo Coelho"},
    {"title": "The Hunger Games", "author": "Suzanne Collins"},
    {"title": "Harry Potter and the Philosopher's Stone", "author": "J.K. Rowling"},
    {"title": "The Shining", "author": "Stephen King"},
    {"title": "The Da Vinci Code", "author": "Dan Brown"},
    {"title": "The Road", "author": "Cormac McCarthy"},
    {"title": "Dune", "author": "Frank Herbert"},
    {"title": "The Handmaid's Tale", "author": "Margaret Atwood"},
    {"title": "The Martian", "author": "Andy Weir"},
    {"title": "Gone Girl", "author": "Gillian Flynn"},
    {"title": "The Silent Patient", "author": "Alex Michaelides"},
    {"title": "Where the Crawdads Sing", "author": "Delia Owens"},
    {"title": "The Night Circus", "author": "Erin Morgenstern"},
    {"title": "The Kite Runner", "author": "Khaled Hosseini"},
    {"title": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson"},
    {"title": "The Book Thief", "author": "Markus Zusak"},
    {"title": "Sapiens: A Brief History of Humankind", "author": "Yuval Noah Harari"},
    {"title": "Educated", "author": "Tara Westover"},
    {"title": "Becoming", "author": "Michelle Obama"},
    {"title": "The Power of Habit", "author": "Charles Duhigg"},
    {"title": "Atomic Habits", "author": "James Clear"},
    {"title": "The Midnight Library", "author": "Matt Haig"},
    {"title": "Project Hail Mary", "author": "Andy Weir"},
    {"title": "The Seven Husbands of Evelyn Hugo", "author": "Taylor Jenkins Reid"},
    {"title": "The Invisible Life of Addie LaRue", "author": "V.E. Schwab"},
    {"title": "Circe", "author": "Madeline Miller"},
    {"title": "The Song of Achilles", "author": "Madeline Miller"},
    {"title": "Normal People", "author": "Sally Rooney"},
    {"title": "The Thursday Murder Club", "author": "Richard Osman"},
    {"title": "Klara and the Sun", "author": "Kazuo Ishiguro"},
    {"title": "The Vanishing Half", "author": "Brit Bennett"},
    {"title": "A Gentleman in Moscow", "author": "Amor Towles"},
    {"title": "The Lincoln Highway", "author": "Amor Towles"},
    {"title": "The Four Winds", "author": "Kristin Hannah"},
    {"title": "The Nightingale", "author": "Kristin Hannah"},
    {"title": "The Overstory", "author": "Richard Powers"},
    {"title": "Hamnet", "author": "Maggie O'Farrell"},
    {"title": "The House in the Cerulean Sea", "author": "TJ Klune"},
    {"title": "Pachinko", "author": "Min Jin Lee"},
    {"title": "The Fifth Season", "author": "N.K. Jemisin"},
    {"title": "The Three-Body Problem", "author": "Liu Cixin"},
    {"title": "Exhalation", "author": "Ted Chiang"},
    {"title": "Children of Time", "author": "Adrian Tchaikovsky"},
    {"title": "The Priory of the Orange Tree", "author": "Samantha Shannon"},
    {"title": "The City We Became", "author": "N.K. Jemisin"},
    {"title": "Mexican Gothic", "author": "Silvia Moreno-Garcia"},
    {"title": "The Starless Sea", "author": "Erin Morgenstern"},
    {"title": "The Water Dancer", "author": "Ta-Nehisi Coates"},
    {"title": "On Earth We're Briefly Gorgeous", "author": "Ocean Vuong"},
    {"title": "The Dutch House", "author": "Ann Patchett"},
    {"title": "The Testaments", "author": "Margaret Atwood"},
    {"title": "The Nickel Boys", "author": "Colson Whitehead"}
]

# Sample notes
SAMPLE_NOTES = [
    "Really enjoyed this one!",
    "A bit slow at the beginning, but gets better.",
    "One of my all-time favorites.",
    "Interesting premise, but the execution could be better.",
    "The characters felt very real and relatable.",
    "Beautiful prose, but the plot was lacking.",
    "Couldn't put it down!",
    "A thought-provoking read.",
    "The ending was unexpected.",
    "Would definitely recommend to others.",
    "Not my cup of tea, but I can see why others might like it.",
    "The world-building was incredible.",
    "I learned a lot from this book.",
    "A perfect summer read.",
    "I'll be thinking about this one for a while.",
    "",  # Empty notes for some books
]

def upgrade() -> None:
    # Get a database connection
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # Ensure the user role exists
        user_role = session.query(Role).filter(Role.name == "user").first()
        if not user_role:
            # Create user role if it doesn't exist
            user_role = Role(
                name="user",
                description="Regular user with standard permissions",
                permissions="{}",
                created_at=datetime.utcnow()
            )
            session.add(user_role)
            session.flush()
            print("Created 'user' role")

        # Check if demo user already exists
        demo_email = "demo@example.com"
        demo_user = session.query(User).filter(User.email == demo_email).first()

        # If demo user exists, delete all their books to reset
        if demo_user:
            print(f"Demo user exists: {demo_email} - Resetting books")
            # Count books before deletion
            book_count = session.query(Book).filter(Book.user_id == demo_user.id).count()
            # Delete all books for the demo user
            session.query(Book).filter(Book.user_id == demo_user.id).delete()
            session.flush()
            print(f"Deleted {book_count} existing books for demo user")
        else:

            # Create new demo user
            demo_user = User(
                email=demo_email,
                name="Demo User",
                hashed_password=get_password_hash("demo"),
                is_active=True,
                role="user",
                created_at=datetime.utcnow(),
                theme_preference="gruvbox-dark"
            )

            session.add(demo_user)
            session.flush()  # Flush to get the user ID

            print(f"Created demo user: {demo_user.email}")

        # Current time for reference
        now = datetime.utcnow()

        # Add 50 random books to the demo user
        selected_books = random.sample(SAMPLE_BOOKS, 50)

        for book_data in selected_books:
            # Weighted selection for status - make COMPLETED more common
            status_weights = {
                BookStatus.COMPLETED: 0.6,  # 60% chance for COMPLETED
                BookStatus.READING: 0.15,   # 15% chance for READING
                BookStatus.TO_READ: 0.1,    # 10% chance for TO_READ
                BookStatus.ON_HOLD: 0.1,    # 10% chance for ON_HOLD
                BookStatus.DNF: 0.05        # 5% chance for DNF
            }
            status = random.choices(
                population=list(status_weights.keys()),
                weights=list(status_weights.values()),
                k=1
            )[0]

            # Set appropriate dates based on status
            start_date = None
            completion_date = None

            if status in [BookStatus.READING, BookStatus.COMPLETED, BookStatus.DNF, BookStatus.ON_HOLD]:
                # For books that have been started, set a start date in the past
                days_ago = random.randint(10, 365)
                start_date = now - timedelta(days=days_ago)

            if status in [BookStatus.COMPLETED, BookStatus.DNF]:
                # For completed or DNF books, set a completion date after the start date
                if start_date:
                    days_to_complete = random.randint(1, min(days_ago, 60))
                    completion_date = start_date + timedelta(days=days_to_complete)

            # Set rating based on status
            rating = None
            if status == BookStatus.COMPLETED:
                # 0-5 rating for completed books with a distribution
                # favoring higher ratings
                # Weights for ratings 0-5
                rating_weights = [0.05, 0.1, 0.15, 0.25, 0.25, 0.2]
                rating = random.choices(
                    population=range(6),
                    weights=rating_weights,
                    k=1
                )[0]

            # Random notes
            notes = random.choice(SAMPLE_NOTES) if random.random() > 0.3 else None

            # Create the book
            book = Book(
                title=book_data["title"],
                author=book_data["author"],
                status=status,
                notes=notes,
                start_date=start_date,
                completion_date=completion_date,
                rating=rating,
                user_id=demo_user.id,
                created_at=now - timedelta(days=random.randint(1, 400)),
                updated_at=now - timedelta(days=random.randint(0, 30))
            )

            session.add(book)
            print(f"Added book: {book.title} by {book.author}")

        # Commit all changes
        session.commit()
        print("Successfully added demo user with 50 sample books")

    except Exception as e:
        session.rollback()
        print(f"Error in migration: {e}")
        raise
    finally:
        session.close()


def downgrade() -> None:
    # Get a database connection
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # Find the demo user
        demo_email = "demo@example.com"
        demo_user = session.query(User).filter(User.email == demo_email).first()

        if demo_user:
            # Delete all books associated with the demo user
            books = session.query(Book).filter(Book.user_id == demo_user.id).all()
            for book in books:
                session.delete(book)

            # Delete the demo user
            session.delete(demo_user)
            session.commit()
            print(f"Removed demo user and associated books: {demo_email}")
        else:
            print(f"Demo user not found: {demo_email}")

    except Exception as e:
        session.rollback()
        print(f"Error in migration downgrade: {e}")
        raise
    finally:
        session.close()
