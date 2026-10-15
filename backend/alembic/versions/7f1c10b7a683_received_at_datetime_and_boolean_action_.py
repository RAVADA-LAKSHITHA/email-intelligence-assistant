"""received_at datetime and boolean action flag

Revision ID: 7f1c10b7a683
Revises: 5503f7c238d4
Create Date: 2026-10-15 11:22:09.966378

"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f1c10b7a683'
down_revision: Union[str, Sequence[str], None] = '5503f7c238d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _parse(raw):
    """Old date text -> 'YYYY-MM-DD HH:MM:SS.ffffff' (UTC), or None."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    dt = None
    try:
        dt = parsedate_to_datetime(raw)          # Gmail style: "Mon, 13 Oct 2025 ..."
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw)     # fallback: ISO text
        except ValueError:
            return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def upgrade() -> None:
    # 1) add NEW typed columns next to the old text ones (no CAST involved)
    op.add_column("emails", sa.Column("received_at_new", sa.DateTime(), nullable=True))
    op.add_column(
        "emails",
        sa.Column("has_action_item_new", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # 2) fill them from the old text values
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, received_at, has_action_item FROM emails")
    ).fetchall()
    for row_id, received_raw, flag_raw in rows:
        flag = 1 if str(flag_raw).strip().lower() in ("true", "1") else 0
        bind.execute(
            sa.text(
                "UPDATE emails SET received_at_new = :r, has_action_item_new = :f WHERE id = :id"
            ),
            {"r": _parse(received_raw), "f": flag, "id": row_id},
        )

    # 3) drop the old columns and give the new ones the old names
    with op.batch_alter_table("emails") as batch:
        batch.drop_column("received_at")
        batch.drop_column("has_action_item")
        batch.alter_column("received_at_new", new_column_name="received_at")
        batch.alter_column("has_action_item_new", new_column_name="has_action_item")


def downgrade() -> None:
    op.add_column("emails", sa.Column("received_at_old", sa.String(), nullable=True))
    op.add_column("emails", sa.Column("has_action_item_old", sa.String(), nullable=True))
    op.execute(
        "UPDATE emails SET received_at_old = received_at, "
        "has_action_item_old = CASE WHEN has_action_item = 1 THEN 'True' ELSE 'False' END"
    )
    with op.batch_alter_table("emails") as batch:
        batch.drop_column("received_at")
        batch.drop_column("has_action_item")
        batch.alter_column("received_at_old", new_column_name="received_at")
        batch.alter_column("has_action_item_old", new_column_name="has_action_item")