from fastapi.testclient import TestClient
from core.api import app
from core.models import Store
from django.test import TransactionTestCase
 # TransactionTestCase is needed for async DB access in tests or ensuring visibility of data 
 # created in test setup if code uses new connection.
 # However, standard TestCase wraps in transaction.
 # FastAPI TestClient runs synchronously.
 # We must ensure the DB loop handling works.
 # Using async testing support from Django 5 + httpx is better but TestClient is simple.
 # Let's see if TestClient (Starlette) plays nice with Django synchronous test db transaction wrapper.
 # Often it requires 'TransactionTestCase' to allow thread modifications if threads are involved.
 # But here everything is in same process.
 
class ApiTestCase(TransactionTestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.store = Store.objects.create(name="Api Store", subdomain="api-store", is_active=True)

    def test_status_endpoint_success(self):
        # We need to act as if we are external
        # The TestClient hits the FastAPI app directly.
        # It bypasses asgi.py routing but tests core/api.py logic
        
        headers = {"X-Tenant-Subdomain": "api-store"}
        response = self.client.get("/status", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "tenant": "Api Store"})

    def test_status_endpoint_missing_tenant(self):
        headers = {"X-Tenant-Subdomain": "non-existent"}
        response = self.client.get("/status", headers=headers)
        self.assertEqual(response.status_code, 404)
