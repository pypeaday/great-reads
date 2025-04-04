"""API endpoints for searching books using the Open Library API."""

import json
import os

import httpx
from fastapi import APIRouter, HTTPException

from app.services import openlibrary_service
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


@router.get("/debug-search")
async def debug_search(q: str, fetch_details: bool = True):
    """
    Debug endpoint to see what fields are available in the search results.
    
    Args:
        q: The search query
        fetch_details: Whether to fetch detailed information
        
    Returns:
        Raw search results with all fields
    """
    if not q:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    try:
        # Use the existing search_books function
        results = await search_books(q, limit=5, fetch_details=fetch_details)
        
        # Analyze page count fields
        page_count_analysis = []
        for i, book in enumerate(results[:3]):
            book_analysis = {
                "index": i,
                "title": book.get("title"),
                "has_number_of_pages": "number_of_pages" in book,
                "number_of_pages_value": book.get("number_of_pages"),
                "has_page_count": "page_count" in book,
                "page_count_value": book.get("page_count"),
                "has_number_of_pages_median": "number_of_pages_median" in book,
                "number_of_pages_median_value": book.get("number_of_pages_median"),
                "all_keys": list(book.keys())
            }
            page_count_analysis.append(book_analysis)
        
        # Return the raw results
        return {
            "query": q,
            "fetch_details": fetch_details,
            "results": results,
            "field_analysis": {
                "has_number_of_pages": any("number_of_pages" in book for book in results),
                "has_page_count": any("page_count" in book for book in results),
                "has_number_of_pages_median": any("number_of_pages_median" in book for book in results),
                "sample_book_keys": [list(book.keys()) for book in results[:1]]
            },
            "page_count_analysis": page_count_analysis
        }
    except Exception as e:
        error_msg = f"Error in debug search: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg) from e


@router.get("/raw-api-response")
async def raw_api_response(q: str):
    """
    Get the raw API response from OpenLibrary for debugging purposes.
    
    Args:
        q: The search query
        
    Returns:
        Raw API response from OpenLibrary
    """
    if not q:
        raise HTTPException(status_code=400, detail="Search query is required")
    
    try:
        # Make a direct API call to OpenLibrary
        url = f"https://openlibrary.org/search.json?q={q}&limit=3"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Extract page count fields from the response
            page_count_fields = []
            for doc in data.get("docs", [])[:3]:
                page_info = {
                    "title": doc.get("title"),
                    "key": doc.get("key"),
                    "has_number_of_pages": "number_of_pages" in doc,
                    "number_of_pages_value": doc.get("number_of_pages"),
                    "has_number_of_pages_median": "number_of_pages_median" in doc,
                    "number_of_pages_median_value": doc.get("number_of_pages_median"),
                    "has_pagination": "pagination" in doc,
                    "pagination_value": doc.get("pagination"),
                }
                page_count_fields.append(page_info)
            
            return {
                "query": q,
                "page_count_fields": page_count_fields,
                "raw_response": data
            }
    except Exception as e:
        error_msg = f"Error fetching raw API response: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg) from e


@router.get("/test-page-count")
async def test_page_count(q: str = "harry potter"):
    """
    Test page count extraction from OpenLibrary.
    
    Args:
        q: The search query
        
    Returns:
        Detailed information about page count extraction
    """
    # First get raw search results
    url = f"https://openlibrary.org/search.json?q={q}&limit=5"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
    
    # Process search results
    results = []
    for doc in data.get("docs", [])[:5]:
        # Get basic book info
        book_info = {
            "title": doc.get("title", "Unknown"),
            "author": (doc.get("author_name", ["Unknown"])[0]
                      if doc.get("author_name") else "Unknown"),
            "work_key": doc.get("key"),
            "edition_keys": doc.get("edition_key", []),
            "cover_edition_key": doc.get("cover_edition_key"),
            "page_count": None,
            "number_of_pages": None,
            "edition_count": doc.get("edition_count", 0)
        }
        
        # First try to use the cover_edition_key if available
        if book_info["cover_edition_key"]:
            edition_id = f"books/{book_info['cover_edition_key']}"
            print(f"DEBUG: Fetching details for cover edition {edition_id}")
            details = await openlibrary_service.get_book_details(edition_id)
            if details:
                book_info["page_count"] = details.get("page_count")
                book_info["number_of_pages"] = details.get("number_of_pages")
                book_info["pagination"] = details.get("pagination")
                print(f"DEBUG: Cover edition details: {details.get('page_count')} pages")
        
        # If no page count found and we have edition keys, try the first one
        elif book_info["edition_keys"] and len(book_info["edition_keys"]) > 0:
            edition_id = f"books/{book_info['edition_keys'][0]}"
            print(f"DEBUG: Fetching details for first edition {edition_id}")
            details = await openlibrary_service.get_book_details(edition_id)
            if details:
                book_info["page_count"] = details.get("page_count")
                book_info["number_of_pages"] = details.get("number_of_pages")
                book_info["pagination"] = details.get("pagination")
                print(f"DEBUG: First edition details: {details.get('page_count')} pages")
        
        results.append(book_info)
    
    return {"results": results}
