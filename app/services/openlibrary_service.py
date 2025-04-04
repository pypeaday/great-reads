"""Service for interacting with the Open Library API."""

import httpx
from typing import Any


async def search_books(query: str, limit: int = 10) -> list[dict[str, Any]]:
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
        books.append(book)
    return books


def get_first_item(items: list[Any]) -> Any | None:
    """Get the first item from a list if it exists."""
    return items[0] if items else None
