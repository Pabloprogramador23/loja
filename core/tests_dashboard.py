from django.test import TransactionTestCase, Client
from fastapi.testclient import TestClient
from core.models import Store, Order
from core.api import app as fastapi_app
from decimal import Decimal

class DashboardTestCase(TransactionTestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Store Dash", subdomain="store-dash", is_active=True)
        self.client_django = Client()
        self.client_fastapi = TestClient(fastapi_app)
        
        # Create an order
        Order.objects.create(
            store=self.store,
            customer_name="Manager Test",
            total_amount=Decimal('50.00'),
            status=Order.Status.PENDING
        )

    def test_order_details_modal_non_staff_returns_403(self):
        from django.contrib.auth.models import User
        non_staff = User.objects.create_user('nonstaff', 'ns@test.com', 'pass123')
        self.client_django.login(username='nonstaff', password='pass123')
        order = Order.objects.first()
        response = self.client_django.get(
            f'/dashboard/order/{order.id}/details/',
            HTTP_X_TENANT_SUBDOMAIN='store-dash'
        )
        self.assertEqual(response.status_code, 403)

    def test_order_details_modal_staff_returns_200(self):
        from django.contrib.auth.models import User
        staff = User.objects.create_user('staffuser', 'staff@test.com', 'pass123', is_staff=True)
        self.client_django.login(username='staffuser', password='pass123')
        order = Order.objects.first()
        response = self.client_django.get(
            f'/dashboard/order/{order.id}/details/',
            HTTP_X_TENANT_SUBDOMAIN='store-dash'
        )
        self.assertEqual(response.status_code, 200)

    def test_fastapi_orders_endpoint(self):
        # Determine the header. In TestClient(fastapi_app), root_path might strip prefix, 
        # but our app is mounted at /api. 
        # If testing FastAPI *app* directly, paths are relative to IT. So "/orders" works.
        
        response = self.client_fastapi.get(
            "/orders", 
            headers={"X-Tenant-Subdomain": "store-dash"}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Manager Test", response.text)
        self.assertIn("R$ 50.00", response.text)
        self.assertIn("bg-yellow-100", response.text) # Pending color
