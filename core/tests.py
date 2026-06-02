from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from core.models import Store, UserSettings, Order, Category, Product
from core.middleware import TenantMiddleware
from core.utils import get_current_tenant, set_current_tenant, reset_current_tenant
from decimal import Decimal
import contextvars

class DeliveryFeeModelTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Fee Store", subdomain="feestore", is_active=True)

    def test_store_delivery_fee_default_is_zero(self):
        self.assertEqual(self.store.delivery_fee, Decimal('0.00'))

    def test_store_free_delivery_threshold_default_is_none(self):
        self.assertIsNone(self.store.free_delivery_threshold)

    def test_store_delivery_fee_can_be_set(self):
        self.store.delivery_fee = Decimal('5.00')
        self.store.save()
        self.store.refresh_from_db()
        self.assertEqual(self.store.delivery_fee, Decimal('5.00'))

    def test_store_free_delivery_threshold_can_be_set(self):
        self.store.free_delivery_threshold = Decimal('50.00')
        self.store.save()
        self.store.refresh_from_db()
        self.assertEqual(self.store.free_delivery_threshold, Decimal('50.00'))

    def test_store_delivery_fee_validator_rejects_negative(self):
        self.store.delivery_fee = Decimal('-1.00')
        with self.assertRaises(ValidationError):
            self.store.full_clean()

    def test_order_delivery_fee_default_is_zero(self):
        token = set_current_tenant(self.store)
        try:
            category = Category.objects.create(name="Cat", store=self.store)
            order = Order.objects.create(
                customer_name="Test",
                customer_phone="99999",
                delivery_address="Rua X",
                status=Order.Status.PENDING,
                total_amount=Decimal('10.00'),
                store=self.store,
            )
            self.assertEqual(order.delivery_fee, Decimal('0.00'))
        finally:
            reset_current_tenant(token)


class TenantTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.store1 = Store.objects.create(name="Store 1", subdomain="store1", is_active=True)
        self.store2 = Store.objects.create(name="Store 2", subdomain="store2", is_active=True)

    def test_tenant_context_utils(self):
        token = set_current_tenant(self.store1)
        self.assertEqual(get_current_tenant(), self.store1)
        reset_current_tenant(token)
        self.assertIsNone(get_current_tenant())

    def test_tenant_middleware_header(self):
        # Create a request with header
        request = self.factory.get('/', headers={'X-Tenant-Subdomain': 'store1'})
        
        def mock_get_response(req):
            # Verify tenant is set in context during request processing
            self.assertEqual(get_current_tenant(), self.store1)
            self.assertEqual(req.tenant, self.store1)
            return None
            
        middleware = TenantMiddleware(mock_get_response)
        middleware(request)
        
        # Verify context is cleared after request
        self.assertIsNone(get_current_tenant())

    def test_tenant_middleware_no_header(self):
        request = self.factory.get('/')
        
        def mock_get_response(req):
            self.assertIsNone(get_current_tenant())
            self.assertIsNone(req.tenant)
            return None

        middleware = TenantMiddleware(mock_get_response)
        middleware(request)


class UserSettingsModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345')

    def test_default_theme_is_system(self):
        settings_obj = UserSettings.objects.create(user=self.user)
        self.assertEqual(settings_obj.theme, 'system')

    def test_one_to_one_constraint(self):
        UserSettings.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            UserSettings.objects.create(user=self.user)

    def test_valid_choices(self):
        valid = {choice.value for choice in UserSettings.Theme}
        self.assertEqual(valid, {'system', 'light', 'dark'})
        for value in valid:
            settings_obj = UserSettings.objects.create(
                user=User.objects.create_user(username=f'u_{value}', password='pw12345'),
                theme=value,
            )
            self.assertEqual(settings_obj.theme, value)


class SetThemeEndpointTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='bob', password='pw12345')
        self.url = reverse('set_theme')

    def test_success_returns_204_and_persists(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'theme': 'dark'})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(UserSettings.objects.get(user=self.user).theme, 'dark')

    def test_invalid_theme_returns_400(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'theme': 'neon'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())

    def test_anonymous_is_blocked(self):
        response = self.client.post(self.url, {'theme': 'dark'})
        self.assertIn(response.status_code, (302, 401))
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())

    def test_get_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_idempotent_resend(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {'theme': 'light'})
        self.client.post(self.url, {'theme': 'light'})
        self.assertEqual(UserSettings.objects.filter(user=self.user).count(), 1)
        self.assertEqual(UserSettings.objects.get(user=self.user).theme, 'light')
