from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def create_session_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=settings.SESSION_DAYS)
    payload = {"sub": str(user_id), "exp": expires}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def read_session_token(token: str) -> int | None:
    """Returns the user id if the token is genuine and not expired, otherwise None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None