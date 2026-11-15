import json

import pytest

from app.core.config import settings
from app.services import gemini_service


class FakeResponse:
    def __init__(self, text):
        self.text = text


def fake_gemini(monkeypatch, reply):
    """Replaces the real Gemini call.

    `reply` is the text to return, or an Exception to raise.
    Returns a list that collects every prompt the code tried to send.
    """
    prompts = []

    def fake_generate(prompt, json_mode=True):
        prompts.append(prompt)
        if isinstance(reply, Exception):
            raise reply
        return FakeResponse(reply)

    monkeypatch.setattr(gemini_service, "_generate", fake_generate)
    return prompts


GOOD_REPLY = json.dumps(
    {
        "category": "Finance",
        "summary": "Pay the bill.",
        "has_action_item": True,
        "action_item_description": "Pay the electricity bill",
        "deadline": "2026-12-01",
    }
)


def analyze(**overrides):
    args = {
        "subject": "Bill due",
        "sender": "power@example.com",
        "body": "Please pay by 1 December.",
        "snippet": "Please pay",
        "received_at": "Mon, 16 Nov 2026 10:00:00 +0530",
    }
    args.update(overrides)
    return gemini_service.analyze_email(**args)


# ---------- Reading Gemini's answer ----------


def test_analyze_email_returns_the_ai_fields(monkeypatch):
    fake_gemini(monkeypatch, GOOD_REPLY)
    result = analyze()
    assert result["category"] == "Finance"
    assert result["has_action_item"] is True
    assert result["deadline"] == "2026-12-01"


def test_unknown_category_becomes_other(monkeypatch):
    fake_gemini(
        monkeypatch,
        json.dumps({"category": "Banana", "summary": "x", "has_action_item": False}),
    )
    assert analyze()["category"] == "Other"


def test_bad_json_returns_none(monkeypatch):
    fake_gemini(monkeypatch, "this is not json")
    assert analyze() is None


def test_json_that_is_not_an_object_returns_none(monkeypatch):
    fake_gemini(monkeypatch, json.dumps(["a", "list"]))
    assert analyze() is None


def test_gemini_error_returns_none(monkeypatch):
    fake_gemini(monkeypatch, RuntimeError("Gemini is down"))
    assert analyze() is None


# ---------- What we send to Gemini ----------


def test_empty_body_falls_back_to_the_snippet(monkeypatch):
    prompts = fake_gemini(monkeypatch, GOOD_REPLY)
    analyze(body="", snippet="UNIQUE-SNIPPET-TEXT")
    assert "UNIQUE-SNIPPET-TEXT" in prompts[0]


def test_prompt_contains_the_sent_date_and_the_code_rule(monkeypatch):
    prompts = fake_gemini(monkeypatch, GOOD_REPLY)
    analyze(received_at="Mon, 16 Nov 2026 10:00:00 +0530")
    assert "Mon, 16 Nov 2026 10:00:00 +0530" in prompts[0]
    assert "one-time" in prompts[0].lower()


def test_very_long_emails_are_cut_short(monkeypatch):
    prompts = fake_gemini(monkeypatch, GOOD_REPLY)
    analyze(body="x" * 50000)
    assert len(prompts[0]) < 12000


# ---------- Retrying when Gemini is busy ----------


class FlakyModels:
    """Pretends to be Gemini: fails a few times, then works."""

    def __init__(self, failures, code):
        self.failures = failures
        self.code = code
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            error = Exception("temporary problem")
            error.code = self.code
            raise error
        return FakeResponse("{}")


class FakeClient:
    def __init__(self, models):
        self.models = models


@pytest.fixture()
def fast_retries(monkeypatch):
    """No real waiting in tests."""
    monkeypatch.setattr(gemini_service.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(settings, "GEMINI_MIN_INTERVAL_SECONDS", 0)


def test_busy_errors_are_retried_until_success(monkeypatch, fast_retries):
    models = FlakyModels(failures=2, code=503)
    monkeypatch.setattr(gemini_service, "client", FakeClient(models))
    response = gemini_service._generate("hello")
    assert response.text == "{}"
    assert models.calls == 3


def test_rate_limit_errors_are_retried(monkeypatch, fast_retries):
    models = FlakyModels(failures=1, code=429)
    monkeypatch.setattr(gemini_service, "client", FakeClient(models))
    gemini_service._generate("hello")
    assert models.calls == 2


def test_permanent_errors_are_not_retried(monkeypatch, fast_retries):
    models = FlakyModels(failures=5, code=400)
    monkeypatch.setattr(gemini_service, "client", FakeClient(models))
    with pytest.raises(Exception):
        gemini_service._generate("hello")
    assert models.calls == 1


def test_gives_up_after_the_last_retry(monkeypatch, fast_retries):
    models = FlakyModels(failures=99, code=503)
    monkeypatch.setattr(gemini_service, "client", FakeClient(models))
    with pytest.raises(Exception):
        gemini_service._generate("hello")
    assert models.calls == len(gemini_service.RETRY_DELAYS) + 1


# ---------- Digest and draft replies ----------


def test_digest_returns_the_text(monkeypatch):
    fake_gemini(monkeypatch, "  Three emails need action.  ")
    assert gemini_service.generate_digest([{"subject": "x"}]) == "Three emails need action."


def test_digest_failure_returns_none(monkeypatch):
    fake_gemini(monkeypatch, RuntimeError("down"))
    assert gemini_service.generate_digest([{"subject": "x"}]) is None


def test_reply_draft_uses_the_tone_and_fences_the_email(monkeypatch):
    prompts = fake_gemini(monkeypatch, "Hi, thanks!")
    draft = gemini_service.generate_reply_draft("Subject", "a@b.com", "Body text", "", "friendly")
    assert draft == "Hi, thanks!"
    assert "warm and friendly" in prompts[0]
    assert "<email>" in prompts[0]
    assert "untrusted" in prompts[0]