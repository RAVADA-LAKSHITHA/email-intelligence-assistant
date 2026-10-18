from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.email import Email

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
def list_tasks(email: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rows = (
        db.query(Email)
        .filter(Email.user_id == user.id, Email.has_action_item.is_(True))
        .order_by(Email.deadline.asc().nulls_last(), Email.received_at.desc())
        .all()
    )

    today = datetime.now(timezone.utc).date()
    tasks = [
        {
            "email_id": e.id,
            "task": e.action_item_description or e.subject,
            "subject": e.subject,
            "sender": e.sender,
            "category": e.category,
            "deadline": e.deadline,
            "overdue": bool(e.deadline and e.deadline.date() < today),
            "received_at": e.received_at,
        }
        for e in rows
    ]

    return {
        "count": len(tasks),
        "overdue_count": sum(1 for t in tasks if t["overdue"]),
        "tasks": tasks,
    }