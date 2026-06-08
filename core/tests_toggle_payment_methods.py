"""
Testes para feature 024-toggle-metodos-pagamento:
- checkout() rejeita payment_method desabilitado
- checkout() bloqueado quando todos os métodos estão desabilitados
- context processor expõe os 3 novos flags
"""
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from core.models import Store, Category, Product, Order
from core.context_processors import cart as cart_processor


SUBDOMAIN = "testloja024"
HEADERS = {"HTTP_X_TENANT_SUBDOMAIN": SUBDOMAIN}


def _make_store(**kwargs):
    defaults = {
        "name": "Loja 024",
        "mercadopago_access_token": "TEST-0000",
        "delivery_enabled": True,
        "payment_online_enabled": True,
        "payment_cash_enabled": True,
        "payment_card_enabled": True,
    }
    defaults.update(kwargs)
    store, _ = Store.objects.get_or_create(subdomain=SUBDOMAIN, defaults=defaults)
    for field, value in defaults.items():
        setattr(store, field, value)
    store.save()
    return store


def _make_user_and_product(store):
    user = User.objects.create_user(
        username="customer024", password="pass", email="c024@test.com"
    )
    cat = Category.objects.create(name="Cat024", store=store)
    product = Product.objects.create(
        name="Produto024", price="10.00", category=cat, store=store, is_available=True
    )
    return user, product


CHECKOUT_URL = "/checkout/"
CHECKOUT_POST_BASE = {
    "customer_name": "Cliente Teste",
    "customer_phone": "11999998888",
    "delivery_address": "Rua Teste, 1",
}


# ---------------------------------------------------------------------------
# Testes do guard no checkout
# ---------------------------------------------------------------------------

class CheckoutPaymentMethodGuardTests(TestCase):
    def setUp(self):
        self.store = _make_store()
        self.user, self.product = _make_user_and_product(self.store)
        self.client.login(username="customer024", password="pass")
        self.client.post(f"/cart/add/{self.product.id}/", {"quantity": 1}, **HEADERS)

    def _post_checkout(self, payment_method):
        data = dict(CHECKOUT_POST_BASE)
        data["payment_method"] = payment_method
        return self.client.post(CHECKOUT_URL, data, **HEADERS)

    def test_cash_disabled_returns_error_no_order_created(self):
        self.store.payment_cash_enabled = False
        self.store.save()
        resp = self._post_checkout("cash")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "não disponível")
        self.assertEqual(Order.objects.filter(store=self.store).count(), 0)

    def test_card_disabled_returns_error_no_order_created(self):
        self.store.payment_card_enabled = False
        self.store.save()
        resp = self._post_checkout("card")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "não disponível")
        self.assertEqual(Order.objects.filter(store=self.store).count(), 0)

    def test_online_disabled_returns_error_no_order_created(self):
        self.store.payment_online_enabled = False
        self.store.save()
        resp = self._post_checkout("online")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "não disponível")
        self.assertEqual(Order.objects.filter(store=self.store).count(), 0)

    def test_all_methods_disabled_blocks_checkout(self):
        self.store.payment_online_enabled = False
        self.store.payment_cash_enabled = False
        self.store.payment_card_enabled = False
        self.store.save()
        resp = self._post_checkout("online")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Nenhum método de pagamento")
        self.assertEqual(Order.objects.filter(store=self.store).count(), 0)

    @patch('core.tasks.process_new_order.delay')
    def test_enabled_method_proceeds_normally(self, mock_task):
        # cash habilitado deve seguir o fluxo normal (não rejeitar no guard)
        resp = self._post_checkout("cash")
        # Não deve conter mensagem de método indisponível
        self.assertNotContains(resp, "Método de pagamento não disponível")
        self.assertNotContains(resp, "Nenhum método de pagamento")


# ---------------------------------------------------------------------------
# Testes do context processor
# ---------------------------------------------------------------------------

class CartContextProcessorPaymentFlagsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.store = _make_store()

    def _get_context(self, store=None):
        request = self.factory.get("/")
        request.tenant = store or self.store
        request.session = self.client.session
        return cart_processor(request)

    def test_all_flags_true_by_default(self):
        ctx = self._get_context()
        self.assertTrue(ctx["payment_online_enabled"])
        self.assertTrue(ctx["payment_cash_enabled"])
        self.assertTrue(ctx["payment_card_enabled"])

    def test_cash_disabled_reflected_in_context(self):
        self.store.payment_cash_enabled = False
        self.store.save()
        ctx = self._get_context()
        self.assertFalse(ctx["payment_cash_enabled"])
        self.assertTrue(ctx["payment_online_enabled"])
        self.assertTrue(ctx["payment_card_enabled"])

    def test_all_flags_false_in_context(self):
        self.store.payment_online_enabled = False
        self.store.payment_cash_enabled = False
        self.store.payment_card_enabled = False
        self.store.save()
        ctx = self._get_context()
        self.assertFalse(ctx["payment_online_enabled"])
        self.assertFalse(ctx["payment_cash_enabled"])
        self.assertFalse(ctx["payment_card_enabled"])

    def test_no_tenant_returns_true_defaults(self):
        request = self.factory.get("/")
        request.tenant = None
        request.session = self.client.session
        ctx = cart_processor(request)
        self.assertTrue(ctx["payment_online_enabled"])
        self.assertTrue(ctx["payment_cash_enabled"])
        self.assertTrue(ctx["payment_card_enabled"])
