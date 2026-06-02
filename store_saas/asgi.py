import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store_saas.settings')

# Initialize Django ASGI app
django_app = get_asgi_application()

# Import FastAPI app after Django setup
from core.api import app as fastapi_app

async def application(scope, receive, send):
    """
    Hybrid Router: Dispatches requests to FastAPI or Django based on path.
    """
    if scope['type'] == 'http':
        path = scope['path']
        if path.startswith('/api'):
            # Strip '/api' prefix so FastAPI sees '/orders' instead of '/api/orders'
            scope['path'] = path[4:]
            scope['root_path'] = '/api'
            # Delegate to FastAPI
            await fastapi_app(scope, receive, send)
            return

    # Delegate to Django
    await django_app(scope, receive, send)
