from decimal import Decimal
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from core.models import Category, Order, OrderItem, Product, Store
from core.utils import reset_current_tenant, set_current_tenant

class CheckoutTestCase(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Store Checkout", subdomain="store-checkout", is_active=True)
        self.category = Category.objects.create(name="Food", store=self.store)
        self.product = Product.objects.create(
            name="Burger", 
            category=self.category, 
            price=Decimal('10.00'), 
            store=self.store
        )
        self.client = Client()

    @patch('core.tasks.process_new_order.delay')
    def test_checkout_flow(self, mock_task):
        # 1. Add to Cart
        # Need to simulate tenant header for session isolation
        # However, standard Client session middleware doesn't read header automatically for key generation 
        # unless we pass it to every request OR middleware does it.
        # TenantMiddleware extracts from header. Cart uses request.tenant.
        
        headers = {'HTTP_X_TENANT_SUBDOMAIN': 'store-checkout'}
        
        # Add to cart
        response = self.client.post(reverse('add_to_cart', args=[self.product.id]), **headers)
        self.assertEqual(response.status_code, 200)
        
        # 2. Checkout
        data = {
            'customer_name': 'John Doe',
            'customer_phone': '555-0123',
            'delivery_address': '123 Main St',
            'customer_email': 'johndoe@test.com',
        }

        response = self.client.post(reverse('checkout'), data, **headers)

        # Verify success response — checkout redireciona para página de pagamento PIX
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PIX")
        self.assertContains(response, "10,00")  # total do pedido

        # Verify Order created
        order = Order.objects.last()
        self.assertIsNotNone(order)
        self.assertEqual(order.customer_name, 'John Doe')
        self.assertEqual(order.total_amount, Decimal('10.00'))
        self.assertEqual(order.store, self.store)

        # Task is dispatched from webhook, not from checkout — should not be called here
        mock_task.assert_not_called()

        # Verify Cart Cleared (Counter OOB should be 0)
        self.assertContains(response, '0')

    @patch('core.tasks.process_new_order.delay')
    def test_checkout_includes_delivery_fee_in_total(self, mock_task):
        """Taxa de entrega é somada ao total e snapshottada no pedido."""
        self.store.delivery_fee = Decimal('5.00')
        self.store.save()
        headers = {'HTTP_X_TENANT_SUBDOMAIN': 'store-checkout'}
        self.client.post(reverse('add_to_cart', args=[self.product.id]), **headers)
        data = {
            'customer_name': 'Fee User',
            'customer_phone': '555-0001',
            'delivery_address': '1 Fee St',
            'customer_email': 'fee@test.com',
        }
        self.client.post(reverse('checkout'), data, **headers)
        order = Order.objects.last()
        self.assertEqual(order.delivery_fee, Decimal('5.00'))
        self.assertEqual(order.total_amount, Decimal('15.00'))  # 10 produto + 5 taxa

    @patch('core.tasks.process_new_order.delay')
    def test_checkout_threshold_grants_free_delivery(self, mock_task):
        """Subtotal >= threshold → delivery_fee = 0.00 no pedido."""
        self.store.delivery_fee = Decimal('5.00')
        self.store.free_delivery_threshold = Decimal('10.00')
        self.store.save()
        headers = {'HTTP_X_TENANT_SUBDOMAIN': 'store-checkout'}
        self.client.post(reverse('add_to_cart', args=[self.product.id]), **headers)
        data = {
            'customer_name': 'Threshold User',
            'customer_phone': '555-0002',
            'delivery_address': '2 Threshold Ave',
            'customer_email': 'threshold@test.com',
        }
        self.client.post(reverse('checkout'), data, **headers)
        order = Order.objects.last()
        self.assertEqual(order.delivery_fee, Decimal('0.00'))
        self.assertEqual(order.total_amount, Decimal('10.00'))  # sem taxa pois subtotal = threshold

    @patch('core.tasks.process_new_order.delay')
    def test_checkout_below_threshold_charges_fee(self, mock_task):
        """Subtotal < threshold → taxa de entrega cobrada normalmente."""
        self.store.delivery_fee = Decimal('5.00')
        self.store.free_delivery_threshold = Decimal('50.00')
        self.store.save()
        headers = {'HTTP_X_TENANT_SUBDOMAIN': 'store-checkout'}
        self.client.post(reverse('add_to_cart', args=[self.product.id]), **headers)
        data = {
            'customer_name': 'Below User',
            'customer_phone': '555-0003',
            'delivery_address': '3 Below Rd',
            'customer_email': 'below@test.com',
        }
        self.client.post(reverse('checkout'), data, **headers)
        order = Order.objects.last()
        self.assertEqual(order.delivery_fee, Decimal('5.00'))
        self.assertEqual(order.total_amount, Decimal('15.00'))

    def test_checkout_snapshot_preserved_after_store_fee_change(self):
        """Alterar a taxa da loja não afeta delivery_fee de pedido já criado."""
        self.store.delivery_fee = Decimal('3.00')
        self.store.save()
        order = Order.objects.create(
            customer_name="Snap",
            customer_phone="999",
            delivery_address="Snap St",
            status=Order.Status.PENDING,
            total_amount=Decimal('13.00'),
            delivery_fee=Decimal('3.00'),
            store=self.store,
        )
        self.store.delivery_fee = Decimal('9.00')
        self.store.save()
        order.refresh_from_db()
        self.assertEqual(order.delivery_fee, Decimal('3.00'))

    @patch('core.tasks.process_new_order.delay')
    def test_checkout_guest_without_email_fails(self, mock_task):
        headers = {'HTTP_X_TENANT_SUBDOMAIN': 'store-checkout'}
        self.client.post(reverse('add_to_cart', args=[self.product.id]), **headers)

        data = {
            'customer_name': 'Guest User',
            'customer_phone': '555-0000',
            'delivery_address': '456 Guest St',
            # customer_email intentionally omitted
        }
        response = self.client.post(reverse('checkout'), data, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email')  # error message mentions email
        # No order should have been created
        self.assertEqual(Order.objects.count(), 0)
