import contextvars
from django.conf import settings
from typing import Optional

# Thread-safe context variable to store the current tenant
_tenant_context = contextvars.ContextVar("current_tenant", default=None)

def get_current_tenant():
    """Retrieves the current tenant from the thread-local context."""
    return _tenant_context.get()

def set_current_tenant(tenant):
    """Sets the current tenant in the thread-local context."""
    token = _tenant_context.set(tenant)
    return token

def reset_current_tenant(token):
    """Resets the tenant context to its previous state."""
    _tenant_context.reset(token)
