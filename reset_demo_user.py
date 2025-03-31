#!/usr/bin/env python3
"""
Script to reset the demo user's books in the book tracking app.
This script deletes all existing books for the demo user and adds 30 new random books.
Designed to be run on a schedule (e.g., daily) to keep the demo account in a clean state.
"""

import random
import sys
import os
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("reset_demo_user")

# Add the current directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app modules
from app.models import Book, BookStatus, User
from app.database import SessionLocal
from app.auth import authenticate_user

# Import sample book data from populate_books.py
from populate_books import SAMPLE_BOOKS, SAMPLE_NOTES

def get_demo_user():
    """Get the demo user account"""
    db = SessionLocal()
    try:
        demo_email = "demo@example.com"
        demo_user = db.query(User).filter(User.email == demo_email).first()
        
        if not demo_user:
            logger.error(f"Demo user not found: {demo_email}")
            return None
        
        logger.info(f"Found demo user: {demo_user.email} (ID: {demo_user.id})")
        return demo_user
    finally:
        db.close()

def delete_demo_books(user_id):
    """Delete all books for the demo user"""
    db = SessionLocal()
    try:
        # Get count of books before deletion
        book_count = db.query(Book).filter(Book.user_id == user_id).count()
        logger.info(f"Found {book_count} books to delete for demo user")
        
        # Delete all books for the demo user
        db.query(Book).filter(Book.user_id == user_id).delete()
        db.commit()
        
        logger.info(f"Successfully deleted {book_count} books for demo user")
        return book_count
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting books: {e}")
        raise
    finally:
        db.close()

def create_random_books(user_id, num_books=30):
    """Create random books for the demo user"""
    db = SessionLocal()
    try:
        # Get a random selection of books
        selected_books = random.sample(SAMPLE_BOOKS, min(num_books, len(SAMPLE_BOOKS)))
        
        # Current time for reference
        now = datetime.utcnow()
        
        # Create and add books
        for book_data in enumerate(selected_books):
            # Randomly select a status
            status = random.choice(list(BookStatus))
            
            # Set appropriate dates based on status
            start_date = None
            completion_date = None
            
            if status in [BookStatus.READING, BookStatus.COMPLETED, BookStatus.DNF, BookStatus.ON_HOLD]:
                # For books that have been started, set a start date in the past
                days_ago = random.randint(10, 365)
                start_date = now - timedelta(days=days_ago)
            
            if status in [BookStatus.COMPLETED, BookStatus.DNF]:
                # For completed or DNF books, set a completion date after the start date
                if start_date:
                    days_to_complete = random.randint(1, min(days_ago, 60))
                    completion_date = start_date + timedelta(days=days_to_complete)
            
            # Set rating based on status
            rating = None
            if status == BookStatus.COMPLETED:
                # 0-3 rating for completed books
                rating = random.randint(0, 3)
            
            # Random notes
            notes = random.choice(SAMPLE_NOTES) if random.random() > 0.3 else None
            
            # Create the book
            book = Book(
                title=book_data[1]["title"],
                author=book_data[1]["author"],
                status=status,
                notes=notes,
                start_date=start_date,
                completion_date=completion_date,
                rating=rating,
                user_id=user_id,
                created_at=now - timedelta(days=random.randint(1, 400)),
                updated_at=now - timedelta(days=random.randint(0, 30))
            )
            
            db.add(book)
            logger.info(f"Added book: {book.title} by {book.author} (Status: {book.status.value})")
        
        db.commit()
        logger.info(f"Successfully added {num_books} books to the demo user's library")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding books: {e}")
        raise
    finally:
        db.close()

def main():
    """Main function to reset demo user's books"""
    logger.info("Starting demo user reset process...")
    
    # Get demo user
    demo_user = get_demo_user()
    if not demo_user:
        logger.error("Demo user not found. Exiting.")
        sys.exit(1)
    
    # Delete existing books
    deleted_count = delete_demo_books(demo_user.id)
    logger.info(f"Deleted {deleted_count} existing books")
    
    # Create new random books
    create_random_books(demo_user.id, 30)
    
    logger.info("Demo user reset completed successfully")

if __name__ == "__main__":
    main()
