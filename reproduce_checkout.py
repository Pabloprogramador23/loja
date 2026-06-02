import os
import django
import json
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store_saas.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from core.views import checkout
from core.models import Product, Store
from core.cart import Cart
from core.utils import set_current_tenant

# Setup
factory = RequestFactory()
store = Store.objects.filter(subdomain='localhost').first()
if not store:
    store = Store.objects.create(name='Local', subdomain='localhost')

# Set Tenant Context
set_current_tenant(store)

# Ensure product
product = Product.objects.filter(store=store).first()
if not product:
    from core.models import Category
    cat = Category.objects.create(name='Test Cat', store=store)
    product = Product.objects.create(name='Burger', price=Decimal('25.90'), category=cat, store=store)

from django.contrib.auth.models import AnonymousUser

# Create Request
request = factory.post('/checkout/', {
    'customer_name': 'Test script',
    'customer_phone': '123',
    'delivery_address': 'Address'
})
request.user = AnonymousUser()
request.tenant = store

# Add Session
middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)
request.session.save()

# Add to Cart
cart = Cart(request)
cart.add(product, 2)
print(f"Cart total items: {len(cart)}")

# Run checkout
try:
    response = checkout(request)
    print(f"Response status: {response.status_code}")
    # key check: serialize session to see if it fails
    # Django session serializer is JSON by default
    request.session.save()
    print("Session saved successfully.")
    
except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
