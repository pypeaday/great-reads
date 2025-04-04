"""Service for interacting with the Open Library API."""

from typing import Any

import httpx


async def search_books(query: str, limit: int = 10, fetch_details: bool = False) -> list[dict[str, Any]]:
    """
    Search for books using the Open Library API.

    Args:
        query: The search query
        limit: Maximum number of results to return
        fetch_details: Whether to fetch detailed information for each book

    Returns:
        List of book data dictionaries
    """
    print(f"DEBUG: Searching for '{query}' with fetch_details={fetch_details}")
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
            "number_of_pages": doc.get("number_of_pages") or doc.get("number_of_pages_median"),
            "number_of_pages_median": doc.get("number_of_pages_median"),
            "page_count": doc.get("number_of_pages") or doc.get("number_of_pages_median"),  # Additional field for compatibility
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
        if fetch_details:
            try:
                # Initialize variables
                details = None
                details_found = False
                
                # First try to get details from the cover edition if available
                if "cover_edition_key" in doc and doc["cover_edition_key"]:
                    cover_edition_id = f"books/{doc['cover_edition_key']}"
                    print(f"DEBUG: Fetching details for cover edition {cover_edition_id}")
                    details = await get_book_details(cover_edition_id)
                    if details and (details.get("number_of_pages") or details.get("page_count")):
                        # Update book with additional details
                        book.update(details)
                        print(f"DEBUG: Found page count in cover edition: {details.get('number_of_pages') or details.get('page_count')}")
                        # We found what we need, no need to check other editions
                        details_found = True
                
                # Then try other editions if no page count found yet
                if not details_found and "edition_key" in doc and doc["edition_key"]:
                    # Try up to 3 editions to find page count
                    for edition_key in doc["edition_key"][:3]:  # Limit to first 3 editions
                        edition_id = f"books/{edition_key}"
                        print(f"DEBUG: Fetching details for edition {edition_id}")
                        details = await get_book_details(edition_id)
                        if details and (details.get("number_of_pages") or details.get("page_count")):
                            # Update book with additional details
                            book.update(details)
                            print(f"DEBUG: Found page count in edition {edition_id}: {details.get('number_of_pages') or details.get('page_count')}")
                            details_found = True
                            break  # Stop once we find an edition with page count
                
                # Fallback to work details if no page count found yet
                if book["key"] and not details_found:
                    work_id = book["key"]
                    print(f"DEBUG: Fetching details for work {work_id}")
                    work_details = await get_book_details(work_id)
                    if work_details:
                        # Only update fields that aren't already set
                        for key, value in work_details.items():
                            if key not in book or not book[key]:
                                book[key] = value
                        
                        # Check if we got page count from work details
                        if work_details.get("number_of_pages") and not book.get("number_of_pages"):
                            book["number_of_pages"] = work_details["number_of_pages"]
                            book["page_count"] = work_details["number_of_pages"]
                            print(f"DEBUG: Set page count from work details: {work_details['number_of_pages']}")
                            details_found = True
            except Exception as e:
                print(f"Error fetching details: {e}")
                
        books.append(book)
    return books


def get_first_item(items: list[Any]) -> Any | None:
    """Get the first item from a list if it exists."""
    return items[0] if items else None


