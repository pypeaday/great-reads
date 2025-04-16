"""add_email_verification_fields

Revision ID: bbcee0f30657
Revises: 4f8e9c2d7a5b
Create Date: 2025-04-03 08:45:43.886159

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbcee0f30657'
down_revision: str | None = '4f8e9c2d7a5b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing columns if they do not exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('users')]
    with op.batch_alter_table('users') as batch_op:
        if 'is_email_verified' not in columns:
            batch_op.add_column(sa.Column('is_email_verified', sa.Boolean(), nullable=True))
        if 'verification_token' not in columns:
            batch_op.add_column(sa.Column('verification_token', sa.String(255), nullable=True))
        if 'verification_token_expires' not in columns:
            batch_op.add_column(sa.Column('verification_token_expires', sa.DateTime(), nullable=True))
    # Create a unique index for verification_token if it doesn't exist
    try:
        op.create_index('ix_users_verification_token', 'users', ['verification_token'], unique=True)
    except Exception as e:
        print(f"Note: {e}")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove only the verification_token_expires column
    # We'll keep the other columns since they might be used by the application
    try:
        op.drop_index('ix_users_verification_token', table_name='users')
    except Exception:
        pass
    
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('verification_token_expires')
