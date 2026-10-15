"""received_at datetime and boolean action flag

Revision ID: 7f1c10b7a683
Revises: 5503f7c238d4
Create Date: 2026-10-15 11:22:09.966378

"""
from datetime import timezone
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
    """Old Gmail date text -> 'YYYY-MM-DD HH:MM:SS.ffffff' (UTC), or None."""
    if not isinstance(raw, str):
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def upgrade() -> None:
    """Upgrade schema."""
    # 1) change column types (SQLite needs batch mode: it rebuilds the table)
    with op.batch_alter_table("emails") as batch:
        batch.alter_column("received_at", type_=sa.DateTime())
        batch.alter_column("has_action_item", type_=sa.Boolean())

    # 2) convert the old text values already stored in the rows
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, received_at, has_action_item FROM emails")
    ).fetchall()
    for row_id, received_raw, flag_raw in rows:
        flag = 1 if str(flag_raw).strip().lower() in ("true", "1") else 0
        bind.execute(
            sa.text("UPDATE emails SET received_at = :r, has_action_item = :f WHERE id = :id"),
            {"r": _parse(received_raw), "f": flag, "id": row_id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    bind.execute(sa.text(
        "UPDATE emails SET has_action_item = "
        "CASE WHEN has_action_item = 1 THEN 'True' ELSE 'False' END"
    ))
    with op.batch_alter_table("emails") as batch:
        batch.alter_column("received_at", type_=sa.String())
        batch.alter_column("has_action_item", type_=sa.String())