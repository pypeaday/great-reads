"""Analytics module for the book tracking app."""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models

def get_books_completed_in_period(
    db: Session, user_id: int, start_date: datetime, end_date: datetime
) -> list[models.Book]:
    """Get all books completed by a user within a specific time period."""
    return (
        db.query(models.Book)
        .filter(
            models.Book.user_id == user_id,
            models.Book.status == models.BookStatus.COMPLETED,
            models.Book.completion_date >= start_date,
            models.Book.completion_date <= end_date,
        )
        .all()
    )


def get_reading_stats(db: Session, user_id: int) -> dict:
    """Get reading statistics for a user over different time periods."""
    now = datetime.utcnow()

    # Define time periods
    one_month_ago = now - timedelta(days=30)
    three_months_ago = now - timedelta(days=90)
    six_months_ago = now - timedelta(days=180)
    one_year_ago = now - timedelta(days=365)

    # Get books completed in each time period
    books_last_month = get_books_completed_in_period(db, user_id, one_month_ago, now)
    books_last_3_months = get_books_completed_in_period(
        db, user_id, three_months_ago, now
    )
    books_last_6_months = get_books_completed_in_period(
        db, user_id, six_months_ago, now
    )
    books_last_year = get_books_completed_in_period(db, user_id, one_year_ago, now)

    # Get total books by status
    total_completed = (
        db.query(func.count(models.Book.id))
        .filter(
            models.Book.user_id == user_id,
            models.Book.status == models.BookStatus.COMPLETED,
        )
        .scalar() or 0
    )

    total_reading = (
        db.query(func.count(models.Book.id))
        .filter(
            models.Book.user_id == user_id,
            models.Book.status == models.BookStatus.READING,
        )
        .scalar() or 0
    )

    total_to_read = (
        db.query(func.count(models.Book.id))
        .filter(
            models.Book.user_id == user_id,
            models.Book.status == models.BookStatus.TO_READ,
        )
        .scalar() or 0
    )

    total_on_hold = (
        db.query(func.count(models.Book.id))
        .filter(
            models.Book.user_id == user_id,
            models.Book.status == models.BookStatus.ON_HOLD,
        )
        .scalar() or 0
    )

    total_dnf = (
        db.query(func.count(models.Book.id))
        .filter(
            models.Book.user_id == user_id,
            models.Book.status == models.BookStatus.DNF,
        )
        .scalar() or 0
    )

    # Calculate average rating for completed books
    avg_rating_result = (
        db.query(func.avg(models.Book.rating))
        .filter(
            models.Book.user_id == user_id,
            models.Book.status == models.BookStatus.COMPLETED,
            models.Book.rating.is_not(None),
        )
        .scalar()
    )

    avg_rating = round(float(avg_rating_result), 1) if avg_rating_result else 0

    return {
        "books_last_month": len(books_last_month),
        "books_last_3_months": len(books_last_3_months),
        "books_last_6_months": len(books_last_6_months),
        "books_last_year": len(books_last_year),
        "total_completed": total_completed,
        "total_reading": total_reading,
        "total_to_read": total_to_read,
        "total_on_hold": total_on_hold,
        "total_dnf": total_dnf,
        "avg_rating": avg_rating,
    }


def get_monthly_reading_data(db: Session, user_id: int) -> list[dict]:
    """Get monthly reading data for the past 12 months."""
    now = datetime.utcnow()

    # Get data for the past 12 months
    months_data = []

    for i in range(12):
        # Calculate start and end of month
        # For current month (i=0)
        if i == 0:
            # Last day of previous month
            end_date = now.replace(day=1) - timedelta(days=1)
        else:
            # For previous months, calculate using datetime's month arithmetic
            # Calculate the year and month for the target month
            target_month = now.month - i
            target_year = now.year

            # Adjust for negative months
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            # Get the first day of the target month
            first_day = datetime(year=target_year, month=target_month, day=1)

            # Last day of the month is one day before the first day of next month
            end_date = first_day - timedelta(days=1)
        # First day of the month
        start_date = end_date.replace(day=1)

        # Get books completed in this month
        books_in_month = get_books_completed_in_period(
            db, user_id, start_date, end_date
        )

        # Format month name
        month_name = start_date.strftime("%b %Y")

        months_data.append({
            "month": month_name,
            "count": len(books_in_month),
        })

    # Reverse to get chronological order
    months_data.reverse()

    return months_data
