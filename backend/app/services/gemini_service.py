import json
import logging
import time
from datetime import datetime, timezone

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

VALID_CATEGORIES = [
    "Work", "Personal", "Finance", "Promotions",
    "Security", "Social", "Education", "Spam", "Other",
]

ANALYSIS_PROMPT = """You are an email triage assistant. Analyze the email below and return ONLY a JSON object (no markdown, no code fences, no explanation) with exactly these fields:

{{
  "category": one of {categories},
  "summary": a 1-2 sentence plain-English summary of the email's content,
  "has_action_item": true or false (true if the recipient needs to DO something: reply, pay, attend, complete a task, click a link to act),
  "action_item_description": a short phrase describing the action needed, or null if has_action_item is false,
  "deadline": an ISO 8601 date (YYYY-MM-DD) if the email mentions a specific deadline or date the recipient should act by, or null if there is none
}}

Today's date is {today}. Use it to convert relative dates like "today" or "this Friday" into real dates.

Email subject: {subject}
Email sender: {sender}
Email body:
{body}
"""

# 429 = we are calling too fast, 503 = Google is overloaded. Both are temporary.
# Anything else (400 bad key, 404 bad model) would fail again, so we don't retry it.
RETRYABLE_CODES = {429, 503}
RETRY_DELAYS = [8, 20]  # seconds to wait before retry 1 and retry 2

_last_call_time = 0.0


def _throttle() -> None:
    """Spaces calls out so we stay under the free-tier requests-per-minute limit."""
    global _last_call_time
    wait = settings.GEMINI_MIN_INTERVAL_SECONDS - (time.monotonic() - _last_call_time)
    if wait > 0:
        time.sleep(wait)
    _last_call_time = time.monotonic()


def _generate(prompt: str):
    """Calls Gemini, retrying temporary failures with growing waits."""
    for attempt in range(len(RETRY_DELAYS) + 1):
        _throttle()
        try:
            return client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:
            code = getattr(exc, "code", None)
            if code not in RETRYABLE_CODES or attempt == len(RETRY_DELAYS):
                raise
            delay = RETRY_DELAYS[attempt]
            logger.warning("Gemini returned %s, retrying in %ss", code, delay)
            time.sleep(delay)


def analyze_email(subject: str, sender: str, body: str, snippet: str) -> dict | None:
    """Sends one email to Gemini. Returns the analysis dict, or None if anything fails."""

    content = body.strip() if body and body.strip() else (snippet or "")

    prompt = ANALYSIS_PROMPT.format(
        categories=VALID_CATEGORIES,
        today=datetime.now(timezone.utc).date().isoformat(),
        subject=subject or "(no subject)",
        sender=sender or "(unknown sender)",
        body=content[:6000],
    )

    try:
        response = _generate(prompt)
        result = json.loads(response.text)
    except Exception as exc:
        logger.warning("Gemini analysis failed for %r: %s", subject, exc)
        return None

    if not isinstance(result, dict):
        logger.warning("Gemini returned unexpected shape for %r", subject)
        return None

    if result.get("category") not in VALID_CATEGORIES:
        result["category"] = "Other"

    return result