"""Add unique constraint on profiles.user_id.

Deletes duplicate profile rows (keeping the newest per user_id) before
adding the constraint, since dev/prod data may already contain duplicates
from issue #92.

Revision ID: 003
Revises: 002
Create Date: 2026-07-26 00:00:00.000000
"""

from alembic import op  # type: ignore[attr-defined]

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the newest row per user_id, delete the rest, so the unique
    # constraint below doesn't fail on existing duplicate profiles.
    op.execute(
        """
        DELETE FROM profiles
        WHERE id NOT IN (
            SELECT DISTINCT ON (user_id) id
            FROM profiles
            ORDER BY user_id, created_at DESC
        )
        """
    )
    op.create_unique_constraint("uq_profiles_user_id", "profiles", ["user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_profiles_user_id", "profiles", type_="unique")
