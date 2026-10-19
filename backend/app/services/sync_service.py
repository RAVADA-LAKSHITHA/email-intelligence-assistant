import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from threading import Lock

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.models.email import Email
from app.services.gmail import fetch_recent_emails
from app.services.gemini_service import analyze_email

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_FAILURES = 3  # stop early if Gemini is clearly struggling

# Progress of each user's sync, kept in memory. It is lost when the server restarts.
_jobs: dict[int, dict] = {}
_lock = Lock()


def _parse_gmail_date(raw: str | None) -> datetime | None:
    """Gmail 'Date' header (RFC 2822 text) -> naive UTC datetime."""
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def get_status(user_id: int) -> dict:
    with _lock:
        return dict(_jobs.get(user_id, {"status": "idle"}))


def start_job(user_id: int) -> bool:
    """Marks a sync as running. Returns False if one is already running."""
    with _lock:
        job = _jobs.get(user_id)
        if job and job["status"] == "running":
            return False
        _jobs[user_id] = {
            "status": "running",
            "total": 0,
            "processed": 0,
            "new_saved": 0,
            "failed": 0,
            "stopped_early": False,
            "error": None,
        }
        return True


def _update(user_id: int, **changes) -> None:
    with _lock:
        _jobs[user_id].update(changes)


def run_sync(user_id: int) -> None:
    """Runs in the background: fetch from Gmail, analyze new emails with Gemini, save them."""
    db = SessionLocal()  # the background job needs its own database session
    try:
        user = db.get(User, user_id)
        if not user or not user.oauth_token:
            raise RuntimeError("User not found or not logged in")
        token = user.oauth_token

        fetched = fetch_recent_emails(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            count=10,
        )

        ids = [m["id"] for m in fetched]
        existing = {
            row[0] for row in db.query(Email.gmail_id).filter(Email.gmail_id.in_(ids)).all()
        }
        new_msgs = [m for m in fetched if m["id"] not in existing]
        _update(user_id, total=len(new_msgs))

        new_count = 0
        failed_count = 0
        consecutive_failures = 0
        stopped_early = False

        for msg in new_msgs:
            analysis = analyze_email(
                subject=msg["subject"],
                sender=msg["sender"],
                body=msg["body"],
                snippet=msg["snippet"],
                received_at=msg["date"],
            )

            if analysis is None:
                failed_count += 1
                consecutive_failures += 1
                _update(user_id, processed=new_count + failed_count, failed=failed_count)
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    stopped_early = True
                    break
                continue
            consecutive_failures = 0

            deadline_value = None
            if analysis.get("deadline"):
                try:
                    deadline_value = datetime.fromisoformat(analysis["deadline"])
                except (ValueError, TypeError):
                    deadline_value = None

            db.add(Email(
                user_id=user_id,
                gmail_id=msg["id"],
                thread_id=msg["thread_id"],
                subject=msg["subject"],
                sender=msg["sender"],
                snippet=msg["snippet"],
                body=msg["body"],
                received_at=_parse_gmail_date(msg["date"]),
                labels=msg["labels"],
                category=analysis["category"],
                summary=analysis.get("summary"),
                has_action_item=bool(analysis.get("has_action_item")),
                action_item_description=analysis.get("action_item_description"),
                deadline=deadline_value,
            ))
            db.commit()  # save each email right away, so progress is never lost
            new_count += 1
            _update(user_id, processed=new_count + failed_count, new_saved=new_count)

        _update(user_id, status="done", stopped_early=stopped_early)

    except Exception as exc:
        logger.exception("Sync failed for user %s", user_id)
        text = str(exc)
        if "invalid_grant" in text:
            text = "Gmail access expired. Log out and connect Gmail again."
        _update(user_id, status="error", error=text)
    finally:
        db.close()