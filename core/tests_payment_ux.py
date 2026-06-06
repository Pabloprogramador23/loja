"""
Testes de UX do checkout MP: tela de espera, status partial e views de retorno.
Feature 018-mp-ux-checkout
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import json

from core.models import Order, Store


def _make_store():
    return Store.objects.get_or_create(
        subdomain="testloja",
        defaults={"name": "Loja Teste", "mercadopago_access_token": "TEST-0000"},
    )[0]


def _make_order(store, status=Order.Status.PENDING):
    return Order.objects.create(
        store=store,
        customer_name="Guest Teste",
        customer_phone="11999999999",
        customer_email="guest@test.com",
        delivery_address="Rua Teste, 1",
        total_amount="50.00",
        delivery_fee="0.00",
        status=status,
        mp_preference_id="MOCK_PREF_1",
    )


# ---------------------------------------------------------------------------
# T002 — payment_waiting_view
# ---------------------------------------------------------------------------

class PaymentWaitingViewTests(TestCase):
    def setUp(self):
        self.store = _make_store()
        self.order = _make_order(self.store)

    def _get(self, params=""):
        with patch("core.middleware.get_current_tenant", return_value=self.store):
            resp = self.client.get(f"/payment/waiting/{params}", HTTP_X_TENANT_SUBDOMAIN="testloja")
        return resp

    def test_valid_order_id_returns_200(self):
        resp = self._get(f"?order_id={self.order.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("order", resp.context)
        self.assertEqual(resp.context["order"].id, self.order.id)

    def test_no_order_id_no_session_returns_200_with_none(self):
        resp = self._get()
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context.get("order"))

    def test_session_fallback(self):
        session = self.client.session
        session["guest_order_id"] = self.order.id
        session.save()
        resp = self._get()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["order"].id, self.order.id)

    def test_invalid_order_id_returns_200_with_none(self):
        resp = self._get("?order_id=999999")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context.get("order"))


# ---------------------------------------------------------------------------
# T003 — payment_waiting_status_view
# ---------------------------------------------------------------------------

class PaymentWaitingStatusViewTests(TestCase):
    def setUp(self):
        self.store = _make_store()

    def _get_status(self, order_id):
        with patch("core.middleware.get_current_tenant", return_value=self.store):
            resp = self.client.get(
                f"/payment/waiting/status/?order_id={order_id}",
                HTTP_X_TENANT_SUBDOMAIN="testloja",
            )
        return resp

    def test_pending_order_no_stop_polling(self):
        order = _make_order(self.store, Order.Status.PENDING)
        resp = self._get_status(order.id)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("stopPolling", resp.get("HX-Trigger", ""))

    def test_preparing_order_stops_polling(self):
        order = _make_order(self.store, Order.Status.PREPARING)
        resp = self._get_status(order.id)
        self.assertEqual(resp.status_code, 200)
        hx_trigger = resp.get("HX-Trigger", "")
        self.assertIn("stopPolling", hx_trigger)

    def test_canceled_order_stops_polling(self):
        order = _make_order(self.store, Order.Status.CANCELED)
        resp = self._get_status(order.id)
        self.assertEqual(resp.status_code, 200)
        hx_trigger = resp.get("HX-Trigger", "")
        self.assertIn("stopPolling", hx_trigger)

    def test_missing_order_returns_200(self):
        resp = self._get_status(999999)
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# T004 — payment_failure_view e payment_pending_view com order
# ---------------------------------------------------------------------------

class PaymentBackUrlsWithOrderTests(TestCase):
    def setUp(self):
        self.store = _make_store()
        self.order = _make_order(self.store)

    def _get(self, url, params=""):
        with patch("core.middleware.get_current_tenant", return_value=self.store):
            resp = self.client.get(f"{url}{params}", HTTP_X_TENANT_SUBDOMAIN="testloja")
        return resp

    def test_failure_with_preference_id_loads_order(self):
        resp = self._get("/payment/failure/", f"?preference_id={self.order.mp_preference_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context.get("order"))
        self.assertEqual(resp.context["order"].id, self.order.id)

    def test_pending_with_preference_id_loads_order(self):
        resp = self._get("/payment/pending/", f"?preference_id={self.order.mp_preference_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context.get("order"))
        self.assertEqual(resp.context["order"].id, self.order.id)

    def test_failure_without_order_still_200(self):
        resp = self._get("/payment/failure/", "?preference_id=NAO_EXISTE")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context.get("order"))

    def test_pending_without_order_still_200(self):
        resp = self._get("/payment/pending/", "?preference_id=NAO_EXISTE")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context.get("order"))
