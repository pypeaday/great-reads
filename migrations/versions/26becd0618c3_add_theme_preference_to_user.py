"""add_theme_preference_to_user

Revision ID: 26becd0618c3
Revises: 2db6bdfb410e
Create Date: 2025-03-30 06:29:23.329230

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "26becd0618c3"
down_revision: Union[str, None] = "2db6bdfb410e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # For SQLite, we need to:
    # 1. Create new table with desired schema
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table to old name

    # Create new table
    op.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            last_login DATETIME,
            theme_preference VARCHAR(50) NOT NULL DEFAULT 'gruvbox-dark',
            role VARCHAR(20) NOT NULL,
            FOREIGN KEY(role) REFERENCES roles(name)
        )
    """)

    # Copy data from old table to new table
    op.execute("""
        INSERT INTO users_new (
            id, email, name, hashed_password, is_active, created_at, 
            last_login, role, theme_preference
        )
        SELECT 
            id, email, name, hashed_password, is_active, created_at,
            last_login, role, 'gruvbox-dark'
        FROM users
    """)

    # Drop old table
    op.execute("DROP TABLE users")

    # Rename new table to old name
    op.execute("ALTER TABLE users_new RENAME TO users")

    # Recreate indexes
    op.execute("CREATE INDEX ix_users_email ON users (email)")
    op.execute("CREATE INDEX ix_users_id ON users (id)")


def downgrade() -> None:
    """Downgrade schema."""
    # Create new table without theme_preference
    op.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            last_login DATETIME,
            role VARCHAR(20) NOT NULL,
            FOREIGN KEY(role) REFERENCES roles(name)
        )
    """)

    # Copy data excluding theme_preference
    op.execute("""
        INSERT INTO users_new (
            id, email, name, hashed_password, is_active, created_at,
            last_login, role
        )
        SELECT 
            id, email, name, hashed_password, is_active, created_at,
            last_login, role
        FROM users
    """)

    # Drop old table
    op.execute("DROP TABLE users")

    # Rename new table to old name
    op.execute("ALTER TABLE users_new RENAME TO users")

    # Recreate indexes
    op.execute("CREATE INDEX ix_users_email ON users (email)")
    op.execute("CREATE INDEX ix_users_id ON users (id)")
