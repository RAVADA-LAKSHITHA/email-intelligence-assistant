from datetime import datetime, timedelta, timezone


def hours_ago(hours):
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)


def test_digest_with_no_recent_emails_does_not_call_the_ai(client, make_user, login, monkeypatch):
    def boom(items):
        raise AssertionError("the AI should not be called")

    monkeypatch.setattr("app.api.emails.generate_digest", boom)
    login(make_user())
    data = client.get("/api/emails/digest", params={"hours": 24}).json()
    assert data["email_count"] == 0


def test_digest_counts_recent_emails_and_returns_the_ai_text(
    client, make_user, make_email, login, monkeypatch
):
    user = make_user()
    make_email(user, has_action_item=True, received_at=hours_ago(1))
    make_email(user, has_action_item=False, received_at=hours_ago(2))
    make_email(user, received_at=hours_ago(500))  # too old for a 24 hour digest
    monkeypatch.setattr("app.api.emails.generate_digest", lambda items: "Digest text")

    login(user)
    data = client.get("/api/emails/digest", params={"hours": 24}).json()
    assert data == {"email_count": 2, "action_count": 1, "digest": "Digest text"}


def test_digest_ai_failure_gives_503(client, make_user, make_email, login, monkeypatch):
    user = make_user()
    make_email(user, received_at=hours_ago(1))
    monkeypatch.setattr("app.api.emails.generate_digest", lambda items: None)

    login(user)
    assert client.get("/api/emails/digest", params={"hours": 24}).status_code == 503


def test_draft_reply_returns_a_draft(client, make_user, make_email, login, monkeypatch):
    user = make_user()
    email = make_email(user)
    monkeypatch.setattr("app.api.emails.generate_reply_draft", lambda **kwargs: "Draft text")

    login(user)
    response = client.post(f"/api/emails/{email.id}/draft-reply", params={"tone": "brief"})
    assert response.status_code == 200
    assert response.json() == {"draft": "Draft text", "tone": "brief"}


def test_draft_reply_rejects_an_unknown_tone(client, make_user, make_email, login):
    user = make_user()
    email = make_email(user)
    login(user)
    response = client.post(f"/api/emails/{email.id}/draft-reply", params={"tone": "angry"})
    assert response.status_code == 400


def test_draft_reply_ai_failure_gives_503(client, make_user, make_email, login, monkeypatch):
    user = make_user()
    email = make_email(user)
    monkeypatch.setattr("app.api.emails.generate_reply_draft", lambda **kwargs: None)

    login(user)
    assert client.post(f"/api/emails/{email.id}/draft-reply").status_code == 503