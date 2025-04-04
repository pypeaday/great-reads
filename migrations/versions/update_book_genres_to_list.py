"""update_book_genres_to_list

Revision ID: update_book_genres
Revises: aa0b51faa7a4
Create Date: 2025-04-04 08:25:00.000000

"""
from collections.abc import Sequence
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'update_book_genres'
down_revision: str | None = 'aa0b51faa7a4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to use genres as a JSON array."""
    # Check if genres column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('books')]
    
    # Only add the genres column if it doesn't exist
    if 'genres' not in columns:
        # Add the new genres column as JSON
        op.add_column('books', sa.Column('genres', sqlite.JSON(), nullable=True))
        
        # Convert existing genre values to JSON arrays
        books = conn.execute(sa.text("SELECT id, genre FROM books")).fetchall()
        for book in books:
            if book[1]:  # If genre is not None
                # Convert single genre to a list with one item
                genres_list = [book[1]]
                # Update the row with the new JSON array
                conn.execute(
                    sa.text("UPDATE books SET genres = :genres WHERE id = :id"),
                    {"id": book[0], "genres": json.dumps(genres_list)}
                )


def downgrade() -> None:
    """Downgrade schema back to single genre string."""
    # Get a reference to the books table
    conn = op.get_bind()
    
    # Convert JSON arrays back to single strings
    books = conn.execute(sa.text("SELECT id, genres FROM books")).fetchall()
    for book in books:
        if book[1]:  # If genres is not None
            try:
                # Parse the JSON array
                genres_list = json.loads(book[1])
                # Take the first genre if available
                genre = genres_list[0] if genres_list else None
                # Update the row with the single genre
                conn.execute(
                    sa.text("UPDATE books SET genre = :genre WHERE id = :id"),
                    {"id": book[0], "genre": genre}
                )
            except (json.JSONDecodeError, IndexError):
                # If there's an error parsing JSON, skip this row
                pass
    
    # Drop the genres column
    op.drop_column('books', 'genres')
