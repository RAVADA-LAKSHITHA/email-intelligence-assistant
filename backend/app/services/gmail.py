import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.services.google_auth import SCOPES


def get_gmail_service(access_token: str, refresh_token: str, client_id: str, client_secret: str):
    """Builds an authenticated Gmail API client from stored token values."""
    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=credentials)


def list_message_ids(service, max_results: int = 10) -> list[str]:
    """Step 1: get a page of message IDs from the inbox."""
    result = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"],
    ).execute()
    messages = result.get("messages", [])
    return [m["id"] for m in messages]


def _get_header(headers: list[dict], name: str) -> str | None:
    """Gmail returns headers as a flat list of {name, value} — this pulls one out."""
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return None


def _extract_plain_text_body(payload: dict) -> str:
    """Gmail nests the body in different shapes depending on whether the
    email is plain text, HTML, or multipart. This walks the structure to
    find a text/plain part and decodes it from base64url."""

    def decode(data: str) -> str:
        return base64.urlsafe_b64decode(data.encode("UTF-8")).decode("UTF-8", errors="replace")

    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return decode(payload["body"]["data"])

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return decode(part["body"]["data"])
        # Recurse for nested multipart (e.g. multipart/alternative inside multipart/mixed)
        if part.get("parts"):
            found = _extract_plain_text_body(part)
            if found:
                return found

    return ""


def get_message_detail(service, message_id: str) -> dict:
    """Step 2: fetch one message's full content and pull out the useful fields."""
    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()

    headers = message["payload"]["headers"]

    return {
        "id": message["id"],
        "thread_id": message["threadId"],
        "subject": _get_header(headers, "Subject") or "(no subject)",
        "sender": _get_header(headers, "From") or "(unknown sender)",
        "date": _get_header(headers, "Date"),
        "snippet": message.get("snippet", ""),
        "body": _extract_plain_text_body(message["payload"]),
        "labels": message.get("labelIds", []),
    }


def fetch_recent_emails(access_token: str, refresh_token: str, client_id: str, client_secret: str, count: int = 10) -> list[dict]:
    """Convenience wrapper: builds the service, lists IDs, fetches details for each."""
    service = get_gmail_service(access_token, refresh_token, client_id, client_secret)
    message_ids = list_message_ids(service, max_results=count)
    return [get_message_detail(service, mid) for mid in message_ids]