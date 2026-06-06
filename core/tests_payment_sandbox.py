"""
Testes para a feature 017-mercadopago-sandbox.
Cobre: customer_email em Order, guest checkout Pro, mock guard com token real.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Category, Order, OrderItem, Product, Store
from core.utils import set_current_tenant, reset_current_tenant


class CustomerEmailSavedOnOrderTest(TestCase):
    """T003 — checkout de guest salva customer_email no Order."""

    def setUp(self):
        self.store = Store.objects.create(
            name="Email Store", subdomain="email-store", is_active=True
        )
        self.category = Category.objects.create(name="Cat", store=self.store)
        self.product = Product.objects.create(
            name="Pizza", category=self.category, price=Decimal('20.00'), store=self.store
        )
        self.client = Client()
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'email-store'}

    def test_guest_checkout_saves_customer_email(self):
        self.client.post(reverse('add_to_cart', args=[self.product.id]), **self.headers)
        self.client.post(reverse('checkout'), {
            'customer_name': 'Maria Guest',
            'customer_phone': '85999990001',
            'delivery_address': 'Rua A, 10',
            'customer_email': 'maria.guest@test.com',
        }, **self.headers)
        order = Order.objects.last()
        self.assertIsNotNone(order)
        self.assertEqual(order.customer_email, 'maria.guest@test.com')

    def test_authenticated_user_checkout_saves_customer_email(self):
        user = User.objects.create_user(username='auth_user', email='auth@test.com', password='pass')
        self.client.login(username='auth_user', password='pass')
        self.client.post(reverse('add_to_cart', args=[self.product.id]), **self.headers)
        self.client.post(reverse('checkout'), {
            'customer_name': 'Auth User',
            'customer_phone': '85999990002',
            'delivery_address': 'Rua B, 20',
        }, **self.headers)
        order = Order.objects.last()
        self.assertIsNotNone(order)
        self.assertEqual(order.customer_email, '')

    def test_guest_checkout_without_email_fails(self):
        self.client.post(reverse('add_to_cart', args=[self.product.id]), **self.headers)
        response = self.client.post(reverse('checkout'), {
            'customer_name': 'No Email Guest',
            'customer_phone': '85999990003',
            'delivery_address': 'Rua C, 30',
            'customer_email': '',
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)


class CheckoutProGuestEmailTest(TestCase):
    """T004 — create_checkout_pro_preference usa customer_email quando order.user é None."""

    def setUp(self):
        self.store = Store.objects.create(
            name="Pro Guest Store", subdomain="pro-guest-store", is_active=True,
            mercadopago_access_token="TEST-real-token-uuid"
        )
        self.category = Category.objects.create(name="Cat", store=self.store)
        self.product = Product.objects.create(
            name="Item", category=self.category, price=Decimal('15.00'), store=self.store
        )

    def _make_guest_order(self, email='guest@test.com'):
        token = set_current_tenant(self.store)
        order = Order.objects.create(
            store=self.store,
            user=None,
            customer_name="Guest User",
            customer_phone="85999990004",
            customer_email=email,
            delivery_address="Rua Guest, 1",
            total_amount=Decimal('15.00'),
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            order=order, product=self.product,
            quantity=1, unit_price=Decimal('15.00'), store=self.store
        )
        reset_current_tenant(token)
        return order

    @patch('core.payment.mercadopago.SDK')
    def test_guest_order_does_not_raise_attribute_error(self, mock_sdk_class):
        mock_sdk = MagicMock()
        mock_sdk_class.return_value = mock_sdk
        mock_sdk.preference.return_value.create.return_value = {
            "status": 201,
            "response": {
                "id": "pref_guest_123",
                "init_point": "https://mp.com/checkout",
                "sandbox_init_point": "https://sandbox.mp.com/checkout",
            }
        }
        from core.payment import create_checkout_pro_preference
        order = self._make_guest_order(email='guest.buyer@test.com')
        result = create_checkout_pro_preference(order)
        self.assertIsNotNone(result)
        self.assertIn('init_point', result)

    @patch('core.payment.mercadopago.SDK')
    def test_guest_order_sends_customer_email_to_mp(self, mock_sdk_class):
        mock_sdk = MagicMock()
        mock_sdk_class.return_value = mock_sdk
        mock_sdk.preference.return_value.create.return_value = {
            "status": 201,
            "response": {
                "id": "pref_guest_456",
                "init_point": "https://mp.com/checkout",
                "sandbox_init_point": "https://sandbox.mp.com/checkout",
            }
        }
        from core.payment import create_checkout_pro_preference
        order = self._make_guest_order(email='verified.guest@test.com')
        create_checkout_pro_preference(order)
        call_args = mock_sdk.preference.return_value.create.call_args[0][0]
        self.assertEqual(call_args['payer']['email'], 'verified.guest@test.com')


class PixMockGuardTest(TestCase):
    """T005 — create_pix_payment com token real e API retornando 403 retorna None, não mock."""

    def setUp(self):
        self.store = Store.objects.create(
            name="PIX Store", subdomain="pix-store", is_active=True,
            mercadopago_access_token="TEST-real-token-for-pix"
        )
        self.category = Category.objects.create(name="Cat", store=self.store)
        self.product = Product.objects.create(
            name="Açaí", category=self.category, price=Decimal('12.00'), store=self.store
        )

    def _make_order(self, email='pix.user@test.com'):
        token = set_current_tenant(self.store)
        order = Order.objects.create(
            store=self.store,
            user=None,
            customer_name="PIX User",
            customer_phone="85999990005",
            customer_email=email,
            delivery_address="Rua PIX, 1",
            total_amount=Decimal('12.00'),
            status=Order.Status.PENDING,
        )
        reset_current_tenant(token)
        return order

    @patch('core.payment.mercadopago.SDK')
    def test_real_token_403_returns_none_not_mock(self, mock_sdk_class):
        mock_sdk = MagicMock()
        mock_sdk_class.return_value = mock_sdk
        mock_sdk.payment.return_value.create.return_value = {
            "status": 403,
            "response": {"message": "Forbidden"},
        }
        from core.payment import create_pix_payment
        order = self._make_order()
        result = create_pix_payment(order)
        self.assertIsNone(result)

    @patch('core.payment.mercadopago.SDK')
    def test_mock_token_test0000_still_returns_mock(self, mock_sdk_class):
        self.store.mercadopago_access_token = "TEST-0000-0000-fake"
        self.store.save()
        from core.payment import create_pix_payment
        order = self._make_order()
        result = create_pix_payment(order)
        self.assertIsNotNone(result)
        self.assertIn('qr_code', result)
        mock_sdk_class.assert_not_called()
