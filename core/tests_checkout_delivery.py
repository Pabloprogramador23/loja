"""
Testes para a feature 014-pagamento-entrega.
Cobre checkout com pagamento na entrega (cash/card) e regressão online.
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase

from core.models import Category, Order, OrderItem, Product, Store
from core.utils import set_current_tenant, reset_current_tenant


class CheckoutDeliveryBaseTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(
            name='Delivery Store', subdomain='delivery-store', is_active=True,
        )
        self.user = User.objects.create_user(
            username='deliveryuser', email='d@test.com', password='pass123'
        )
        self.category = Category.objects.create(name='Cat', store=self.store)
        self.product = Product.objects.create(
            name='Item', category=self.category, price=Decimal('20.00'),
            store=self.store, is_available=True,
        )
        self.client = Client()
        self.client.login(username='deliveryuser', password='pass123')

    def _add_to_cart(self):
        from django.urls import reverse
        self.client.post(
            reverse('add_to_cart', args=[self.product.id]),
            HTTP_X_TENANT_SUBDOMAIN='delivery-store',
        )

    def _checkout_post(self, extra_data=None):
        from django.urls import reverse
        data = {
            'customer_name': 'Fulano',
            'customer_phone': '85999990000',
            'delivery_address': 'Rua A, 1',
        }
        if extra_data:
            data.update(extra_data)
        return self.client.post(
            reverse('checkout'),
            data,
            HTTP_X_TENANT_SUBDOMAIN='delivery-store',
        )


class CheckoutCashTest(CheckoutDeliveryBaseTest):
    def test_cash_creates_confirmed_order_with_change(self):
        self._add_to_cart()
        with patch('core.tasks.process_new_order.delay') as mock_delay:
            self._checkout_post({'payment_method': 'cash', 'change_amount': '50'})
        order = Order.objects.filter(store=self.store).last()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CASH)
        self.assertEqual(order.change_amount, Decimal('50.00'))
        mock_delay.assert_called_once_with(order.id)

    def test_cash_without_change_creates_confirmed_order(self):
        self._add_to_cart()
        with patch('core.tasks.process_new_order.delay'):
            self._checkout_post({'payment_method': 'cash', 'change_amount': ''})
        order = Order.objects.filter(store=self.store).last()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertIsNone(order.change_amount)

    def test_cash_negative_change_is_rejected(self):
        self._add_to_cart()
        count_before = Order.objects.count()
        self._checkout_post({'payment_method': 'cash', 'change_amount': '-10'})
        self.assertEqual(Order.objects.count(), count_before)

    def test_cash_non_numeric_change_is_rejected(self):
        self._add_to_cart()
        count_before = Order.objects.count()
        self._checkout_post({'payment_method': 'cash', 'change_amount': 'abc'})
        self.assertEqual(Order.objects.count(), count_before)

    def test_cash_does_not_call_mercadopago(self):
        self._add_to_cart()
        with patch('core.payment.create_checkout_pro_preference') as mock_mp, \
             patch('core.tasks.process_new_order.delay'):
            self._checkout_post({'payment_method': 'cash', 'change_amount': ''})
        mock_mp.assert_not_called()

    def test_cash_redirects_to_success_without_mp(self):
        self._add_to_cart()
        with patch('core.tasks.process_new_order.delay'):
            response = self._checkout_post({'payment_method': 'cash', 'change_amount': ''})
        self.assertNotIn(b'mercadopago', response.content.lower())
        self.assertNotIn(b'init_point', response.content.lower())


class CheckoutCardTest(CheckoutDeliveryBaseTest):
    def test_card_credit_creates_confirmed_order(self):
        self._add_to_cart()
        with patch('core.tasks.process_new_order.delay') as mock_delay:
            self._checkout_post({'payment_method': 'card', 'card_type': 'credit'})
        order = Order.objects.filter(store=self.store).last()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CARD)
        self.assertEqual(order.card_type, Order.CardType.CREDIT)
        self.assertIsNone(order.change_amount)
        mock_delay.assert_called_once_with(order.id)

    def test_card_debit_creates_confirmed_order(self):
        self._add_to_cart()
        with patch('core.tasks.process_new_order.delay'):
            self._checkout_post({'payment_method': 'card', 'card_type': 'debit'})
        order = Order.objects.filter(store=self.store).last()
        self.assertEqual(order.card_type, Order.CardType.DEBIT)

    def test_card_does_not_call_mercadopago(self):
        self._add_to_cart()
        with patch('core.payment.create_checkout_pro_preference') as mock_mp, \
             patch('core.tasks.process_new_order.delay'):
            self._checkout_post({'payment_method': 'card', 'card_type': 'credit'})
        mock_mp.assert_not_called()


class CheckoutOnlineRegressionTest(CheckoutDeliveryBaseTest):
    def test_online_creates_pending_order(self):
        self._add_to_cart()
        with patch('core.payment.create_checkout_pro_preference') as mock_mp:
            mock_mp.return_value = {'init_point': 'https://mp.example.com/pay'}
            self._checkout_post({'payment_method': 'online'})
        order = Order.objects.filter(store=self.store).last()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_method, Order.PaymentMethod.ONLINE)
        mock_mp.assert_called_once()

    def test_missing_payment_method_defaults_to_online(self):
        self._add_to_cart()
        with patch('core.payment.create_checkout_pro_preference') as mock_mp:
            mock_mp.return_value = {'init_point': 'https://mp.example.com/pay'}
            self._checkout_post()
        order = Order.objects.filter(store=self.store).last()
        self.assertEqual(order.payment_method, Order.PaymentMethod.ONLINE)

    def test_online_does_not_call_process_new_order(self):
        self._add_to_cart()
        with patch('core.payment.create_checkout_pro_preference') as mock_mp, \
             patch('core.tasks.process_new_order.delay') as mock_delay:
            mock_mp.return_value = {'init_point': 'https://mp.example.com/pay'}
            self._checkout_post({'payment_method': 'online'})
        mock_delay.assert_not_called()
