"""Book management routes for the book tracking app."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi import status as http_status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from . import models, auth, roles
from .database import get_db
from .schemas import Book, BookCreate, BookUpdate
from .roles import requires_permission

router = APIRouter(
    prefix="/books",
    tags=["books"],
    responses={404: {"description": "Not found"}},
)


def get_templates(request: Request):
    """Get templates from app state."""
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse)
async def list_books(
    request: Request,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """List all books for the current user."""
    query = db.query(models.Book)

    # Filter by user unless they have permission to view all books
    if not roles.has_permission(current_user, "view_all_books"):
        query = query.filter(models.Book.user_id == current_user.id)

    # Apply status filter if provided
    if status_filter:
        try:
            book_status = models.BookStatus[status_filter]
            query = query.filter(models.Book.status == book_status)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status filter")

    books = query.order_by(desc(models.Book.created_at)).all()

    templates = get_templates(request)
    return templates.TemplateResponse(
        "books/list.html",
        {
            "request": request,
            "current_user": current_user,
            "books": books,
            "status_filter": status_filter,
            "statuses": [status for status in models.BookStatus],
        },
    )


@router.get("/new", response_class=HTMLResponse)
@requires_permission("manage_own_books")
async def new_book_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Show form to create a new book."""
    templates = get_templates(request)
    return templates.TemplateResponse(
        "books/form.html",
        {
            "request": request,
            "current_user": current_user,
            "book": None,
            "statuses": [status for status in models.BookStatus],
            "is_new": True,
        },
    )


@router.post("/")
@requires_permission("manage_own_books")
async def create_book(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
    title: str = Form(...),
    author: str = Form(...),
    status: str = Form(...),
    notes: Optional[str] = Form(None),
    rating: Optional[str] = Form(None),
):
    """Create a new book."""
    # Validate status
    try:
        book_status = models.BookStatus[status.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid status")

    # Handle rating
    parsed_rating = None
    if rating is not None and rating != "null":
        try:
            parsed_rating = int(rating)
            if not 0 <= parsed_rating <= 3:
                raise HTTPException(
                    status_code=400, detail="Rating must be between 0 and 3"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Rating must be a valid integer between 0 and 3"
            )

    # Create book
    now = datetime.utcnow()
    book = models.Book(
        title=title,
        author=author,
        status=book_status,
        notes=notes,
        rating=parsed_rating,
        user_id=current_user.id,
        created_at=now,
        updated_at=now,
        start_date=now if book_status == models.BookStatus.READING else None,
        completion_date=now if book_status == models.BookStatus.COMPLETED else None,
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    return RedirectResponse(
        url="/books",
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


@router.get("/{book_id}/edit", response_class=HTMLResponse)
@requires_permission("manage_own_books")
async def edit_book_form(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Show form to edit a book."""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if user has permission to edit this book
    if book.user_id != current_user.id and not auth.has_permission(
        current_user, "manage_all_books"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to edit this book")

    templates = get_templates(request)
    return templates.TemplateResponse(
        "books/form.html",
        {
            "request": request,
            "current_user": current_user,
            "book": book,
            "statuses": [status for status in models.BookStatus],
            "is_new": False,
        },
    )


@router.put("/{book_id}")
@requires_permission("manage_own_books")
async def update_book(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
    title: str = Form(...),
    author: str = Form(...),
    status: str = Form(...),
    notes: Optional[str] = Form(None),
    rating: Optional[str] = Form(None),
):
    """Update a book's information."""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if user has permission to edit this book
    if book.user_id != current_user.id and not auth.has_permission(
        current_user, "manage_all_books"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to edit this book")

    # Validate status
    try:
        new_status = models.BookStatus[status.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid status")

    # Handle rating
    parsed_rating = None
    if rating is not None and rating != "null":
        try:
            parsed_rating = int(rating)
            if not 0 <= parsed_rating <= 3:
                raise HTTPException(
                    status_code=400, detail="Rating must be between 0 and 3"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Rating must be a valid integer between 0 and 3"
            )

    # Update start_date if status changes to READING
    if (
        new_status == models.BookStatus.READING
        and book.status != models.BookStatus.READING
    ):
        book.start_date = datetime.utcnow()

    # Update completion_date if status changes to COMPLETED
    if (
        new_status == models.BookStatus.COMPLETED
        and book.status != models.BookStatus.COMPLETED
    ):
        book.completion_date = datetime.utcnow()

    # Update book
    book.title = title
    book.author = author
    book.status = new_status
    book.notes = notes
    book.rating = parsed_rating
    book.updated_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(
        url="/books",
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


@router.delete("/{book_id}")
@requires_permission("manage_own_books")
async def delete_book(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Delete a book."""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if user has permission to delete this book
    if book.user_id != current_user.id and not auth.has_permission(
        current_user, "manage_all_books"
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this book"
        )

    db.delete(book)
    db.commit()

    return {"success": True}
