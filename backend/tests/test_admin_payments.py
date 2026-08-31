from app.db.enums import UserRole
from tests.conftest import auth_headers, register_user, unique_email
from tests.test_admin_permissions import promote


async def _paid_subscription(client, admin_tokens, user_tokens) -> str:
    """Create a plan, buy it for the user via a mock webhook, return the payment id."""
    plans = await client.get("/api/v1/subscription/plans")
    if not plans.json()["data"]:
        resp = await client.post(
            "/api/v1/admin/subscription-plans",
            headers=auth_headers(admin_tokens),
            json={"name": "Test Plan", "price": 100, "currency": "INR", "duration_days": 30},
        )
        assert resp.status_code == 200, resp.text
    plans = await client.get("/api/v1/subscription/plans")
    plan_id = plans.json()["data"][0]["id"]
    checkout = await client.post(
        "/api/v1/subscription/checkout", headers=auth_headers(user_tokens), json={"plan_id": plan_id}
    )
    assert checkout.status_code == 200, checkout.text
    payment_id = checkout.json()["data"]["payment_id"]
    await client.post(
        "/api/v1/payments/webhook/mock",
        json={"event": {"provider_payment_id": f"mock_{payment_id}", "status": "SUCCESS"}},
    )
    return payment_id


class TestPaymentsAdmin:
    async def test_list_payments(self, client, session_factory):
        user = await register_user(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        await _paid_subscription(client, admin, user)
        finance = await promote(client, session_factory, unique_email("fin"), UserRole.FINANCE)
        resp = await client.get("/api/v1/admin/payments", headers=auth_headers(finance))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["status"] == "SUCCESS"

    async def test_filter_by_status(self, client, session_factory):
        finance = await promote(client, session_factory, unique_email("fin"), UserRole.FINANCE)
        resp = await client.get("/api/v1/admin/payments?status=FAILED", headers=auth_headers(finance))
        assert resp.status_code == 200

    async def test_payment_detail(self, client, session_factory):
        user = await register_user(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        payment_id = await _paid_subscription(client, admin, user)
        finance = await promote(client, session_factory, unique_email("fin"), UserRole.FINANCE)
        resp = await client.get(f"/api/v1/admin/payments/{payment_id}", headers=auth_headers(finance))
        assert resp.status_code == 200
        assert resp.json()["data"]["payment_type"] == "SUBSCRIPTION"

    async def test_refund_flow(self, client, session_factory):
        user = await register_user(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        payment_id = await _paid_subscription(client, admin, user)
        finance = await promote(client, session_factory, unique_email("fin"), UserRole.FINANCE)
        resp = await client.post(
            f"/api/v1/admin/payments/{payment_id}/refund",
            headers=auth_headers(finance),
            json={"reason": "customer request"},
        )
        assert resp.status_code == 200
        detail = await client.get(f"/api/v1/admin/payments/{payment_id}", headers=auth_headers(finance))
        assert detail.json()["data"]["status"] == "REFUNDED"

    async def test_duplicate_refund_rejected(self, client, session_factory):
        user = await register_user(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        payment_id = await _paid_subscription(client, admin, user)
        finance = await promote(client, session_factory, unique_email("fin"), UserRole.FINANCE)
        resp = await client.post(
            f"/api/v1/admin/payments/{payment_id}/refund", headers=auth_headers(finance), json={"reason": "first"}
        )
        assert resp.status_code == 200
        resp = await client.post(
            f"/api/v1/admin/payments/{payment_id}/refund", headers=auth_headers(finance), json={"reason": "again"}
        )
        assert resp.status_code == 422

    async def test_refund_requires_finance_permission(self, client, session_factory):
        user = await register_user(client)
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        payment_id = await _paid_subscription(client, admin, user)
        analyst = await promote(client, session_factory, unique_email("an"), UserRole.ANALYST)
        resp = await client.post(
            f"/api/v1/admin/payments/{payment_id}/refund", headers=auth_headers(analyst), json={"reason": "x"}
        )
        assert resp.status_code == 403


class TestSubscriptionPlansAdmin:
    async def test_crud_plans(self, client, session_factory):
        admin = await promote(client, session_factory, unique_email("adm"), UserRole.ADMIN)
        resp = await client.post(
            "/api/v1/admin/subscription-plans",
            headers=auth_headers(admin),
            json={
                "name": "Test Plan",
                "description": "trial",
                "price": 100,
                "currency": "INR",
                "duration_days": 30,
                "features": {"test": True},
            },
        )
        assert resp.status_code == 200, resp.text
        plan_id = resp.json()["data"]["id"]

        resp = await client.patch(
            f"/api/v1/admin/subscription-plans/{plan_id}",
            headers=auth_headers(admin),
            json={"price": 150},
        )
        assert resp.status_code == 200
        assert float(resp.json()["data"]["price"]) == 150

        resp = await client.post(f"/api/v1/admin/subscription-plans/{plan_id}/deactivate", headers=auth_headers(admin))
        assert resp.status_code == 200

    async def test_plan_requires_manage_permission(self, client, session_factory):
        mod = await promote(client, session_factory, unique_email("mod"), UserRole.MODERATOR)
        resp = await client.post(
            "/api/v1/admin/subscription-plans",
            headers=auth_headers(mod),
            json={"name": "X", "price": 1, "currency": "INR", "duration_days": 1},
        )
        assert resp.status_code == 403
