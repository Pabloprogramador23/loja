from django.contrib import admin
from .models import Store, Category, Product, Order, OrderItem
from .utils import get_current_tenant

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'subdomain', 'owner', 'is_active', 'created_at')
    readonly_fields = ('owner',)

class TenantAdmin(admin.ModelAdmin):
    """
    Base Admin class that filters objects by the current tenant.
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        tenant = get_current_tenant()
        # If there is a tenant in context (set by middleware), filter by it.
        # Note: In a real admin scenario, the admin user might be a superuser managing all stores,
        # or a store manager. If it's a store manager, the middleware should have set the tenant.
        # If it is a superuser accessing /admin without specific tenant context, they might want to see everything?
        # The requirement says: "so que o administrador da loja só veja os produtos/pedidos da PRÓPRIA loja".
        
        # We'll rely on get_current_tenant(). If it's set, we filter.
        if tenant:
            return qs.filter(store=tenant)
        return qs

    # Also need to handle saving models to ensure store is set if not already?
    # TenantAwareModel.save handles that if context is set.

@admin.register(Category)
class CategoryAdmin(TenantAdmin):
    list_display = ('name', 'store')

@admin.register(Product)
class ProductAdmin(TenantAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'store')
    list_filter = ('is_available', 'category')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Inlines also need to respect tenant? 
    # Usually inlines are filtered by the parent (Order), which is already filtered.
    # But when adding potential products in a dropdown, we need to filter products by tenant too.
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        tenant = get_current_tenant()
        if tenant and db_field.name == "product":
            kwargs["queryset"] = Product.objects.filter(store=tenant)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Order)
class OrderAdmin(TenantAdmin):
    list_display = ('id', 'customer_name', 'status', 'total_amount', 'created_at', 'store')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(TenantAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'store')
