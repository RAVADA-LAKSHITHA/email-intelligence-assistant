from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.email import Email
from app.services.gmail import fetch_recent_emails
from app.services.gemini_service import analyze_email

router = APIRouter(prefix="/api/emails", tags=["emails"])
MAX_CONSECUTIVE_FAILURES = 3  # stop early if Gemini is clearly struggling


@router.post("/sync")
def sync_emails(email: str = Query(..., description="Logged-in user's email"), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.oauth_token:
        raise HTTPException(status_code=404, detail="User not found or not logged in")

    token = user.oauth_token

    fetched = fetch_recent_emails(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        count=10,
    )

    new_count = 0
    failed_count = 0
    consecutive_failures = 0
    stopped_early = False

    for msg in fetched:
        exists = db.query(Email).filter(Email.gmail_id == msg["id"]).first()
        if exists:
            continue

        analysis = analyze_email(
            subject=msg["subject"],
            sender=msg["sender"],
            body=msg["body"],
            snippet=msg["snippet"],
            received_at=msg["date"]
        )
        if analysis is None:
            failed_count += 1  # not saved, so the next sync retries it
            consecutive_failures += 1
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
            user_id=user.id,
            gmail_id=msg["id"],
            thread_id=msg["thread_id"],
            subject=msg["subject"],
            sender=msg["sender"],
            snippet=msg["snippet"],
            body=msg["body"],
            received_at=msg["date"],
            labels=msg["labels"],
            category=analysis["category"],
            summary=analysis.get("summary"),
            has_action_item=str(bool(analysis.get("has_action_item"))),
            deadline=deadline_value,
        ))
        new_count += 1

    db.commit()
    return {
        "fetched": len(fetched),
        "new_saved": new_count,
        "failed": failed_count,
        "stopped_early": stopped_early,
    }

@router.get("")
def list_emails(email: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    emails = (
        db.query(Email)
        .filter(Email.user_id == user.id)
        .order_by(Email.fetched_at.desc())
        .all()
    )
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