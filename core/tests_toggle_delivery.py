"""
Testes para feature 019-toggle-delivery:
- toggle_delivery_view
- checkout() bloqueado com delivery_enabled=False
- context processor expõe delivery_enabled
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from core.models import Store, Order
from core.context_processors import cart as cart_processor


def _make_store(delivery_enabled=True):
    return Store.objects.get_or_create(
        subdomain="testloja019",
        defaults={
            "name": "Loja 019",
            "mercadopago_access_token": "TEST-0000",
            "delivery_enabled": delivery_enabled,
        },
    )[0]


def _make_manager(store):
    user = User.objects.create_user(username="manager019", password="pass", is_staff=True)
    return user


# ---------------------------------------------------------------------------
# T004 — toggle_delivery_view
# ---------------------------------------------------------------------------

class ToggleDeliveryViewTests(TestCase):
    def setUp(self):
        self.store = _make_store(delivery_enabled=True)
        self.manager = _make_manager(self.store)

    def test_manager_can_toggle_off(self):
        self.client.login(username="manager019", password="pass")
        resp = self.client.post(
            "/dashboard/toggle-delivery/",
            HTTP_X_TENANT_SUBDOMAIN="testloja019",
        )
        self.assertEqual(resp.status_code, 200)
        self.store.refresh_from_db()
        self.assertFalse(self.store.delivery_enabled)

    def test_manager_can_toggle_back_on(self):
        self.store.delivery_enabled = False
        self.store.save()
        self.client.login(username="manager019", password="pass")
        resp = self.client.post(
            "/dashboard/toggle-delivery/",
            HTTP_X_TENANT_SUBDOMAIN="testloja019",
        )
        self.assertEqual(resp.status_code, 200)
        self.store.refresh_from_db()
        self.assertTrue(self.store.delivery_enabled)

    def test_non_manager_gets_403(self):
        regular = User.objects.create_user(username="regular019", password="pass", is_staff=False)
        self.client.login(username="regular019", password="pass")
        resp = self.client.post(
            "/dashboard/toggle-delivery/",
            HTTP_X_TENANT_SUBDOMAIN="testloja019",
        )
        self.assertEqual(resp.status_code, 403)
        self.store.refresh_from_db()
        self.assertTrue(self.store.delivery_enabled)  # estado não mudou

    def test_unauthenticated_redirects(self):
        resp = self.client.post(
            "/dashboard/toggle-delivery/",
            HTTP_X_TENANT_SUBDOMAIN="testloja019",
        )
        self.assertIn(resp.status_code, [302, 403])


# ---------------------------------------------------------------------------
# T005 — checkout() bloqueado quando delivery_enabled=False
# ---------------------------------------------------------------------------

class CheckoutBlockedWhenClosedTests(TestCase):
    def setUp(self):
        self.store = _make_store(delivery_enabled=False)

    def test_checkout_blocked_returns_error_no_order_created(self):
        count_before = Order.objects.count()
        resp = self.client.post(
            "/checkout/",
            {
                "customer_name": "Teste",
                "customer_phone": "11999999999",
                "delivery_address": "Rua Teste, 1",
                "customer_email": "guest@test.com",
                "payment_method": "online",
            },
            HTTP_X_TENANT_SUBDOMAIN="testloja019",
        )
        self.assertEqual(resp.status_code, 200)
        count_after = Order.objects.count()
        self.assertEqual(count_before, count_after)  # nenhum Order criado
        self.assertContains(resp, "não está aceitando pedidos")

    def test_checkout_allowed_when_open(self):
        self.store.delivery_enabled = True
        self.store.save()
        # Apenas verifica que NÃO retorna a mensagem de loja fechada
        resp = self.client.post(
            "/checkout/",
            {
                "customer_name": "Teste",
                "customer_phone": "11999999999",
                "delivery_address": "Rua Teste, 1",
                "customer_email": "guest@test.com",
                "payment_method": "online",
            },
            HTTP_X_TENANT_SUBDOMAIN="testloja019",
        )
        self.assertNotContains(resp, "não está aceitando pedidos")


# ---------------------------------------------------------------------------
# T006 — context processor expõe delivery_enabled
# ---------------------------------------------------------------------------

class ContextProcessorDeliveryEnabledTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _make_request(self, store):
        req = self.factory.get("/")
        req.tenant = store
        req.session = {}
        return req

    def test_delivery_enabled_true_in_context(self):
        store = _make_store(delivery_enabled=True)
        req = self._make_request(store)
        ctx = cart_processor(req)
        self.assertIn("delivery_enabled", ctx)
        self.assertTrue(ctx["delivery_enabled"])

    def test_delivery_enabled_false_in_context(self):
        store = _make_store(delivery_enabled=True)
        store.delivery_enabled = False
        store.save()
        req = self._make_request(store)
        ctx = cart_processor(req)
        self.assertFalse(ctx["delivery_enabled"])

    def test_delivery_enabled_true_when_no_tenant(self):
        req = self.factory.get("/")
        req.tenant = None
        req.session = {}
        ctx = cart_processor(req)
        self.assertTrue(ctx.get("delivery_enabled", True))
