from datetime import date

from test_analytics import canonical_analytics_fixture  # noqa: F401
from test_financial_core import headers, register
from test_phase07 import client  # noqa: F401

from app.db.models import User
from app.recommendations.service import (
    ACCEPTED,
    DISMISSED,
    generate_candidates,
)


def test_recommendations_are_traceable_deterministic_and_estimates(canonical_analytics_fixture):  # noqa: F811
    test_client, auth, _ = canonical_analytics_fixture
    first = test_client.get(
        "/api/v1/recommendations",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    )
    assert first.status_code == 200, first.text
    items = first.json()["items"]
    assert items
    assert {item["type"] for item in items} <= {
        "REDUCE_CATEGORY",
        "ADJUST_BUDGET",
        "INCREASE_SAVING",
        "GOAL_PACING",
        "CASHFLOW_PREPARATION",
    }
    assert all(item["expected_impact"].startswith("ESTIMATE:") for item in items)
    assert all(item["source_insight_id"] and item["source_metric"] for item in items)
    repeated = test_client.get(
        "/api/v1/recommendations",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    )
    assert [item["deterministic_id"] for item in repeated.json()["items"]] == [
        item["deterministic_id"] for item in items
    ]


def test_empty_evidence_and_recurring_recommendation_fail_closed(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        candidates = generate_candidates(db, user, date(2026, 8, 1), date(2026, 8, 31), "VND")
        assert candidates == []
        assert all(item.type != "REVIEW_RECURRING_EXPENSE" for item in candidates)


def test_accept_dismiss_feedback_and_cross_user_isolation(canonical_analytics_fixture):  # noqa: F811
    test_client, auth, account_data = canonical_analytics_fixture
    listing = test_client.get(
        "/api/v1/recommendations",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    ).json()
    recommendation_id = listing["items"][0]["id"]
    balance_before = test_client.get("/api/v1/accounts", headers=headers(auth)).json()["items"][0][
        "current_balance"
    ]
    other = register(test_client)
    assert (
        test_client.post(
            f"/api/v1/recommendations/{recommendation_id}/accept", headers=headers(other)
        ).status_code
        == 404
    )
    accepted = test_client.post(
        f"/api/v1/recommendations/{recommendation_id}/accept", headers=headers(auth)
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == ACCEPTED
    assert (
        test_client.get("/api/v1/accounts", headers=headers(auth)).json()["items"][0][
            "current_balance"
        ]
        == balance_before
    )

    remaining = test_client.get(
        "/api/v1/recommendations",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    ).json()["items"]
    dismiss_id = next(item["id"] for item in remaining if item["id"] != recommendation_id)
    dismissed = test_client.post(
        f"/api/v1/recommendations/{dismiss_id}/dismiss", headers=headers(auth)
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == DISMISSED
    assert all(
        item["id"] != dismiss_id
        for item in test_client.get(
            "/api/v1/recommendations",
            headers=headers(auth),
            params={"start": "2026-08-01", "end": "2026-08-31"},
        ).json()["items"]
    )
    feedback = test_client.post(
        f"/api/v1/recommendations/{recommendation_id}/feedback",
        headers=headers(auth),
        json={"feedback": "HELPFUL"},
    )
    assert feedback.status_code == 200
    assert feedback.json()["feedback_score"] == 1


def test_recommendation_events_and_source_database_row(canonical_analytics_fixture):  # noqa: F811
    test_client, auth, _ = canonical_analytics_fixture
    item = test_client.get(
        "/api/v1/recommendations",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    ).json()["items"][0]
    event = test_client.post(
        f"/api/v1/recommendations/{item['id']}/events",
        headers=headers(auth),
        params={"event_type": "SHOWN"},
    )
    assert event.status_code == 201
    with test_client as active_client:
        assert (
            active_client.get(
                f"/api/v1/recommendations/{item['id']}",
                headers=headers(auth),
                params={"start": "2026-08-01", "end": "2026-08-31"},
            ).status_code
            == 200
        )
