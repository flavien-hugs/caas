"""add pages table

Revision ID: a7b1f0d4e2c3
Revises: 66e3d56c4485
Create Date: 2026-06-16 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'a7b1f0d4e2c3'
down_revision: Union[str, Sequence[str], None] = '66e3d56c4485'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pages',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('slug', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('blocks', sa.JSON(), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pages_slug'), 'pages', ['slug'], unique=True)
    op.create_index(op.f('ix_pages_status'), 'pages', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_pages_status'), table_name='pages')
    op.drop_index(op.f('ix_pages_slug'), table_name='pages')
    op.drop_table('pages')
