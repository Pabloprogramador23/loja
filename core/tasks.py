import logging
from celery import shared_task
from .models import Order

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_new_order(self, order_id):
    try:
        order = Order.objects.get(id=order_id)

        # Idempotency guard: webhook already set status to PREPARING before dispatch
        if order.status != Order.Status.PREPARING:
            return

        print(f"--- [CELERY] Processing Order #{order.id} for Store: {order.store.name} ---")
        # TODO: send confirmation email, check stock, notify kitchen system

    except Order.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc)
