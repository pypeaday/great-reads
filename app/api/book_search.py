"""API endpoints for searching books using the Open Library API."""

from fastapi import APIRouter, HTTPException
from app.services.openlibrary_service import search_books

router = APIRouter(prefix="/api/books", tags=["book_api"])


@router.get("/search", response_model=list[dict])
async def search_books_endpoint(
    q: str,
    limit: int = 10,
):
    """
    Search for books using the Open Library API.

    Args:
        q: The search query
        limit: Maximum number of results to return

    Returns:
        List of book data dictionaries
    """
    if not q:
        raise HTTPException(status_code=400, detail="Search query is required")

    try:
        results = await search_books(q, limit)
        return results
    except Exception as e:
        error_msg = f"Error searching books: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg) from e
