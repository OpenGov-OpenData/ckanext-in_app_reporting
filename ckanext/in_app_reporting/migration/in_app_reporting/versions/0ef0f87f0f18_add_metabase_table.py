"""add metabase table

Revision ID: 0ef0f87f0f18
Revises: 
Create Date: 2025-05-28 21:03:28.941186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ef0f87f0f18'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    if "metabase_mapping" not in tables:
        op.create_table(
            "metabase_mapping",
            sa.Column("user_id", sa.UnicodeText, primary_key=True),
            sa.Column("platform_uuid", sa.UnicodeText, nullable=False),
            sa.Column("email", sa.UnicodeText, nullable=False),
            sa.Column("group_ids", sa.UnicodeText, default=None),
            sa.Column("collection_ids", sa.UnicodeText, default=None),
            sa.Column("created", sa.DateTime),
            sa.Column("modified", sa.DateTime),
        )


def downgrade():
    op.drop_table("metabase_mapping")
