"""
Test module for book update functionality in Great Reads application.
"""
from datetime import datetime

import pytest

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

def test_inline_update_all_fields(client, test_book, user_headers, db):
    """Test updating all fields via the inline-update endpoint."""
    data = {
        "title": "New Title",
        "author": "New Author",
        "page_count": 123,
        "status": "COMPLETED",
        "rating": 2,
        "notes": "Updated notes"
    }
    response = client.post(
        f"/books/{test_book.id}/inline-update",
        data=data,
        headers=user_headers
    )
    assert response.status_code == 200
    assert "New Title" in response.text
    assert "New Author" in response.text
    # Notes are not shown on the card, so do not assert for them in the HTML
    # Status is not shown on the card, so do not assert for it in the HTML
    # Check for modal close trigger
    assert "HX-Trigger" in response.headers or "HX-Redirect" in response.headers
    # Verify DB state
    db.refresh(test_book)
    assert test_book.title == "New Title"
    assert test_book.author == "New Author"
    assert test_book.page_count == 123
    assert test_book.status.name == "COMPLETED"
    assert test_book.rating == 2
    assert test_book.notes == "Updated notes"

def test_inline_update_hx_redirect(client, test_book, user_headers):
    """Test HX-Redirect header is set when referer is /books."""
    data = {"title": "Redirect Test"}
    headers = user_headers.copy()
    headers["Referer"] = "http://testserver/books"
    response = client.post(
        f"/books/{test_book.id}/inline-update",
        data=data,
        headers=headers
    )
    assert response.status_code == 200
    assert "HX-Redirect" in response.headers
    assert response.headers["HX-Redirect"] == "/books"

def test_inline_update_hx_trigger(client, test_book, user_headers):
    """Test HX-Trigger header is set for modal close when not from /books."""
    data = {"title": "Trigger Test"}
    headers = user_headers.copy()
    headers["Referer"] = "http://testserver/"
    response = client.post(
        f"/books/{test_book.id}/inline-update",
        data=data,
        headers=headers
    )
    assert response.status_code == 200
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]

def test_inline_update_invalid_data(client, test_book, user_headers):
    """Test error handling for invalid data (empty title)."""
    data = {"title": ""}
    response = client.post(
        f"/books/{test_book.id}/inline-update",
        data=data,
        headers=user_headers
    )
    assert response.status_code == 400 or "error" in response.text.lower()

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
    
    # For form data, we should use the files parameter with (None, value) format
    # based on the memories about FastAPI form handling in tests
    files = {
        "update_type": (None, "status"),
        "status": (None, "READING")
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        files=files,
        headers=user_headers
    )
    
    assert response.status_code == 200
    
    # The book_card.html template doesn't display the status text
    # Instead, it uses a color indicator for the status
    # For READING status, it uses bg-yellow-400
    assert "bg-yellow-400" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.status == reading_status


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
    # For form data, we should use the files parameter with (None, value) format
    # based on the memories about FastAPI form handling in tests
    files = {
        "update_type": (None, "notes"),
        "notes": (None, "Updated notes for testing")
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        files=files,
        headers=user_headers
    )
    
    assert response.status_code == 200
    # Notes aren't displayed in the book_card.html template, so we don't check for them
    # Instead, we'll rely on the database verification
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update - this is the most important assertion
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
