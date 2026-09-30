from __future__ import annotations

from datetime import date, timedelta

from test_financial_core import client, headers, register  # noqa: F401


def test_financial_contacts_crud(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)

    # 1. Create contact
    res = test_client.post(
        "/api/v1/financial-contacts",
        headers=headers(auth),
        json={
            "name": "Mẹ",
            "relationship_type": "Gia đình",
            "phone": "0987654321",
            "notes": "Có thể hỗ trợ khi cần kíp",
            "is_support_contact": True,
        },
    )
    assert res.status_code == 201, res.text
    contact = res.json()
    assert contact["name"] == "Mẹ"
    assert contact["is_support_contact"] is True
    contact_id = contact["id"]

    # 2. List contacts
    res = test_client.get("/api/v1/financial-contacts", headers=headers(auth))
    assert res.status_code == 200
    contacts = res.json()
    assert len(contacts) == 1
    assert contacts[0]["id"] == contact_id

    # 3. Update contact
    res = test_client.patch(
        f"/api/v1/financial-contacts/{contact_id}",
        headers=headers(auth),
        json={"notes": "Cập nhật ghi chú"},
    )
    assert res.status_code == 200
    assert res.json()["notes"] == "Cập nhật ghi chú"

    # 4. Delete contact
    res = test_client.delete(f"/api/v1/financial-contacts/{contact_id}", headers=headers(auth))
    assert res.status_code == 204


def test_debts_crud_payments_and_summary(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)

    # Create a contact first
    contact_res = test_client.post(
        "/api/v1/financial-contacts",
        headers=headers(auth),
        json={"name": "Anh Nam", "relationship_type": "Bạn bè"},
    ).json()

    today = date.today()
    in_3_days = today + timedelta(days=3)

    # 1. Create a BORROW debt (I borrowed money)
    borrow_res = test_client.post(
        "/api/v1/debts",
        headers=headers(auth),
        json={
            "type": "BORROW",
            "counterparty_name": "Anh Nam",
            "contact_id": contact_res["id"],
            "total_amount": 5000000,
            "currency": "VND",
            "due_date": in_3_days.isoformat(),
            "notes": "Vay tiền mua laptop",
        },
    )
    assert borrow_res.status_code == 201, borrow_res.text
    debt = borrow_res.json()
    assert debt["remaining_amount"] == 5000000
    assert debt["status"] == "ACTIVE"
    debt_id = debt["id"]

    # 2. Create a LEND debt (I lent money)
    lend_res = test_client.post(
        "/api/v1/debts",
        headers=headers(auth),
        json={
            "type": "LEND",
            "counterparty_name": "Bạn Hùng",
            "total_amount": 2000000,
            "currency": "VND",
        },
    )
    assert lend_res.status_code == 201

    # 3. Check summary
    sum_res = test_client.get("/api/v1/debts/summary", headers=headers(auth))
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["total_borrow_remaining"] == 5000000
    assert summary["total_lend_remaining"] == 2000000
    assert summary["upcoming_debts_count"] == 1
    assert summary["overdue_debts_count"] == 0

    # 4. Partial payment: Pay 2,000,000 VND
    pay_res = test_client.post(
        f"/api/v1/debts/{debt_id}/payments",
        headers=headers(auth),
        json={"amount": 2000000, "notes": "Trả đợt 1"},
    )
    assert pay_res.status_code == 201
    updated_debt = test_client.get(f"/api/v1/debts/{debt_id}", headers=headers(auth)).json()
    assert updated_debt["remaining_amount"] == 3000000
    assert updated_debt["status"] == "ACTIVE"
    assert len(updated_debt["payments"]) == 1

    # 5. Final payment: Pay remaining 3,000,000 VND
    pay_res2 = test_client.post(
        f"/api/v1/debts/{debt_id}/payments",
        headers=headers(auth),
        json={"amount": 3000000, "notes": "Tất toán hết nợ"},
    )
    assert pay_res2.status_code == 201
    settled_debt = test_client.get(f"/api/v1/debts/{debt_id}", headers=headers(auth)).json()
    assert settled_debt["remaining_amount"] == 0
    assert settled_debt["status"] == "PAID"

    # 6. Verify cross-user isolation
    auth2 = register(test_client)
    res_forbidden = test_client.get(f"/api/v1/debts/{debt_id}", headers=headers(auth2))
    assert res_forbidden.status_code == 404
