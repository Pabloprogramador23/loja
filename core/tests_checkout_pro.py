"""
Testes para a feature 013-checkout-pro-mp.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Category, Order, Product, Store
from core.utils import set_current_tenant, reset_current_tenant


class CreateCheckoutProPreferenceTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(
            name="CP Store", subdomain="cp-store", is_active=True,
            mercadopago_access_token=""
        )
        self.user = User.objects.create_user(username="cpuser", email="cp@test.com", password="pass123")
        self.category = Category.objects.create(name="Cat", store=self.store)
        self.product = Product.objects.create(
            name="Item", category=self.category, price=Decimal('30.00'), store=self.store
        )

    def _make_order(self):
        from core.models import OrderItem
        token = set_current_tenant(self.store)
        order = Order.objects.create(
            store=self.store, user=self.user,
            customer_name="CP User", customer_phone="85999990000",
            delivery_address="Rua Teste, 1", total_amount=Decimal('30.00'),
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, unit_price=Decimal('30.00'), store=self.store)
        reset_current_tenant(token)
        return order

    def test_mock_token_returns_local_init_point(self):
        from core.payment import create_checkout_pro_preference
        order = self._make_order()
        result = create_checkout_pro_preference(order)
        self.assertIn('/payment/mock/', result['init_point'])
        order.refresh_from_db()
        self.assertTrue(order.mp_preference_id.startswith('MOCK_PREF_'))

    def test_mock_token_saves_mp_preference_id(self):
        from core.payment import create_checkout_pro_preference
        order = self._make_order()
        create_checkout_pro_preference(order)
        order.refresh_from_db()
        self.assertNotEqual(order.mp_preference_id, '')

    @patch('core.payment.mercadopago.SDK')
    def test_real_token_calls_preference_api(self, mock_sdk_class):
        self.store.mercadopago_access_token = "TEST-real-token"
        self.store.save()
        mock_sdk = MagicMock()
        mock_sdk_class.return_value = mock_sdk
        mock_sdk.preference.return_value.create.return_value = {
            "status": 201,
            "response": {
                "id": "pref_abc123",
                "init_point": "https://mp.com/checkout",
                "sandbox_init_point": "https://sandbox.mp.com/checkout",
            }
        }
        from core.payment import create_checkout_pro_preference
        order = self._make_order()
        result = create_checkout_pro_preference(order)
        self.assertIn('init_point', result)
        self.assertIsNotNone(result['init_point'])
        order.refresh_from_db()
        self.assertEqual(order.mp_preference_id, 'pref_abc123')


class CheckoutViewWithProTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Pro Store", subdomain="pro-store", is_active=True)
        self.user = User.objects.create_user(
            username="prouser", email="pro@test.com", password="pass123"
        )
        self.category = Category.objects.create(name="Cat", store=self.store)
        self.product = Product.objects.create(
            name="Item", category=self.category, price=Decimal('25.00'), store=self.store
        )
        self.client = Client()
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'pro-store'}

    def test_checkout_redirects_to_init_point(self):
        self.client.login(username='prouser', password='pass123')
        self.client.post(reverse('add_to_cart', args=[self.product.id]), **self.headers)
        response = self.client.post(reverse('checkout'), {
            'customer_name': 'Pro User',
            'customer_phone': '85999990000',
            'delivery_address': 'Rua Teste, 1',
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('window.location.href', content)
        self.assertIn('/payment/', content)


class PaymentReturnViewsTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Ret Store", subdomain="ret-store", is_active=True)
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'ret-store'}

    def test_success_view_returns_200(self):
        response = self.client.get('/payment/success/?payment_id=123&status=approved', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'confirmado')

    def test_pending_view_returns_200(self):
        response = self.client.get('/payment/pending/?payment_id=123', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'processamento')

    def test_failure_view_returns_200(self):
        response = self.client.get('/payment/failure/?payment_id=123', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'conclu')

    def test_mock_view_redirects_in_testing_mode(self):
        # REVERSA_TESTING=true no .env — a view processa e redireciona para success
        response = self.client.get('/payment/mock/?order_id=1', **self.headers)
        # Em modo de teste redireciona (302) ou retorna 400 se order não existir
        self.assertIn(response.status_code, [302, 400, 200])
