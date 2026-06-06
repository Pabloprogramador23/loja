from decimal import Decimal
from django.conf import settings
from .models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        # Isolate cart by tenant
        # If no tenant (e.g. admin or invalid), use 'default' (though middleware should prevent this ideally)
        tenant_id = request.tenant.id if hasattr(request, 'tenant') and request.tenant else 'default'
        self.cart_id = f'cart_{tenant_id}'
        cart = self.session.get(self.cart_id)
        if not cart:
            cart = self.session[self.cart_id] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        # Explicitly re-assign to session to ensure it persists
        self.session[self.cart_id] = self.cart
        self.session.modified = True

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        # Create a map for easy lookup
        product_map = {str(p.id): p for p in products}

        for product_id, item_data in self.cart.items():
            # Create a detached copy for yielding
            item = item_data.copy()
            product = product_map.get(str(product_id))
            
            if product:
                item['product'] = product
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                yield item

    @property
    def total_items(self):
        return sum(item['quantity'] for item in self.cart.values())

    def __len__(self):
        return self.total_items

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        self.cart = {}
        self.session[self.cart_id] = self.cart
        self.session.modified = True
