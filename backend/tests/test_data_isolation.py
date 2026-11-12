from datetime import datetime, timedelta, timezone


def test_each_user_only_sees_their_own_emails(client, make_user, make_email, login):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    make_email(alice, subject="Alice's email")
    make_email(bob, subject="Bob's email")

    login(alice)
    subjects = [e["subject"] for e in client.get("/api/emails").json()["emails"]]
    assert subjects == ["Alice's email"]


def test_cannot_open_another_users_email(client, make_user, make_email, login):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    bobs_email = make_email(bob, subject="Private")

    login(alice)
    assert client.get(f"/api/emails/{bobs_email.id}").status_code == 404
    assert client.post(f"/api/emails/{bobs_email.id}/draft-reply").status_code == 404


def test_you_can_open_your_own_email(client, make_user, make_email, login):
    alice = make_user("alice@example.com")
    mine = make_email(alice, subject="Mine")

    login(alice)
    response = client.get(f"/api/emails/{mine.id}")
    assert response.status_code == 200
    assert response.json()["subject"] == "Mine"


def test_stats_count_only_your_own_emails(client, make_user, make_email, login):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    make_email(alice, category="Work")
    make_email(alice, category="Work")
    make_email(alice, category="Finance")
    make_email(bob, category="Work")

    login(alice)
    assert client.get("/api/emails/stats").json() == {
        "total": 3,
        "by_category": {"Work": 2, "Finance": 1},
    }


def test_unknown_category_is_rejected(client, make_user, login):
    login(make_user())
    response = client.get("/api/emails", params={"category": "Banana"})
    assert response.status_code == 400


def test_category_and_action_filters(client, make_user, make_email, login):
    user = make_user()
    make_email(user, subject="Task", category="Work", has_action_item=True)
    make_email(user, subject="Ad", category="Promotions")
    login(user)

    def subjects(**params):
        return [e["subject"] for e in client.get("/api/emails", params=params).json()["emails"]]

    assert subjects(category="Work") == ["Task"]
    assert subjects(action_only="true") == ["Task"]
    assert subjects(category="Promotions", action_only="true") == []


def test_tasks_are_sorted_by_deadline_and_flag_overdue(client, make_user, make_email, login):
    user = make_user()
    today = datetime.now(timezone.utc).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
    make_email(user, subject="Later", has_action_item=True, deadline=today + timedelta(days=5))
    make_email(user, subject="Overdue", has_action_item=True, deadline=today - timedelta(days=3))
    make_email(user, subject="No deadline", has_action_item=True, deadline=None)
    make_email(user, subject="Not a task", has_action_item=False)

    login(user)
    data = client.get("/api/tasks").json()
    assert [t["subject"] for t in data["tasks"]] == ["Overdue", "Later", "No deadline"]
    assert data["count"] == 3
    assert data["overdue_count"] == 1
    assert data["tasks"][0]["overdue"] is True