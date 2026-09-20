from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.services.google_auth import get_authorization_url, exchange_code_for_credentials
from app.services.gmail import fetch_recent_emails

router = APIRouter(prefix="/api/auth/google", tags=["auth"])


@router.get("/login")
def login():
    """Step 1: redirect the browser to Google's consent screen."""
    authorization_url, state, code_verifier = get_authorization_url()

    response = RedirectResponse(authorization_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,
    )
    response.set_cookie(
        key="oauth_code_verifier",
        value=code_verifier,
        httponly=True,
        max_age=600,
    )
    return response


@router.get("/callback")
def callback(request: Request, code: str | None = None, state: str | None = None):
    """Step 2: Google redirects here with a `code`. Exchange it for tokens."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    cookie_state = request.cookies.get("oauth_state")
    code_verifier = request.cookies.get("oauth_code_verifier")

    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Missing code verifier cookie")

    credentials = exchange_code_for_credentials(code, code_verifier)

    print("ACCESS TOKEN:", credentials.token)
    print("REFRESH TOKEN:", credentials.refresh_token)

    response = RedirectResponse(f"{settings.FRONTEND_URL}?login=success")
    response.delete_cookie("oauth_state")
    response.delete_cookie("oauth_code_verifier")
    return response

@router.get("/test-fetch")
def test_fetch(access_token: str, refresh_token: str):
    """TEMPORARY debug endpoint — paste tokens from the callback console output."""
    emails = fetch_recent_emails(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        count=5,
    )
    return {"count": len(emails), "emails": emails}