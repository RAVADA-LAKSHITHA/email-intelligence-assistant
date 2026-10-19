from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.email import Email
from app.services.gemini_service import generate_digest, VALID_CATEGORIES
from app.services.sync_service import start_job, run_sync, get_status

router = APIRouter(prefix="/api/emails", tags=["emails"])


def _get_user_or_404(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/sync")
def start_sync(
    background_tasks: BackgroundTasks,
    email: str = Query(..., description="Logged-in user's email"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.oauth_token:
        raise HTTPException(status_code=404, detail="User not found or not logged in")

    if not start_job(user.id):
        return {"status": "already_running"}

    background_tasks.add_task(run_sync, user.id)
    return {"status": "started"}


@router.get("/sync/status")
def sync_status(email: str = Query(...), db: Session = Depends(get_db)):
    user = _get_user_or_404(db, email)
    return get_status(user.id)


@router.get("")
def list_emails(
    email: str = Query(...),
    category: str | None = Query(None, description="Optional: only show this category"),
    action_only: bool = Query(False, description="If true, only emails that need action"),
    db: Session = Depends(get_db),
):
    user = _get_user_or_404(db, email)

    if category is not None and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category '{category}'. Valid: {VALID_CATEGORIES}",
        )

    query = db.query(Email).filter(Email.user_id == user.id)
    if category:
        query = query.filter(Email.category == category)
    if action_only:
        query = query.filter(Email.has_action_item.is_(True))

    emails = query.order_by(Email.received_at.desc().nulls_last()).all()
    return {
        "count": len(emails),
        "emails": [
            {
                "id": e.id,
                "subject": e.subject,
                "sender": e.sender,
                "received_at": e.received_at,
                "category": e.category,
                "summary": e.summary,
                "has_action_item": e.has_action_item,
                "deadline": e.deadline,
            }
            for e in emails
        ],
    }


@router.get("/stats")
def email_stats(email: str = Query(...), db: Session = Depends(get_db)):
    user = _get_user_or_404(db, email)

    rows = (
        db.query(Email.category, func.count(Email.id))
        .filter(Email.user_id == user.id)
        .group_by(Email.category)
        .all()
    )
    return {
        "total": sum(count for _, count in rows),
        "by_category": {cat or "Uncategorized": count for cat, count in rows},
    }


@router.get("/digest")
def email_digest(
    email: str = Query(...),
    hours: int = Query(24, ge=1, le=720, description="Look back this many hours"),
    db: Session = Depends(get_db),
):
    user = _get_user_or_404(db, email)

    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    rows = (
        db.query(Email)
        .filter(Email.user_id == user.id, Email.received_at >= since)
        .order_by(Email.received_at.desc())
        .limit(50)
        .all()
    )

    if not rows:
        return {"email_count": 0, "action_count": 0, "digest": "No emails in this time range."}

    items = [
        {
            "subject": e.subject,
            "category": e.category,
            "summary": e.summary,
            "needs_action": e.has_action_item,
            "deadline": e.deadline.date().isoformat() if e.deadline else None,
        }
        for e in rows
    ]

    digest = generate_digest(items)
    if digest is None:
        raise HTTPException(
            status_code=503,
            detail="Could not generate the digest right now. Try again in a minute.",
        )

    return {
        "email_count": len(rows),
        "action_count": sum(1 for e in rows if e.has_action_item),
        "digest": digest,
    }


@router.get("/{email_id}")
def get_email(
    email_id: int,
    email: str = Query(..., description="Logged-in user's email"),
    db: Session = Depends(get_db),
):
    user = _get_user_or_404(db, email)

    item = (
        db.query(Email)
        .filter(Email.id == email_id, Email.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Email not found")

    return {
        "id": item.id,
        "gmail_id": item.gmail_id,
        "thread_id": item.thread_id,
        "subject": item.subject,
        "sender": item.sender,
        "received_at": item.received_at,
        "labels": item.labels,
        "category": item.category,
        "summary": item.summary,
        "has_action_item": item.has_action_item,
        "action_item_description": item.action_item_description,
        "deadline": item.deadline,
        "snippet": item.snippet,
        "body": item.body,
    }