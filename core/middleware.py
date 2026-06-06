import ipaddress
from django.http import HttpResponse
from .models import Store
from .utils import set_current_tenant, reset_current_tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        hostname = request.get_host().split(':')[0]
        parts = hostname.split('.')

        # Detect IP addresses to avoid misidentifying octets as subdomains
        try:
            ipaddress.ip_address(hostname)
            is_ip = True
        except ValueError:
            is_ip = False

        dev_host = (
            'localhost' in hostname
            or '127.0.0.1' in hostname
            or hostname.endswith('.ngrok-free.dev')
            or hostname.endswith('.ngrok-free.app')
            or hostname.endswith('.ngrok.io')
        )

        # 1. Host-based resolution — production (e.g. loja-a.meusaas.com)
        if not is_ip and not dev_host and len(parts) >= 3:
            subdomain = parts[0]
            try:
                tenant = Store.objects.get(subdomain=subdomain, is_active=True)
            except Store.DoesNotExist:
                # Subdomain present in URL but no matching active store → 404
                return HttpResponse(status=404)

        # 2. Header fallback — dev/API clients (X-Tenant-Subdomain)
        if not tenant:
            tenant_header = request.headers.get('X-Tenant-Subdomain')
            if tenant_header:
                try:
                    tenant = Store.objects.get(subdomain=tenant_header, is_active=True)
                except Store.DoesNotExist:
                    pass

        # 3. Localhost/dev fallback — prefer the authenticated user's own store
        if not tenant and (is_ip or dev_host):
            if hasattr(request, 'user') and request.user.is_authenticated:
                tenant = getattr(request.user, 'owned_store', None)
            if not tenant:
                tenant = Store.objects.filter(is_active=True).first()

        token = set_current_tenant(tenant)
        request.tenant = tenant

        request.user_can_manage = False
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_staff:
                request.user_can_manage = True
            elif tenant and getattr(request.user, 'owned_store', None) == tenant:
                request.user_can_manage = True

        try:
            response = self.get_response(request)
        finally:
            reset_current_tenant(token)

        return response
