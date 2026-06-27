"""add users.role column

Revision ID: c2d8e9f01a4b
Revises: a7b1f0d4e2c3
Create Date: 2026-06-16 18:00:00.000000

The ``role`` column was added to ``UserRow`` (RBAC introduction) but the
initial baseline migration was authored before it, so existing DBs miss it.
This migration adds it as nullable, backfills to ``reader`` (least
privileged), then enforces NOT NULL and creates the index.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'c2d8e9f01a4b'
down_revision: Union[str, Sequence[str], None] = 'a7b1f0d4e2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite has limited ALTER TABLE support; use batch_alter for portability
    # (Postgres falls through to the native form).
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(
            sa.Column('role', sqlmodel.sql.sqltypes.AutoString(), nullable=True)
        )

    # Backfill existing rows. Reader is the safest default — sysadmins can
    # upgrade individual users via the admin UI afterwards.
    op.execute("UPDATE users SET role = 'reader' WHERE role IS NULL")

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('role', nullable=False, server_default='reader')
        batch_op.create_index(op.f('ix_users_role'), ['role'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index(op.f('ix_users_role'))
        batch_op.drop_column('role')