async def get_book_details(resource_id: str) -> dict[str, Any] | None:
    """
    Get detailed information for a book from the Open Library API.
    
    Args:
        resource_id: The Open Library resource ID (e.g., "works/OL82536W" or "books/OL13522117M")
        
    Returns:
        Dictionary with detailed book information or None if not found
    """
    # Remove leading slash if present
    if resource_id.startswith("/"):
        resource_id = resource_id[1:]
    
    is_book_edition = "books/" in resource_id
    url = f"https://openlibrary.org/{resource_id}.json"
    print(f"DEBUG: Fetching details from {url}")
    
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
            
        # Handle page count differently based on whether this is a work or an edition
        page_count_found = False
        
        # For editions (book endpoint), check pagination field directly
        if is_book_edition:
            # Check for pagination field which contains page count
            pagination = data.get("pagination")
            print(f"DEBUG: Direct pagination field: {pagination}")
            
            if pagination:
                # Try to extract number from pagination string (e.g., "xii, 223 p.")
                import re
                # Look for patterns like "ix, 687 p." or "223 pages" or "223 p"
                page_match = re.search(r'(\d+)\s*p(?:\.|ages)?', pagination)
                if page_match:
                    extracted_pages = page_match.group(1)
                    details["number_of_pages"] = int(extracted_pages)
                    details["page_count"] = int(extracted_pages)
                    print(f"DEBUG: Extracted page count from pagination: {extracted_pages}")
                    page_count_found = True
                else:
                    # Fallback: just extract any number
                    page_match = re.search(r'\d+', pagination)
                    if page_match:
                        extracted_pages = page_match.group(0)
                        details["number_of_pages"] = int(extracted_pages)
                        details["page_count"] = int(extracted_pages)
                        print(f"DEBUG: Extracted page count from pagination (fallback): {extracted_pages}")
                        page_count_found = True
            
            # Also check direct number_of_pages field
            if not page_count_found and "number_of_pages" in data:
                page_count = data.get("number_of_pages")
                if page_count:
                    details["number_of_pages"] = page_count
                    details["page_count"] = page_count
                    print(f"DEBUG: Found page count in edition data: {page_count}")
                    page_count_found = True
        
        # For works, check main data first, then fetch editions
        else:
            # First check if page count is in the main work data
            if "number_of_pages" in data:
                page_count = data.get("number_of_pages")
                if page_count:
                    details["number_of_pages"] = page_count
                    details["page_count"] = page_count
                    print(f"DEBUG: Found page count in main work data: {page_count}")
                    page_count_found = True
            
            # Next check for page count in editions
            if not page_count_found and "links" in data and "editions" in data.get("links", {}):
                edition_url = data["links"]["editions"]
                print(f"DEBUG: Fetching editions from {edition_url}")
                edition_data = await get_editions(edition_url)
                
                if edition_data:
                    print(f"DEBUG: Edition data keys: {list(edition_data.keys() if isinstance(edition_data, dict) else [])}")
                
                if edition_data and "entries" in edition_data and edition_data["entries"]:
                    # Check multiple editions, not just the first one
                    for edition_index, edition in enumerate(edition_data["entries"][:3]):  # Check first 3 editions
                        print(f"DEBUG: Edition {edition_index} keys: {list(edition.keys())}")
                        
                        # Try direct page count fields first
                        page_count = edition.get("number_of_pages")
                        print(f"DEBUG: number_of_pages from edition {edition_index}: {page_count}")
                        
                        if page_count:
                            details["number_of_pages"] = page_count
                            details["page_count"] = page_count  # Additional field for compatibility
                            print(f"DEBUG: Set page_count to {page_count} from edition {edition_index}")
                            page_count_found = True
                            break  # Found what we need, stop checking editions
                    
                        # Check for pagination field which might contain page count
                        pagination = edition.get("pagination")
                        print(f"DEBUG: pagination field in edition {edition_index}: {pagination}")
                        
                        if pagination:
                            # Try to extract number from pagination string (e.g., "xii, 223 p.")
                            import re
                            # Look for patterns like "ix, 687 p." or "223 pages" or "223 p"
                            page_match = re.search(r'(\d+)\s*p(?:\.|ages)?', pagination)
                            if page_match:
                                extracted_pages = page_match.group(1)
                                details["number_of_pages"] = int(extracted_pages)
                                details["page_count"] = int(extracted_pages)
                                print(f"DEBUG: Extracted page count from pagination: {extracted_pages}")
                                page_count_found = True
                                break  # Found what we need, stop checking editions
                            else:
                                # Fallback: just extract any number
                                page_match = re.search(r'\d+', pagination)
                                if page_match:
                                    extracted_pages = page_match.group(0)
                                    details["number_of_pages"] = int(extracted_pages)
                                    details["page_count"] = int(extracted_pages)
                                    print(f"DEBUG: Extracted page count from pagination (fallback): {extracted_pages}")
                                    page_count_found = True
                                    break  # Found what we need, stop checking editions
                    
                        # Check for physical_dimensions field which might contain page count
                        physical_dimensions = edition.get("physical_dimensions")
                        print(f"DEBUG: physical_dimensions field in edition {edition_index}: {physical_dimensions}")
                        
                        if physical_dimensions and not page_count_found:
                            # Try to extract number from physical_dimensions string
                            import re
                            # Look for patterns like "223 p" or "223 pages"
                            page_match = re.search(r'(\d+)\s*p(?:\.|ages)?', physical_dimensions)
                            if page_match:
                                extracted_pages = page_match.group(1)
                                details["number_of_pages"] = int(extracted_pages)
                                details["page_count"] = int(extracted_pages)
                                print(f"DEBUG: Extracted page count from physical_dimensions: {extracted_pages}")
                                page_count_found = True
                                break  # Found what we need, stop checking editions
                
                # If we still don't have page count, check for number_of_pages_median in the first edition
                if not page_count_found and edition_data["entries"]:
                    first_edition = edition_data["entries"][0]
                    median_pages = first_edition.get("number_of_pages_median")
                    print(f"DEBUG: number_of_pages_median: {median_pages}")
                    if median_pages:
                        details["number_of_pages"] = median_pages
                        details["page_count"] = median_pages
                        print(f"DEBUG: Set page_count to median value: {median_pages}")
                        page_count_found = True
        
        # If we still don't have page count, check if it's in the number_of_pages_median field of the work
        if not page_count_found and "number_of_pages_median" in data:
            median_pages = data.get("number_of_pages_median")
            if median_pages:
                details["number_of_pages"] = median_pages
                details["page_count"] = median_pages
                print(f"DEBUG: Using work's number_of_pages_median as fallback: {median_pages}")
                page_count_found = True
        
        if not page_count_found:
            print("DEBUG: No page count found in any field")
                
        return details


async def get_editions(editions_url: str) -> dict[str, Any] | None:
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
