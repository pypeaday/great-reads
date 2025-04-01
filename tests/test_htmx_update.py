"""
Test module for HTMX-based book update functionality in Great Reads application.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Book, BookStatus


@pytest.fixture
def test_book(db, regular_user):
    """Create a test book for testing updates."""
    book = Book(
        title="Test Book",
        author="Test Author",
        status_id=1,  # Assuming TO_READ is id 1
        user_id=regular_user.id,
        notes="Test notes",
        rating=None
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@pytest.fixture
def htmx_headers(user_headers):
    """Create headers for HTMX requests."""
    headers = user_headers.copy()
    headers.update({
        "HX-Request": "true",
        "HX-Trigger": "none",
        "Content-Type": "application/x-www-form-urlencoded"
    })
    return headers


def test_htmx_update_title(client, test_book, htmx_headers, db):
    """Test updating a book's title via HTMX."""
    htmx_headers["HX-Target"] = f"book-{test_book.id}"
    
    data = {
        "update_type": "title",
        "title": "HTMX Updated Title"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=htmx_headers
    )
    
    assert response.status_code == 200
    assert "HTMX Updated Title" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.title == "HTMX Updated Title"


def test_htmx_update_author(client, test_book, htmx_headers, db):
    """Test updating a book's author via HTMX."""
    htmx_headers["HX-Target"] = f"book-{test_book.id}"
    
    data = {
        "update_type": "author",
        "author": "HTMX Updated Author"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=htmx_headers
    )
    
    assert response.status_code == 200
    assert "HTMX Updated Author" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.author == "HTMX Updated Author"


def test_htmx_update_status(client, test_book, htmx_headers, db):
    """Test updating a book's status via HTMX."""
    htmx_headers["HX-Target"] = f"book-{test_book.id}"
    
    # Get the COMPLETED status ID
    completed_status = db.query(BookStatus).filter(BookStatus.name == "COMPLETED").first()
    assert completed_status is not None
    
    data = {
        "update_type": "status",
        "status": "COMPLETED"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=htmx_headers
    )
    
    assert response.status_code == 200
    assert "COMPLETED" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.status_id == completed_status.id


def test_htmx_update_rating(client, test_book, htmx_headers, db):
    """Test updating a book's rating via HTMX."""
    htmx_headers["HX-Target"] = f"book-{test_book.id}"
    
    data = {
        "update_type": "rating",
        "rating": "3"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=htmx_headers
    )
    
    assert response.status_code == 200
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.rating == 3


def test_htmx_update_notes(client, test_book, htmx_headers, db):
    """Test updating a book's notes via HTMX."""
    htmx_headers["HX-Target"] = f"book-{test_book.id}"
    
    data = {
        "update_type": "notes",
        "notes": "HTMX updated notes for testing"
    }
    
    response = client.post(
        f"/books/{test_book.id}/inline-update", 
        data=data,
        headers=htmx_headers
    )
    
    assert response.status_code == 200
    assert "HTMX updated notes for testing" in response.text
    
    # Verify the HX-Trigger header for closing modal
    assert "HX-Trigger" in response.headers
    assert "closeModal" in response.headers["HX-Trigger"]
    
    # Verify the database update
    db.refresh(test_book)
    assert test_book.notes == "HTMX updated notes for testing"


def test_htmx_book_modal(client, test_book, htmx_headers):
    """Test the book modal endpoint with HTMX."""
    htmx_headers["HX-Target"] = "modal-container"
    
    response = client.get(
        f"/books/{test_book.id}/modal", 
        headers=htmx_headers
    )
    
    assert response.status_code == 200
    assert test_book.title in response.text
    assert test_book.author in response.text
    assert "book-modal-form" in response.text  # Check for the form element
    
    # Check for form fields
    assert 'name="title"' in response.text
    assert 'name="author"' in response.text
    assert 'name="status"' in response.text
    assert 'name="notes"' in response.text
    assert 'name="rating"' in response.text
