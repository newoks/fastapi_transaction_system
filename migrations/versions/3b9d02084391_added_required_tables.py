"""Added required tables

Revision ID: 3b9d02084391
Revises:
Create Date: 2022-11-14 18:17:47.591030

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey

# revision identifiers, used by Alembic.
revision = '3b9d02084391'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(256), unique=True),
        sa.Column('name', sa.String(256), unique=False),
        sa.Column('is_active', sa.Integer, nullable=False, unique=False),
    )

    op.create_table(
        'balance',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, ForeignKey('users.id')),
        sa.Column('value', sa.Integer, unique=False),
        sa.Column('updated_at', sa.DateTime, unique=False)
    )


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('balance')
