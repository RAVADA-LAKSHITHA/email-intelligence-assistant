from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from app.core.config import settings
import requests

# Scopes must match exactly what you configured on the OAuth consent screen.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _client_config() -> dict:
    """Builds the client config dict the Flow object expects,
    without needing a downloaded client_secret.json file."""
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }


def build_flow() -> Flow:
    """Creates a fresh OAuth flow object for one login attempt."""
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return flow


def get_authorization_url() -> tuple[str, str, str]:
    """Returns (url_to_redirect_user_to, state_token, code_verifier)."""
    flow = build_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url, state, flow.code_verifier


def exchange_code_for_credentials(code: str, code_verifier: str) -> Credentials:
    """Swaps the temporary authorization code for real access/refresh tokens."""
    flow = build_flow()
    flow.code_verifier = code_verifier  # restore the PKCE verifier from /login
    flow.fetch_token(code=code)
    return flow.credentials

def get_user_email(access_token: str) -> str:
    """Calls Google's userinfo endpoint to get the logged-in user's email."""
    response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()["email"]