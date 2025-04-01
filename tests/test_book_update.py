"""
Test module for book update functionality in Great Reads application.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Book, BookStatus


@pytest.fixture
def test_book(db, regular_user):
    """Create a test book for testing updates."""
    book = Book(
        title="Test Book",
        author="Test Author",
        status=BookStatus.TO_READ,
        user_id=regular_user.id,
        notes="Test notes",
        rating=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def test_get_book(client, test_book, user_headers):
    """Test retrieving a book by ID."""
    response = client.get(f"/books/{test_book.id}", headers=user_headers)
    assert response.status_code == 200
    assert "Test Book" in response.text
    assert "Test Author" in response.text


def test_update_book_title(client, test_book, user_headers):
    """Test updating a book's title."""
    data = {
        "update_type": "title",
        "title": "Updated Title"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=user_headers
    )
    
    assert response.status_code == 200
    assert "Updated Title" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]


def test_update_book_author(client, test_book, user_headers):
    """Test updating a book's author."""
    data = {
        "update_type": "author",
        "author": "Updated Author"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=user_headers
    )
    
    assert response.status_code == 200
    assert "Updated Author" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]


def test_update_book_status(client, test_book, user_headers, db):
    """Test updating a book's status."""
    # Use the BookStatus enum directly
    reading_status = BookStatus.READING
    
    data = {
        "update_type": "status",
        "status": "READING"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=user_headers
    )
    
    assert response.status_code == 200
    assert "READING" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.status_id == reading_status.id


def test_update_book_rating(client, test_book, user_headers, db):
    """Test updating a book's rating."""
    data = {
        "update_type": "rating",
        "rating": "2"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=user_headers
    )
    
    assert response.status_code == 200
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.rating == 2


def test_update_book_notes(client, test_book, user_headers, db):
    """Test updating a book's notes."""
    data = {
        "update_type": "notes",
        "notes": "Updated notes for testing"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=user_headers
    )
    
    assert response.status_code == 200
    assert "Updated notes for testing" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.notes == "Updated notes for testing"


def test_book_not_found(client, user_headers):
    """Test error handling when book is not found."""
    data = {
        "update_type": "title",
        "title": "Updated Title"
    }
    
    response = client.post(
        "/books/9999/inline-update", 
        data=data,
        headers=user_headers
    )
    
    assert response.status_code == 404
    assert "Book not found" in response.text


def test_unauthorized_access(client, test_book, moderator_headers, db):
    """Test unauthorized access to update a book."""
    # Ensure the book belongs to regular_user, not moderator
    from app.models import User
    moderator = db.query(User).filter(User.role == "moderator").first()
    assert test_book.user_id != moderator.id
    
    data = {
        "update_type": "title",
        "title": "Unauthorized Update"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=moderator_headers
    )
    
    # Should return 403 Forbidden if the user doesn't have permission
    # or 404 Not Found if the app hides the existence of the book
    assert response.status_code in [403, 404]
