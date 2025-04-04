"""API endpoints for searching books using the Open Library API."""

import json
import os

import httpx
from fastapi import APIRouter, HTTPException

from app.services.openlibrary_service import search_books

router = APIRouter(prefix="/api/books", tags=["book_api"])


@router.get("/search", response_model=list[dict])
async def search_books_endpoint(
    q: str,
    limit: int = 10,
    fetch_details: bool = False,
):
    """
    Search for books using the Open Library API.

    Args:
        q: The search query
        limit: Maximum number of results to return
        fetch_details: Whether to fetch detailed information for each book

    Returns:
        List of book data dictionaries
    """
    if not q:
        raise HTTPException(status_code=400, detail="Search query is required")

    try:
        results = await search_books(q, limit, fetch_details)
        return results
    except Exception as e:
        error_msg = f"Error searching books: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg) from e


@router.get("/dump-raw-response")
async def dump_raw_response(q: str):
    """
    Dump the raw API response from Open Library to a file for debugging.
    
    Args:
        q: The search query
        
    Returns:
        Path to the dumped file
    """
    if not q:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    try:
        # Make a direct API call to get the raw response
        url = f"https://openlibrary.org/search.json?q={q}&limit=10"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        
        # Create a directory for dumps if it doesn't exist
        os.makedirs("api_dumps", exist_ok=True)
    
        # Write the raw response to a file
        dump_path = f"api_dumps/openlibrary_response_{q.replace(' ', '_')}.json"
        with open(dump_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return {"message": f"API response dumped to {dump_path}", "path": dump_path}
    except Exception as e:
        error_msg = f"Error dumping API response: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg) from e
