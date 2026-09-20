from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.google_auth import (
    get_authorization_url,
    exchange_code_for_credentials,
    get_user_email,
)
from app.services.user_service import get_or_create_user, save_tokens

router = APIRouter(prefix="/api/auth/google", tags=["auth"])


@router.get("/login")
def login():
    authorization_url, state, code_verifier = get_authorization_url()

    response = RedirectResponse(authorization_url)
    response.set_cookie(key="oauth_state", value=state, httponly=True, max_age=600)
    response.set_cookie(key="oauth_code_verifier", value=code_verifier, httponly=True, max_age=600)
    return response


@router.get("/callback")
def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    cookie_state = request.cookies.get("oauth_state")
    code_verifier = request.cookies.get("oauth_code_verifier")

    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Missing code verifier cookie")

    credentials = exchange_code_for_credentials(code, code_verifier)
    email = get_user_email(credentials.token)

    user = get_or_create_user(db, email=email)
    save_tokens(
        db,
        user=user,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        expires_in=3600,
    )

    response = RedirectResponse(f"{settings.FRONTEND_URL}?login=success&email={email}")
    response.delete_cookie("oauth_state")
    response.delete_cookie("oauth_code_verifier")
    return response