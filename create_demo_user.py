#!/usr/bin/env python3
"""
Script to create a demo user with sample books for the book tracking app.
This script adds a demo user with login credentials:
- Email: demo@example.com
- Password: demo
And populates the account with 30 random books with various statuses and ratings.
"""

import random
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the current directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app modules
from app.models import Book, BookStatus, User
from app.database import SessionLocal
from app.auth import get_password_hash, authenticate_user

# Import sample book data from populate_books.py
from populate_books import SAMPLE_BOOKS, SAMPLE_NOTES

def create_demo_user():
    """Create a demo user account if it doesn't already exist"""
    db = SessionLocal()
    try:
        # Check if demo user already exists
        demo_email = "demo@example.com"
        demo_password = "demo"
        
        existing_user = db.query(User).filter(User.email == demo_email).first()
        if existing_user:
            print(f"Demo user already exists: {demo_email}")
            return existing_user
        
        # Create demo user
        demo_user = User(
            email=demo_email,
            hashed_password=get_password_hash(demo_password),
            name="Demo User",
            is_active=True,
            role="user",
            created_at=datetime.utcnow(),
            theme_preference="gruvbox-dark"
        )
        
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        
        print(f"Successfully created demo user: {demo_user.email}")
        return demo_user
    except Exception as e:
        db.rollback()
        print(f"Error creating demo user: {e}")
        sys.exit(1)
    finally:
        db.close()

def create_random_books(user_id, num_books=30):
    """Create random books for the specified user"""
    db = SessionLocal()
    try:
        # Get a random selection of books
        selected_books = random.sample(SAMPLE_BOOKS, min(num_books, len(SAMPLE_BOOKS)))
        
        # Current time for reference
        now = datetime.utcnow()
        
        # Create and add books
        for i, book_data in enumerate(selected_books):
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
                title=book_data["title"],
                author=book_data["author"],
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
            print(f"Added book: {book.title} by {book.author} (Status: {book.status.value})")
        
        db.commit()
        print(f"\nSuccessfully added {num_books} books to the demo user's library!")
        
    except Exception as e:
        db.rollback()
        print(f"Error adding books: {e}")
        sys.exit(1)
    finally:
        db.close()

def verify_demo_user():
    """Verify that the demo user can be authenticated"""
    db = SessionLocal()
    try:
        demo_email = "demo@example.com"
        demo_password = "demo"
        
        user = authenticate_user(db, demo_email, demo_password)
        if user:
            print(f"Successfully verified demo user authentication: {user.email}")
            return True
        else:
            print("Failed to authenticate demo user. Check credentials.")
            return False
    finally:
        db.close()

def main():
    """Main function to create demo user and populate with random books"""
    print("Creating demo user and populating with sample books...")
    
    # Create demo user
    demo_user = create_demo_user()
    
    # Create random books for the demo user
    create_random_books(demo_user.id, 30)
    
    # Verify demo user can login
    verify_demo_user()
    
    print("\nDone! You can now login with:")
    print("Email: demo@example.com")
    print("Password: demo")

if __name__ == "__main__":
    main()
