"""
Test module for direct database operations related to book updates.
"""
import datetime
import pytest
from sqlalchemy.orm import Session

from app.models import Book, BookStatus


@pytest.fixture
def test_book(db, regular_user):
    """Create a test book for testing updates."""
    now = datetime.datetime.now()
    book = Book(
        title="Test Book",
        author="Test Author",
        status=BookStatus.TO_READ,
        user_id=regular_user.id,
        notes="Test notes",
        rating=None,
        created_at=now,
        updated_at=now
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def test_get_book(db, test_book):
    """Test retrieving a book by ID directly from the database."""
    book = db.query(Book).filter(Book.id == test_book.id).first()
    
    assert book is not None
    assert book.title == "Test Book"
    assert book.author == "Test Author"
    assert book.notes == "Test notes"
    assert book.rating is None


def test_update_book_title(db, test_book):
    """Test updating a book's title directly in the database."""
    # Get the book
    book = db.query(Book).filter(Book.id == test_book.id).first()
    assert book is not None
    
    # Update the title
    book.title = "DB Updated Title"
    db.commit()
    
    # Verify the update
    db.refresh(book)
    assert book.title == "DB Updated Title"


def test_update_book_author(db, test_book):
    """Test updating a book's author directly in the database."""
    # Get the book
    book = db.query(Book).filter(Book.id == test_book.id).first()
    assert book is not None
    
    # Update the author
    book.author = "DB Updated Author"
    db.commit()
    
    # Verify the update
    db.refresh(book)
    assert book.author == "DB Updated Author"


def test_update_book_status(db, test_book):
    """Test updating a book's status directly in the database."""
    # Get the book
    book = db.query(Book).filter(Book.id == test_book.id).first()
    assert book is not None
    
    # Use the BookStatus enum directly
    on_hold_status = BookStatus.ON_HOLD
    
    # Update the status
    book.status = on_hold_status
    db.commit()
    
    # Verify the update
    db.refresh(book)
    assert book.status == on_hold_status
    
    # Verify the enum value
    assert book.status == BookStatus.ON_HOLD


def test_update_book_rating(db, test_book):
    """Test updating a book's rating directly in the database."""
    # Get the book
    book = db.query(Book).filter(Book.id == test_book.id).first()
    assert book is not None
    
    # Update the rating
    book.rating = 1
    db.commit()
    
    # Verify the update
    db.refresh(book)
    assert book.rating == 1
    
    # Test setting rating to None
    book.rating = None
    db.commit()
    
    # Verify the update
    db.refresh(book)
    assert book.rating is None


def test_update_book_notes(db, test_book):
    """Test updating a book's notes directly in the database."""
    # Get the book
    book = db.query(Book).filter(Book.id == test_book.id).first()
    assert book is not None
    
    # Update the notes
    book.notes = "DB updated notes for testing"
    db.commit()
    
    # Verify the update
    db.refresh(book)
    assert book.notes == "DB updated notes for testing"


def test_book_not_found(db):
    """Test handling when a book is not found in the database."""
    # Try to get a non-existent book
    book = db.query(Book).filter(Book.id == 9999).first()
    assert book is None


def test_multiple_updates(db, test_book):
    """Test multiple updates in a single transaction."""
    # Get the book
    book = db.query(Book).filter(Book.id == test_book.id).first()
    assert book is not None
    
    # Use the BookStatus enum directly
    completed_status = BookStatus.COMPLETED
    
    # Update multiple fields
    book.title = "Multiple Updates Title"
    book.author = "Multiple Updates Author"
    book.status = completed_status
    book.rating = 3
    book.notes = "Notes after multiple updates"
    
    # Commit all changes at once
    db.commit()
    
    # Verify all updates
    db.refresh(book)
    assert book.title == "Multiple Updates Title"
    assert book.author == "Multiple Updates Author"
    assert book.status == completed_status
    assert book.rating == 3
    assert book.notes == "Notes after multiple updates"


def test_transaction_rollback(db, test_book):
    """Test transaction rollback when an error occurs."""
    # Get the book
    book = db.query(Book).filter(Book.id == test_book.id).first()
    assert book is not None
    
    # Store original values
    original_title = book.title
    original_author = book.author
    
    try:
        # Update title
        book.title = "Rollback Test Title"
        
        # Simulate an error
        # This will cause an integrity error because status cannot be null
        book.status = None
        
        # Try to commit
        db.commit()
        
        # Should not reach here
        assert False, "Expected an error but none was raised"
    except Exception:
        # Rollback on error
        db.rollback()
    
    # Verify the book was not updated due to rollback
    db.refresh(book)
    assert book.title == original_title
    assert book.author == original_author
