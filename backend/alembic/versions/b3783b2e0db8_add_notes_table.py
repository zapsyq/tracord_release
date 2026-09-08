"""add_notes_table

Revision ID: b3783b2e0db8
Revises: 6b8c089ded3c
Create Date: 2026-08-08 21:09:26.454327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3783b2e0db8'
down_revision: Union[str, Sequence[str], None] = '6b8c089ded3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('notes',
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('create_time', sa.DateTime(), nullable=False, comment='创建时间'),
    sa.Column('update_time', sa.DateTime(), nullable=False, comment='更新时间'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], name=op.f('fk_notes_trip_id_trips')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notes'))
    )


def downgrade() -> None:
    op.drop_table('notes')
