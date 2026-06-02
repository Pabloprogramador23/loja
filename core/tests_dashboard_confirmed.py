"""
Testes para a feature 014: dashboard() deve contar pedidos CONFIRMED em total_orders_pending.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from core.models import Order, Store


class DashboardConfirmedCountTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(
            name='Dash Store', subdomain='dash-store', is_active=True,
        )
        self.manager = User.objects.create_user(
            username='manager', email='m@test.com', password='pass123', is_staff=True,
        )
        self.client = Client()
        self.client.login(username='manager', password='pass123')

    def _make_order(self, status):
        return Order.objects.create(
            store=self.store,
            customer_name='Test',
            customer_phone='11999990000',
            delivery_address='Rua X',
            total_amount=Decimal('30.00'),
            status=status,
        )

    def test_confirmed_order_counted_in_pending(self):
        self._make_order(Order.Status.CONFIRMED)
        response = self.client.get(
            '/dashboard/',
            HTTP_X_TENANT_SUBDOMAIN='dash-store',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_orders_pending'], 1)

    def test_pending_order_counted_in_pending(self):
        self._make_order(Order.Status.PENDING)
        response = self.client.get(
            '/dashboard/',
            HTTP_X_TENANT_SUBDOMAIN='dash-store',
        )
        self.assertEqual(response.context['total_orders_pending'], 1)

    def test_confirmed_and_pending_both_counted(self):
        self._make_order(Order.Status.CONFIRMED)
        self._make_order(Order.Status.PENDING)
        response = self.client.get(
            '/dashboard/',
            HTTP_X_TENANT_SUBDOMAIN='dash-store',
        )
        self.assertEqual(response.context['total_orders_pending'], 2)

    def test_completed_order_not_counted_in_pending(self):
        self._make_order(Order.Status.COMPLETED)
        response = self.client.get(
            '/dashboard/',
            HTTP_X_TENANT_SUBDOMAIN='dash-store',
        )
        self.assertEqual(response.context['total_orders_pending'], 0)
