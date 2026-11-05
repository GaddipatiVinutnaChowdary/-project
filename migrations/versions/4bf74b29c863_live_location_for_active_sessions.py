"""Add consent-scoped live locations for active presence sessions.

Revision ID: 4bf74b29c863
Revises: 69a0cbbafe6e
Create Date: 2026-11-05 15:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "4bf74b29c863"
down_revision = "69a0cbbafe6e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "presence_live_locations",
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("accuracy_m", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("demo_record", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["presence_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["campus_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("ix_presence_live_locations_student_id", "presence_live_locations", ["student_id"])
    op.create_index("ix_presence_live_locations_updated_at", "presence_live_locations", ["updated_at"])


def downgrade():
    op.drop_index("ix_presence_live_locations_updated_at", table_name="presence_live_locations")
    op.drop_index("ix_presence_live_locations_student_id", table_name="presence_live_locations")
    op.drop_table("presence_live_locations")
