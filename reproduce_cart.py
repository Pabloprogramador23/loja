
import os
import django
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "store_saas.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from core.models import Store, Product, Category
from core.cart import Cart

def reproduce():
    # Setup
    print("--- Setting up environment ---")
    store, _ = Store.objects.get_or_create(name="Test Store", subdomain="teststore")
    cat, _ = Category.objects.get_or_create(name="Test Cat", store=store)
    p1, _ = Product.objects.get_or_create(name="P1", price=10.00, category=cat, store=store)
    p2, _ = Product.objects.get_or_create(name="P2", price=20.00, category=cat, store=store)

    # Simulate Request
    factory = RequestFactory()
    request = factory.get('/')
    request.tenant = store
    
    # Add Session
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    print("\n--- Testing Cart Increment ---")
    # Action 1: Add P1
    print(f"Adding P1 (1st time)...")
    cart = Cart(request)
    cart.add(p1)
    print(f"Cart P1 Qty: {cart.cart[str(p1.id)]['quantity']}")
    
    # Simulate new request (persist session)
    request.session.save()
    
    # Action 2: Add P1 again
    print(f"Adding P1 (2nd time)...")
    cart2 = Cart(request) # Re-init cart with same session
    cart2.add(p1)
    
    qty = cart2.cart[str(p1.id)]['quantity']
    print(f"Cart P1 Qty: {qty}")
    
    if qty == 2:
        print("SUCCESS: Quantity incremented correctly.")
    else:
        print(f"FAILURE: Quantity is {qty}, expected 2.")

    # Action 3: Add P2
    print(f"\nAdding P2...")
    cart2.add(p2)
    print(f"Cart P2 Qty: {cart2.cart[str(p2.id)]['quantity']}")
    
    request.session.save()
    cart3 = Cart(request)
    
    total = len(cart3)
    print(f"\nTotal Items in Cart: {total}")
    if total == 3: # 2 of P1 + 1 of P2
         print("SUCCESS: Total items count seems correct.")
    else:
         print(f"FAILURE: Total items {total}, expected 3.")

if __name__ == "__main__":
    reproduce()
