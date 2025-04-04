"""Book management routes for the book tracking app."""

from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import HTTPException
from fastapi import Request
from fastapi import status as http_status
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import auth
from . import models
from . import roles
from .database import get_db
from .roles import requires_permission

router = APIRouter(
    prefix="/books",
    tags=["books"],
    responses={404: {"description": "Not found"}},
)


def get_templates(request: Request):
    """Get templates from app state."""
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse, response_model=None)
async def list_books(
    request: Request,
    status_filter: str | None = None,
    title_filter: str | None = None,
    author_filter: str | None = None,
    notes_filter: str | None = None,
    rating_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """List all books for the current user with optional filtering."""

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
            raise HTTPException(
                status_code=400, detail="Invalid status filter"
            ) from None

    # Apply title filter if provided
    if title_filter:
        query = query.filter(models.Book.title.ilike(f"%{title_filter}%"))

    # Apply author filter if provided
    if author_filter:
        query = query.filter(models.Book.author.ilike(f"%{author_filter}%"))

    # Apply notes filter if provided
    if notes_filter:
        query = query.filter(models.Book.notes.ilike(f"%{notes_filter}%"))

    # Apply rating filter if provided
    if rating_filter and rating_filter.isdigit():
        rating = int(rating_filter)
        if 0 <= rating <= 3:  # Ensure rating is within valid range
            query = query.filter(models.Book.rating == rating)

    books = query.order_by(desc(models.Book.created_at)).all()

    templates = get_templates(request)
    return templates.TemplateResponse(
        "books/list.html",
        {
            "request": request,
            "current_user": current_user,
            "books": books,
            "status_filter": status_filter,
            "title_filter": title_filter,
            "author_filter": author_filter,
            "notes_filter": notes_filter,
            "rating_filter": rating_filter,
            "statuses": list(models.BookStatus),
        },
    )


@router.get("/new", response_class=HTMLResponse, response_model=None)
@requires_permission("manage_own_books")
async def new_book_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Show form to create a new book."""
    if db is None:
        db = get_db()
    if current_user is None:
        current_user = auth.get_current_active_user()

    templates = get_templates(request)
    return templates.TemplateResponse(
        "books/form.html",
        {
            "request": request,
            "current_user": current_user,
            "book": None,
            "statuses": list(models.BookStatus),
            "is_new": True,
        },
    )


@router.post("/", response_model=None)
@requires_permission("manage_own_books")
async def create_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    status: str = Form(...),
    notes: str | None = Form(None),
    rating: str | None = Form(None),
    genres: str | None = Form(None),  # Will be a comma-separated string of genres
    publication_date: str | None = Form(None),
    page_count: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Create a new book."""

    # Validate status
    try:
        book_status = models.BookStatus[status.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid status") from None

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
                status_code=400,
                detail="Rating must be a valid integer between 0 and 3"
            ) from None
    # Parse page count if provided
    parsed_page_count = None
    if page_count and page_count.strip():
        try:
            parsed_page_count = int(page_count)
        except ValueError:
            # If not a valid integer, just ignore it
            pass
            
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
        # New fields
        genres=genres.split(',') if genres else [],
        publication_date=publication_date,
        page_count=parsed_page_count,
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    return RedirectResponse(
        url="/books",
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


@router.get("/{book_id}", response_class=HTMLResponse, response_model=None)
async def get_book(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Get a single book by ID."""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    # Check if user has permission to view this book
    if book.user_id != current_user.id and not roles.has_permission(
        current_user, "view_all_books"
    ):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this book",
        )
        
    templates = get_templates(request)
    return templates.TemplateResponse(
        "books/book_modal.html",
        {
            "request": request,
            "book": book,
            "current_user": current_user,
        },
    )


@router.get("/{book_id}/edit", response_class=HTMLResponse, response_model=None)
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
    if book.user_id != current_user.id and not roles.has_permission(
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
            "statuses": list(models.BookStatus),
            "is_new": False,
        },
    )


@router.post("/{book_id}", response_model=None)
@requires_permission("manage_own_books")
async def update_book(
    request: Request,
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    status: str = Form(...),
    notes: str | None = Form(None),
    rating: str | None = Form(None),
    genres: str | None = Form(None),  # Will be a comma-separated string of genres
    publication_date: str | None = Form(None),
    page_count: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Update a book's information."""

    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if user has permission to edit this book
    if book.user_id != current_user.id and not roles.has_permission(
        current_user, "manage_all_books"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to edit this book")

    # Validate status
    try:
        new_status = models.BookStatus[status.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid status") from None

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
                status_code=400,
                detail="Rating must be a valid integer between 0 and 3"
            ) from None

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

    # Parse page count if provided
    parsed_page_count = None
    if page_count and page_count.strip():
        try:
            parsed_page_count = int(page_count)
        except ValueError:
            # If not a valid integer, just ignore it
            pass

    # Update book
    book.title = title
    book.author = author
    book.status = new_status
    book.notes = notes
    book.rating = parsed_rating
    book.genres = genres.split(',') if genres else []
    book.publication_date = publication_date
    book.page_count = parsed_page_count
    book.updated_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(
        url="/books",
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


@router.delete("/{book_id}", response_model=None)
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
    if book.user_id != current_user.id and not roles.has_permission(
        current_user, "manage_all_books"
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this book"
        )

    db.delete(book)
    db.commit()

    return {"success": True}


@router.post("/{book_id}/inline-update", response_class=HTMLResponse)
@requires_permission("manage_own_books")
async def inline_update_book(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Update a specific field of a book via inline editing."""
    # Manually extract form data from the request
    form_data = await request.form()

    # Extract fields from form data
    update_type = form_data.get("update_type")
    notes = form_data.get("notes")
    status = form_data.get("status")
    rating = form_data.get("rating")
    title = form_data.get("title")
    author = form_data.get("author")

    # Debug logging
    print(f"Received form data: {dict(form_data)}")
    print(f"Update type: {update_type}")

    # Validate required fields
    if not update_type:
        raise HTTPException(status_code=400, detail="Update type is required")
    # Get the book
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if user has permission to edit this book
    if book.user_id != current_user.id and not roles.has_permission(
        current_user, "manage_all_books"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to edit this book")

    # Update based on the update type
    if update_type == "notes" and notes is not None:
        book.notes = notes
    elif update_type == "status" and status is not None:
        try:
            new_status = models.BookStatus[status.upper()]

            # Handle date updates based on status change
            now = datetime.utcnow()

            # If changing to READING and no start date, set it
            if new_status == models.BookStatus.READING and not book.start_date:
                book.start_date = now

            # If changing to COMPLETED and no completion date, set it
            if new_status == models.BookStatus.COMPLETED and not book.completion_date:
                book.completion_date = now

            book.status = new_status
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status") from None
    elif update_type == "rating":
        # Handle rating
        if rating == "null" or rating is None:
            book.rating = None
        else:
            try:
                parsed_rating = int(rating)
                if not 0 <= parsed_rating <= 3:
                    raise HTTPException(
                        status_code=400, detail="Rating must be between 0 and 3"
                    )
                book.rating = parsed_rating
                # Print for debugging
                print(f"Setting rating to {parsed_rating} for book {book.id}")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Rating must be a valid integer between 0 and 3"
                ) from None
    elif update_type == "title" and title is not None:
        # Update title
        if not title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        book.title = title.strip()
    elif update_type == "author" and author is not None:
        # Update author
        if not author.strip():
            raise HTTPException(status_code=400, detail="Author cannot be empty")
        book.author = author.strip()
    else:
        raise HTTPException(
            status_code=400, detail="Invalid update type or missing data"
        )

    # Update the timestamp
    book.updated_at = datetime.utcnow()
    
    # Print debugging information
    print(f"Before commit - Book {book.id} update: {update_type}")
    print(f"Book status: {book.status}, title: {book.title}, author: {book.author}")
    print(f"Book rating: {book.rating}")

    try:
        # Commit changes to database
        db.commit()

        # Verify the changes were committed
        db.refresh(book)
        print(f"After commit - Book {book.id} update: {update_type}")
        print(f"Book status: {book.status}, title: {book.title}, author: {book.author}")
        print(f"Book rating: {book.rating}")
    except Exception as e:
        print(f"Error updating book: {e}")
        db.rollback()
        error_msg = f"Failed to update book: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg) from e

    # Get templates
    templates = get_templates(request)
    response = templates.TemplateResponse(
        "books/book_card.html",
        {
            "request": request,
            "current_user": current_user,
            "book": book,
            "statuses": list(models.BookStatus),
            "book_statuses": list(models.BookStatus),  # For the modal
        },
    )

    # Add HX-Trigger header to close the modal
    response.headers["HX-Trigger"] = '{"closeModal": true}'
    return response


@router.get("/{book_id}/modal", response_class=HTMLResponse)
async def book_modal(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Get book details for modal display."""
    # Dependencies are now properly injected via function parameters
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if user has permission to view this book
    if book.user_id != current_user.id and not roles.has_permission(
        current_user, "view_all_books"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view this book")

    templates = get_templates(request)
    return templates.TemplateResponse(
        "books/book_modal.html",
        {
            "request": request,
            "book": book,
            "book_statuses": list(models.BookStatus),
            "current_user": current_user
        }
    )


@router.post("/{book_id}/status")
@requires_permission("manage_own_books")
async def update_book_status(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Update a book's status via drag-and-drop."""
    # Dependencies are now properly injected via function parameters
    # Get JSON data from request
    status_data = await request.json()
    # Get the book
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if user has permission to edit this book
    if book.user_id != current_user.id and not roles.has_permission(
        current_user, "manage_all_books"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to edit this book")

    # Get the new status from request body
    new_status_name = status_data.get("status")
    if not new_status_name:
        raise HTTPException(status_code=400, detail="Status is required")

    # Validate status
    try:
        new_status = models.BookStatus[new_status_name.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid status") from None

    # Skip update if status hasn't changed
    if book.status == new_status:
        return {"success": True, "message": "Status unchanged"}

    # Update start_date if status changes to READING
    now = datetime.utcnow()
    if new_status == models.BookStatus.READING and book.status != models.BookStatus.READING:
        book.start_date = now

    # Update completion_date if status changes to COMPLETED
    if new_status == models.BookStatus.COMPLETED and book.status != models.BookStatus.COMPLETED:
        book.completion_date = now

    # Update book status
    book.status = new_status
    book.updated_at = now
    db.commit()

    return {"success": True, "message": "Status updated successfully"}
