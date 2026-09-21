import importlib.util
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from test_analytics import canonical_analytics_fixture  # noqa: F401
from test_financial_core import account, headers, register
from test_phase07 import client  # noqa: F401

from app.db.models import Notification, User
from app.notifications.service import (
    _in_quiet_hours,
    evaluate_notifications,
    notification_candidates,
)


class FakeLock:
    def __init__(self, acquired):
        self.acquired = acquired
        self.released = False

    def acquire(self, blocking=False):
        return self.acquired

    def release(self):
        self.released = True


class FakeRedis:
    def __init__(self, lock):
        self.lock_instance = lock

    def lock(self, key, timeout, blocking):
        assert key == "notifications:cycle"
        assert timeout == 55
        return self.lock_instance


def _setup_budget(test_client, auth, limit=10_000):
    account_data = account(test_client, auth, "Notification account", 100_000)
    budget = test_client.post(
        "/api/v1/budgets",
        headers=headers(auth),
        json={
            "name": "September",
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "total_limit": limit,
            "currency": "VND",
        },
    ).json()
    return account_data, budget


def _expense(test_client, auth, account_id, amount, key):
    response = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": key},
        json={
            "type": "EXPENSE",
            "account_id": account_id,
            "amount": amount,
            "currency": "VND",
            "transaction_date": "2026-09-03T12:00:00+00:00",
        },
    )
    assert response.status_code == 201, response.text


def test_budget_thresholds_and_deduplication(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    account_data, budget = _setup_budget(test_client, auth)
    _expense(test_client, auth, account_data["id"], 9_000, "notification-budget")
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        candidates = notification_candidates(db, user, date(2026, 9, 1), date(2026, 9, 30), "VND")
        budget_candidate = next(
            item
            for item in candidates
            if item["subject_id"] == budget["id"] and item["rule_id"] == "budget_90"
        )
        assert budget_candidate["rule_id"] == "budget_90"
        created = evaluate_notifications(
            db,
            user,
            date(2026, 9, 1),
            date(2026, 9, 30),
            "VND",
            now=datetime(2026, 9, 3, 12, tzinfo=timezone.utc),
        )
        assert {item.rule_id for item in created} == {"budget_80", "budget_90"}
        assert (
            evaluate_notifications(
                db,
                user,
                date(2026, 9, 1),
                date(2026, 9, 30),
                "VND",
                now=datetime(2026, 9, 3, 12, tzinfo=timezone.utc),
            )
            == []
        )


def test_preferences_quiet_hours_cap_and_critical_bypass(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    account_data, _ = _setup_budget(test_client, auth)
    _expense(test_client, auth, account_data["id"], 8_000, "notification-cap")
    preferences = test_client.patch(
        "/api/v1/preferences/notifications",
        headers=headers(auth),
        json={
            "max_notifications_per_day": 1,
            "quiet_hours_start": "09:00",
            "quiet_hours_end": "17:00",
        },
    )
    assert preferences.status_code == 200
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        created = evaluate_notifications(
            db,
            user,
            date(2026, 9, 1),
            date(2026, 9, 30),
            "VND",
            now=datetime(2026, 9, 3, 12, tzinfo=timezone.utc),
        )
        assert created == []
        created = evaluate_notifications(
            db,
            user,
            date(2026, 9, 1),
            date(2026, 9, 30),
            "VND",
            now=datetime(2026, 9, 3, 12, tzinfo=timezone.utc),
        )
        assert created == []
    disabled = test_client.patch(
        "/api/v1/preferences/notifications",
        headers=headers(auth),
        json={"smart_notifications_enabled": False},
    )
    assert disabled.status_code == 200


def test_notification_api_read_events_and_cross_user_denial(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    account_data, _ = _setup_budget(test_client, auth)
    _expense(test_client, auth, account_data["id"], 10_000, "notification-api")
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        created = evaluate_notifications(
            db,
            user,
            date(2026, 9, 1),
            date(2026, 9, 30),
            "VND",
            now=datetime.now(timezone.utc),
        )
        db.commit()
        notification_id = created[0].id
    listing = test_client.get("/api/v1/notifications", headers=headers(auth))
    assert listing.status_code == 200
    assert listing.json()["unread"] == 3
    other = register(test_client)
    assert (
        test_client.post(
            f"/api/v1/notifications/{notification_id}/read", headers=headers(other)
        ).status_code
        == 404
    )
    read = test_client.post(f"/api/v1/notifications/{notification_id}/read", headers=headers(auth))
    assert read.status_code == 200
    assert read.json()["read_at"] is not None
    event = test_client.post(
        f"/api/v1/notifications/{notification_id}/events",
        headers=headers(auth),
        json={"event_type": "OPEN", "result": "shown"},
    )
    assert event.status_code == 201
    with factory() as db:
        assert db.query(Notification).filter_by(id=notification_id).one().read_at is not None
        assert db.query(Notification).filter_by(id=notification_id).one().events


def test_recurring_payment_is_fail_closed(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        assert all(
            item["type"] != "RECURRING_PAYMENT_DUE"
            for item in notification_candidates(
                db, user, date(2026, 9, 1), date(2026, 9, 30), "VND"
            )
        )


def test_canonical_insights_feed_notifications(canonical_analytics_fixture):  # noqa: F811
    test_client, auth, _ = canonical_analytics_fixture
    with test_client as active_client:
        response = active_client.get("/api/v1/notifications", headers=headers(auth))
    assert response.status_code == 200


def test_quiet_hours_midnight_crossing_and_critical_bypass(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    account_data, _ = _setup_budget(test_client, auth)
    _expense(test_client, auth, account_data["id"], 10_000, "notification-critical")
    test_client.patch(
        "/api/v1/preferences/notifications",
        headers=headers(auth),
        json={
            "quiet_hours_start": "23:00",
            "quiet_hours_end": "07:00",
            "max_notifications_per_day": 1,
        },
    )
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        preference = user.user_preferences
        assert _in_quiet_hours(user, preference, datetime(2026, 9, 3, 23, 30, tzinfo=timezone.utc))
        assert _in_quiet_hours(user, preference, datetime(2026, 9, 4, 6, 30, tzinfo=timezone.utc))
        assert not _in_quiet_hours(user, preference, datetime(2026, 9, 4, 12, tzinfo=timezone.utc))
        created = evaluate_notifications(
            db,
            user,
            date(2026, 9, 1),
            date(2026, 9, 30),
            "VND",
            now=datetime(2026, 9, 3, 23, 30, tzinfo=timezone.utc),
        )
        assert {item.rule_id for item in created} == {"budget_100"}


def test_scheduler_lock_prevents_duplicate_cycle():
    path = Path(__file__).parents[3] / "apps" / "worker" / "app" / "scheduler.py"
    spec = importlib.util.spec_from_file_location("phase11_scheduler", path)
    scheduler = importlib.util.module_from_spec(spec)
    sys.modules["phase11_scheduler"] = scheduler
    spec.loader.exec_module(scheduler)

    held = FakeLock(False)
    assert scheduler.run_once(FakeRedis(held), lambda: 1) == 0
    available = FakeLock(True)
    assert scheduler.run_once(FakeRedis(available), lambda: 3) == 3
    assert available.released
