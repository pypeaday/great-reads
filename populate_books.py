#!/usr/bin/env python3
"""
Script to populate the book tracking app with random books.
This script adds 50 random books with various statuses and ratings to the admin account.
"""

import os
import random
import sys
from datetime import datetime
from datetime import timedelta

# Add the current directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app modules
from app.auth import authenticate_user
from app.database import SessionLocal
from app.models import Book
from app.models import BookStatus

# Sample book data
SAMPLE_BOOKS = [
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"title": "1984", "author": "George Orwell"},
    {"title": "Pride and Prejudice", "author": "Jane Austen"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien"},
    {"title": "Brave New World", "author": "Aldous Huxley"},
    {"title": "The Lord of the Rings", "author": "J.R.R. Tolkien"},
    {"title": "Animal Farm", "author": "George Orwell"},
    {"title": "The Alchemist", "author": "Paulo Coelho"},
    {"title": "The Hunger Games", "author": "Suzanne Collins"},
    {"title": "Harry Potter and the Philosopher's Stone", "author": "J.K. Rowling"},
    {"title": "The Shining", "author": "Stephen King"},
    {"title": "The Da Vinci Code", "author": "Dan Brown"},
    {"title": "The Road", "author": "Cormac McCarthy"},
    {"title": "Dune", "author": "Frank Herbert"},
    {"title": "The Handmaid's Tale", "author": "Margaret Atwood"},
    {"title": "The Martian", "author": "Andy Weir"},
    {"title": "Gone Girl", "author": "Gillian Flynn"},
    {"title": "The Silent Patient", "author": "Alex Michaelides"},
    {"title": "Where the Crawdads Sing", "author": "Delia Owens"},
    {"title": "The Night Circus", "author": "Erin Morgenstern"},
    {"title": "The Kite Runner", "author": "Khaled Hosseini"},
    {"title": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson"},
    {"title": "The Book Thief", "author": "Markus Zusak"},
    {"title": "Sapiens: A Brief History of Humankind", "author": "Yuval Noah Harari"},
    {"title": "Educated", "author": "Tara Westover"},
    {"title": "Becoming", "author": "Michelle Obama"},
    {"title": "The Power of Habit", "author": "Charles Duhigg"},
    {"title": "Atomic Habits", "author": "James Clear"},
    {"title": "The Midnight Library", "author": "Matt Haig"},
    {"title": "Project Hail Mary", "author": "Andy Weir"},
    {"title": "The Seven Husbands of Evelyn Hugo", "author": "Taylor Jenkins Reid"},
    {"title": "The Invisible Life of Addie LaRue", "author": "V.E. Schwab"},
    {"title": "Circe", "author": "Madeline Miller"},
    {"title": "The Song of Achilles", "author": "Madeline Miller"},
    {"title": "Normal People", "author": "Sally Rooney"},
    {"title": "The Thursday Murder Club", "author": "Richard Osman"},
    {"title": "Klara and the Sun", "author": "Kazuo Ishiguro"},
    {"title": "The Vanishing Half", "author": "Brit Bennett"},
    {"title": "A Gentleman in Moscow", "author": "Amor Towles"},
    {"title": "The Lincoln Highway", "author": "Amor Towles"},
    {"title": "The Four Winds", "author": "Kristin Hannah"},
    {"title": "The Nightingale", "author": "Kristin Hannah"},
    {"title": "The Overstory", "author": "Richard Powers"},
    {"title": "Hamnet", "author": "Maggie O'Farrell"},
    {"title": "The House in the Cerulean Sea", "author": "TJ Klune"},
    {"title": "Pachinko", "author": "Min Jin Lee"},
    {"title": "The Fifth Season", "author": "N.K. Jemisin"},
    {"title": "The Three-Body Problem", "author": "Liu Cixin"},
    {"title": "Exhalation", "author": "Ted Chiang"},
    {"title": "Children of Time", "author": "Adrian Tchaikovsky"},
    {"title": "The Priory of the Orange Tree", "author": "Samantha Shannon"},
    {"title": "The City We Became", "author": "N.K. Jemisin"},
    {"title": "Mexican Gothic", "author": "Silvia Moreno-Garcia"},
    {"title": "The Starless Sea", "author": "Erin Morgenstern"},
    {"title": "The Water Dancer", "author": "Ta-Nehisi Coates"},
    {"title": "On Earth We're Briefly Gorgeous", "author": "Ocean Vuong"},
    {"title": "The Dutch House", "author": "Ann Patchett"},
    {"title": "The Testaments", "author": "Margaret Atwood"},
    {"title": "The Nickel Boys", "author": "Colson Whitehead"}
]

# Sample notes
SAMPLE_NOTES = [
    "Really enjoyed this one!",
    "A bit slow at the beginning, but gets better.",
    "One of my all-time favorites.",
    "Interesting premise, but the execution could be better.",
    "The characters felt very real and relatable.",
    "Beautiful prose, but the plot was lacking.",
    "Couldn't put it down!",
    "A thought-provoking read.",
    "The ending was unexpected.",
    "Would definitely recommend to others.",
    "Not my cup of tea, but I can see why others might like it.",
    "The world-building was incredible.",
    "I learned a lot from this book.",
    "A perfect summer read.",
    "I'll be thinking about this one for a while.",
    "",  # Empty notes for some books
]

def login_admin():
    """Log in as admin and return the user object"""
    db = SessionLocal()
    try:
        # Authenticate admin user
        admin_email = "admin@example.com"
        admin_password = "admin123"

        user = authenticate_user(db, admin_email, admin_password)
        if not user:
            print("Failed to authenticate admin user. Check credentials.")
            sys.exit(1)

        print(f"Successfully authenticated as admin: {user.email}")
        return user
    finally:
        db.close()

def create_random_books(user_id, num_books=20):
    """Create random books for the specified user"""
    db = SessionLocal()
    try:
        # Get a random selection of books
        selected_books = random.sample(SAMPLE_BOOKS, min(num_books, len(SAMPLE_BOOKS)))

        # Current time for reference
        now = datetime.utcnow()

        # Create and add books
        for book_data in selected_books:
            # Weighted selection for status - make COMPLETED more common
            status_weights = {
                BookStatus.COMPLETED: 0.6,  # 60% chance for COMPLETED
                BookStatus.READING: 0.15,   # 15% chance for READING
                BookStatus.TO_READ: 0.1,    # 10% chance for TO_READ
                BookStatus.ON_HOLD: 0.1,    # 10% chance for ON_HOLD
                BookStatus.DNF: 0.05       # 5% chance for DNF
            }
            status = random.choices(
                population=list(status_weights.keys()),
                weights=list(status_weights.values()),
                k=1
            )[0]

            # Set appropriate dates based on status
            start_date = None
            completion_date = None

            if status in [
                BookStatus.READING,
                BookStatus.COMPLETED,
                BookStatus.DNF,
                BookStatus.ON_HOLD
            ]:
                # For books that have been started, set a start date in the past
                days_ago = random.randint(10, 365)
                start_date = now - timedelta(days=days_ago)

            if status in [BookStatus.COMPLETED, BookStatus.DNF]:
                # For completed or DNF books, set a completion date after the start date
                if start_date:
                    days_to_complete = random.randint(1, min(days_ago, 60))
                    completion_date = start_date + timedelta(
                        days=days_to_complete
                    )

            # Set rating based on status
            rating = None
            if status == BookStatus.COMPLETED:
                # 0-5 rating for completed books with a distribution
                # favoring higher ratings
                # Weights for ratings 0-5
                rating_weights = [0.05, 0.1, 0.15, 0.25, 0.25, 0.2]
                rating = random.choices(
                    population=range(6),
                    weights=rating_weights,
                    k=1
                )[0]

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
            print(
                f"Added book: {book.title} by {book.author} "
                f"(Status: {book.status.value})"
            )

        db.commit()
        print(f"\nSuccessfully added {num_books} books to the database!")

    except Exception as e:
        db.rollback()
        print(f"Error adding books: {e}")
        sys.exit(1)
    finally:
        db.close()

def main():
    """Main function to populate the database with random books"""
    print("Populating book tracking app with random books...")

    # Login as admin
    admin_user = login_admin()

    # Create random books for the admin user
    create_random_books(admin_user.id, 50)

    print("\nDone! You can now view the books in the app.")

if __name__ == "__main__":
    main()
