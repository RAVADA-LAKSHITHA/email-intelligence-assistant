from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.email import Email
from app.services.gmail import fetch_recent_emails

router = APIRouter(prefix="/api/emails", tags=["emails"])


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
    for msg in fetched:
        exists = db.query(Email).filter(Email.gmail_id == msg["id"]).first()
        if exists:
            continue

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
        ))
        new_count += 1

    db.commit()
    return {"fetched": len(fetched), "new_saved": new_count}


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
    return {"count": len(emails), "emails": emails}