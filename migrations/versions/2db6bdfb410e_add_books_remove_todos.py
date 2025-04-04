"""add_books_remove_todos

Revision ID: 2db6bdfb410e
Revises: 3ad4540a4ed1
Create Date: 2025-03-28 16:46:13.300369

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2db6bdfb410e'
down_revision: str | None = '3ad4540a4ed1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('books',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('author', sa.String(length=255), nullable=False),
    sa.Column('status', sa.Enum('TO_READ', 'READING', 'COMPLETED', 'ON_HOLD', 'DNF', name='bookstatus'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('completion_date', sa.DateTime(), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_books_id'), 'books', ['id'], unique=False)
    op.drop_index('ix_todos_id', table_name='todos')
    op.drop_table('todos')
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.create_table('todos',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('content', sa.VARCHAR(length=500), nullable=False),
    sa.Column('completed', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_todos_id', 'todos', ['id'], unique=False)
    op.drop_index(op.f('ix_books_id'), table_name='books')
    op.drop_table('books')
    # ### end Alembic commands ###
