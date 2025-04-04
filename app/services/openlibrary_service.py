"""Service for interacting with the Open Library API."""

import httpx
from typing import Any, Optional


async def search_books(query: str, limit: int = 10, fetch_details: bool = False) -> list[dict[str, Any]]:
    """
    Search for books using the Open Library API.

    Args:
        query: The search query
        limit: Maximum number of results to return

    Returns:
        List of book data dictionaries
    """
    url = f"https://openlibrary.org/search.json?q={query}&limit={limit}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
    books = []
    for doc in data.get("docs", []):
        # Extract relevant book information
        book = {
            "title": doc.get("title", "Unknown Title"),
            "author": (doc.get("author_name", ["Unknown Author"])[0]
                     if doc.get("author_name") else "Unknown Author"),
            "first_publish_year": doc.get("first_publish_year"),
            "key": doc.get("key"),  # Open Library ID
            "cover_id": doc.get("cover_i"),
            "isbn": get_first_item(doc.get("isbn", [])),
            "number_of_pages": doc.get("number_of_pages_median"),
            "publishers": doc.get("publisher", []),
            "subjects": doc.get("subject", [])[:5] if doc.get("subject") else [],
            "language": get_first_item(doc.get("language", [])),
            "olid": get_first_item(doc.get("edition_key", [])),
        }
        # Add cover image URL if available
        if book["cover_id"]:
            book["cover_url"] = f"https://covers.openlibrary.org/b/id/{book['cover_id']}-M.jpg"
        elif book["isbn"]:
            book["cover_url"] = f"https://covers.openlibrary.org/b/isbn/{book['isbn']}-M.jpg"
        elif book["olid"]:
            book["cover_url"] = f"https://covers.openlibrary.org/b/olid/{book['olid']}-M.jpg"
        # Add Open Library URL
        if book["key"]:
            book["ol_url"] = f"https://openlibrary.org{book['key']}"
            
        # Fetch detailed information if requested
        if fetch_details and book["key"]:
            try:
                details = await get_book_details(book["key"])
                if details:
                    # Update book with additional details
                    book.update(details)
            except Exception as e:
                print(f"Error fetching details for {book['key']}: {e}")
                
        books.append(book)
    return books


def get_first_item(items: list[Any]) -> Any | None:
    """Get the first item from a list if it exists."""
    return items[0] if items else None


async def get_book_details(work_id: str) -> Optional[dict[str, Any]]:
    """
    Get detailed information for a book from the Open Library API using its work ID.
    
    Args:
        work_id: The Open Library work ID (e.g., "/works/OL82536W")
        
    Returns:
        Dictionary with detailed book information or None if not found
    """
    # Remove leading slash if present
    if work_id.startswith("/"):
        work_id = work_id[1:]
        
    url = f"https://openlibrary.org/{work_id}.json"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        # Extract relevant details
        details = {}
        
        # Get subjects (genres) - collect from multiple fields for better coverage
        subjects = []
        # Main subjects list
        if "subjects" in data:
            subjects.extend(data.get("subjects", []))
            
        # Subject places
        if "subject_places" in data:
            subjects.extend(data.get("subject_places", []))
            
        # Subject times
        if "subject_times" in data:
            subjects.extend(data.get("subject_times", []))
            
        # Subject people
        if "subject_people" in data:
            subjects.extend(data.get("subject_people", []))
            
        # Remove duplicates and store
        if subjects:
            details["subjects"] = list(dict.fromkeys(subjects))
            
        # Get description
        description = data.get("description", {})
        if isinstance(description, dict):
            details["description"] = description.get("value", "")
        elif isinstance(description, str):
            details["description"] = description
            
        # Get publication date from first_publish_date
        if "first_publish_date" in data:
            details["publication_date"] = data["first_publish_date"]
            
        # Get page count - we'll need to fetch an edition for this
        if "links" in data and "editions" in data.get("links", {}):
            edition_url = data["links"]["editions"]
            edition_data = await get_editions(edition_url)
            if edition_data and "entries" in edition_data and edition_data["entries"]:
                first_edition = edition_data["entries"][0]
                details["number_of_pages"] = first_edition.get("number_of_pages")
                
        return details


async def get_editions(editions_url: str) -> Optional[dict[str, Any]]:
    """
    Get editions information for a book.
    
    Args:
        editions_url: URL to the editions endpoint
        
    Returns:
        Dictionary with editions information or None if not found
    """
    if not editions_url.startswith("http"):
        editions_url = f"https://openlibrary.org{editions_url}.json"
        
    async with httpx.AsyncClient() as client:
        response = await client.get(editions_url)
        if response.status_code != 200:
            return None
            
        return response.json()
