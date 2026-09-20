from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.oauth_token import OAuthToken


def get_or_create_user(db: Session, email: str) -> User:
    """Finds an existing user by email, or creates one."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_tokens(db: Session, user: User, access_token: str, refresh_token: str, expires_in: int | None = None) -> OAuthToken:
    """Creates or updates the single OAuthToken row for this user."""
    expires_at = None
    if expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    token_row = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()

    if token_row:
        token_row.access_token = access_token
        if refresh_token:
            token_row.refresh_token = refresh_token
        token_row.expires_at = expires_at
    else:
        token_row = OAuthToken(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        db.add(token_row)

    db.commit()
    db.refresh(token_row)
    return token_row