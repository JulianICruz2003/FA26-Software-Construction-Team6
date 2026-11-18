"""Add optional deadline and team name to projects."""
from alembic import op
import sqlalchemy as sa


revision = "b7e3a91c42d0"
down_revision = "c4d8bdf07474"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("deadline", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("team_name", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "team_name")
    op.drop_column("projects", "deadline")
