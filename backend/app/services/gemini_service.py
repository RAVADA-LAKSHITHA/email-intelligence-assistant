import json
import logging
import time

from google import genai
from google.genai import types
from datetime import datetime, timezone

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
  "has_action_item": true or false,
  "action_item_description": a short phrase describing the action needed, or null if has_action_item is false,
  "deadline": an ISO 8601 date (YYYY-MM-DD) or null
}}

Category guide:
- Promotions: marketing, offers, discounts, newsletters, and engagement nudges from apps and services (streak reminders, "try our new feature", trial offers).
- Finance: bank statements, transactions, bills, payment and tax notices.
- Security: sign-in alerts, password and 2-step verification notices.
- Work: messages about jobs, internships, interviews, or colleagues.
- Education: courses, assignments, exams, and college or learning-platform notices that are not marketing.
- Personal: messages from real people such as friends and family.
- Social: social network notifications.
- Spam: unsolicited or suspicious mail.
- Other: anything else.

Rules for has_action_item: true ONLY if the recipient genuinely needs to do something specific, such as pay a bill, reply to a person, attend a meeting, submit something, or secure their account. Marketing calls to action ("try now", "claim offer", "keep your streak") are NOT action items, so use false for them.

Rules for deadline: set a date ONLY when has_action_item is true and the email gives a real due date or event date. Offer expiry dates in marketing emails are not deadlines, so use null. This email was sent on {sent}. Resolve relative dates such as "today" or "this Friday" against that sent date, not against today's date.

Email subject: {subject}
Email sender: {sender}
Email sent: {sent}
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


def _generate(prompt: str, json_mode: bool = True):
    """Calls Gemini, retrying temporary failures with growing waits."""
    config = (
        types.GenerateContentConfig(response_mime_type="application/json")
        if json_mode
        else types.GenerateContentConfig()
    )
    for attempt in range(len(RETRY_DELAYS) + 1):
        _throttle()
        try:
            return client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            code = getattr(exc, "code", None)
            if code not in RETRYABLE_CODES or attempt == len(RETRY_DELAYS):
                raise
            delay = RETRY_DELAYS[attempt]
            logger.warning("Gemini returned %s, retrying in %ss", code, delay)
            time.sleep(delay)


def analyze_email(subject: str, sender: str, body: str, snippet: str, received_at: str | None = None) -> dict | None:
    """Sends one email to Gemini. Returns the analysis dict, or None if anything fails."""

    content = body.strip() if body and body.strip() else (snippet or "")

    prompt = ANALYSIS_PROMPT.format(
        categories=VALID_CATEGORIES,
        sent=received_at or "unknown",
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

DIGEST_PROMPT = """You are an assistant that writes a short digest of someone's recent emails.

Below is a JSON list of emails. Each has a subject, a category, a one-line summary, whether it needs action, and an optional deadline.

Write the digest as plain text, at most 5 short lines:
- Line 1: one sentence on the overall picture (how many emails, what kinds).
- Then list what the person must do, with deadlines, most urgent first. Skip this if nothing needs action.
- Finish with one short line about the rest (for example: the remaining emails are promotions).
Do not use markdown symbols. Do not invent anything that is not in the list. Today's date is {today}.

Emails:
{emails_json}
"""


def generate_digest(items: list[dict]) -> str | None:
    """Turns a list of email summaries into one short digest. Returns None on failure."""
    prompt = DIGEST_PROMPT.format(
        today=datetime.now(timezone.utc).date().isoformat(),
        emails_json=json.dumps(items, ensure_ascii=False),
    )
    try:
        response = _generate(prompt, json_mode=False)
        text = (response.text or "").strip()
    except Exception as exc:
        logger.warning("Gemini digest failed: %s", exc)
        return None
    return text or None