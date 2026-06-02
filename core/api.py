import hashlib
import hmac
import logging
from decimal import Decimal

from fastapi import FastAPI, Depends, Header, HTTPException, Request, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import mercadopago
from asgiref.sync import sync_to_async
from django.conf import settings

from core.models import Order, Store
from core.utils import reset_current_tenant, set_current_tenant

app = FastAPI()
logger = logging.getLogger(__name__)


async def get_tenant_dependency(x_tenant_subdomain: str = Header(..., alias="X-Tenant-Subdomain")):
    """
    Dependency to resolve the tenant from the header and set the context.
    Uses 'yield' to ensure context cleanup after the request.
    """
    try:
        tenant = await Store.objects.aget(subdomain=x_tenant_subdomain, is_active=True)
    except Store.DoesNotExist:
        raise HTTPException(status_code=404, detail="Tenant not found")

    token = set_current_tenant(tenant)
    try:
        yield tenant
    finally:
        reset_current_tenant(token)


@app.get("/status")
async def status(tenant: Store = Depends(get_tenant_dependency)):
    return {"status": "ok", "tenant": tenant.name}


@app.get("/orders", response_class=HTMLResponse)
async def get_orders(tenant: Store = Depends(get_tenant_dependency)):
    """
    Returns HTML fragment of orders for the dashboard table.
    """
    orders = []
    async for order in Order.objects.all().order_by('-created_at'):
        orders.append(order)

    if not orders:
        return """
        <tr>
            <td colspan="5" class="px-6 py-4 text-center text-sm text-gray-500">
                Nenhum pedido encontrado.
            </td>
        </tr>
        """

    html = ""
    for order in orders:
        status_colors = {
            Order.Status.PENDING: "bg-yellow-100 text-yellow-800",
            Order.Status.CONFIRMED: "bg-green-100 text-green-800",
            Order.Status.PREPARING: "bg-blue-100 text-blue-800",
            Order.Status.DELIVERING: "bg-indigo-100 text-indigo-800",
            Order.Status.COMPLETED: "bg-green-100 text-green-800",
            Order.Status.CANCELED: "bg-red-100 text-red-800",
        }
        status_badges = {
            Order.Status.PENDING: "Pendente",
            Order.Status.CONFIRMED: "Confirmado",
            Order.Status.PREPARING: "Preparando",
            Order.Status.DELIVERING: "Em trânsito",
            Order.Status.COMPLETED: "Concluído",
            Order.Status.CANCELED: "Cancelado",
        }

        status_badge = f'<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full {status_colors.get(order.status, "bg-gray-100 text-gray-800")}">{status_badges.get(order.status, order.status)}</span>'

        html += f"""
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                <button hx-get="/dashboard/order/{order.id}/details" hx-target="#modal-container"
                        class="text-indigo-600 hover:text-indigo-900 font-bold hover:underline">
                    #{order.id}
                </button>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {order.customer_name}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                R$ {order.total_amount}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                {status_badge}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {order.created_at.strftime("%d/%m/%Y %H:%M")}
            </td>
        </tr>
        """
    return html


@app.get("/orders/{order_id}/track", response_class=HTMLResponse)
async def get_order_progress(order_id: int, tenant: Store = Depends(get_tenant_dependency)):
    try:
        order = await Order.objects.aget(id=order_id)
    except Order.DoesNotExist:
        return "<div>Pedido não encontrado</div>"

    status = order.status

    width = "w-0"

    if status == Order.Status.PENDING:
        width = "w-1/4"
        active_step_index = 0
    elif status == Order.Status.PREPARING:
        width = "w-2/4"
        active_step_index = 1
    elif status == Order.Status.DELIVERING:
        width = "w-3/4"
        active_step_index = 2
    elif status == Order.Status.COMPLETED:
        width = "w-full"
        active_step_index = 3
    elif status == Order.Status.CANCELED:
        width = "w-full"
        active_step_index = -1
    else:
        active_step_index = 0

    color_class = "bg-green-500" if status != Order.Status.CANCELED else "bg-red-500"

    steps_html = ""
    steps_labels = ["Recebido", "Preparando", "Saiu", "Entregue"]

    for i, label in enumerate(steps_labels):
        icon_color = "text-green-600" if i <= active_step_index and status != Order.Status.CANCELED else "text-gray-400"
        if status == Order.Status.CANCELED:
            icon_color = "text-red-400"

        steps_html += f"""
        <div class="flex flex-col items-center">
            <div class="rounded-full transition duration-500 ease-in-out h-8 w-8 py-3 border-2 border-gray-300 {icon_color if i > active_step_index else ('bg-green-500 border-green-500 text-white' if status != Order.Status.CANCELED else 'bg-red-500 border-red-500 text-white')} flex items-center justify-center">
                {i + 1}
            </div>
            <div class="text-xs font-medium text-center mt-2 {icon_color}">{label}</div>
        </div>
        """

    return f"""
    <div class="w-full py-6" hx-trigger="every 5s" hx-get="/api/orders/{order_id}/track" hx-swap="outerHTML">
         <div class="mb-4 text-center">
             <span class="px-4 py-2 rounded-full text-sm font-bold {'bg-red-100 text-red-800' if status == Order.Status.CANCELED else 'bg-green-100 text-green-800'}">
                {order.get_status_display()}
             </span>
         </div>

        <div class="relative pt-1 px-4">
            <div class="overflow-hidden h-4 mb-4 text-xs flex rounded-full bg-gray-200">
                <div class="{width} shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center {color_class} transition-all duration-500"></div>
            </div>

            <div class="flex justify-between w-full px-2">
                {steps_html}
            </div>
        </div>
    </div>
    """


# T015: scoped ao tenant via Depends(get_tenant_dependency)
@app.get("/orders/{order_id}/check-status")
async def check_order_status(order_id: int, tenant: Store = Depends(get_tenant_dependency)):
    try:
        order = await Order.objects.aget(id=order_id)
        paid_statuses = [Order.Status.PREPARING, Order.Status.DELIVERING, Order.Status.COMPLETED]
        is_paid = order.status in paid_statuses
        return {"status": order.status, "paid": is_paid}
    except Order.DoesNotExist:
        return {"error": "Order not found"}


# T013 + T014: webhook com HMAC, sem backdoor hardcoded, lookup por mp_payment_id
@app.post("/webhooks/mercadopago")
async def mercadopago_webhook(request: Request, payload: dict = Body(...)):
    webhook_secret = settings.MERCADOPAGO_WEBHOOK_SECRET

    # Validar HMAC quando o segredo estiver configurado
    if webhook_secret:
        x_signature = request.headers.get("x-signature", "")
        x_request_id = request.headers.get("x-request-id", "")
        payment_id_str = str(payload.get("data", {}).get("id", ""))

        sig_parts = dict(
            part.split("=", 1) for part in x_signature.split(",") if "=" in part
        )
        ts = sig_parts.get("ts", "")
        v1 = sig_parts.get("v1", "")
        manifest = f"id:{payment_id_str};request-id:{x_request_id};ts:{ts}"
        expected = hmac.new(
            webhook_secret.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, v1):
            client_host = request.client.host if request.client else "unknown"
            logger.warning("HMAC validation failed for webhook from %s", client_host)
            raise HTTPException(status_code=401, detail="Invalid signature")

    elif not settings.REVERSA_TESTING:
        # Sem segredo configurado e fora do modo de teste → rejeitar
        raise HTTPException(status_code=401, detail="Webhook secret not configured")

    action = payload.get("action")

    # Backdoor de teste — ativo APENAS quando REVERSA_TESTING=true
    if settings.REVERSA_TESTING and action == "test.approved":
        order_id = payload.get("order_id")
        if order_id:
            await sync_to_async(update_paid_order)(order_id)
            return {"status": "ok", "mode": "test"}

    if action in ("payment.updated", "payment.created"):
        payment_id = payload.get("data", {}).get("id")
        if payment_id:
            # Buscar payment no MP usando token global para ter acesso ao external_reference
            sdk_global = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            payment_info = sdk_global.payment().get(payment_id)
            payment_response = payment_info.get("response", {})
            mp_status = payment_response.get("status")
            external_ref = payment_response.get("external_reference")

            # Lookup por external_reference (order.id) — compatível com Checkout Pro
            order = None
            if external_ref:
                try:
                    order = await Order.objects.aget(id=int(external_ref))
                except (Order.DoesNotExist, ValueError):
                    pass

            # Fallback: lookup por mp_payment_id (compatibilidade com PIX antigo)
            if order is None:
                try:
                    order = await Order.objects.aget(mp_payment_id=str(payment_id))
                except Order.DoesNotExist:
                    logger.warning("Order not found for payment_id=%s external_ref=%s", payment_id, external_ref)
                    return {"status": "ok", "note": "order not found"}

            # Salvar mp_payment_id se ainda não estiver preenchido
            if not order.mp_payment_id:
                order.mp_payment_id = str(payment_id)
                await order.asave(update_fields=["mp_payment_id"])

            # Usar token da loja correta para re-verificar se necessário
            store_token = await sync_to_async(
                lambda: order.store.mercadopago_access_token
            )()
            if store_token and store_token != settings.MERCADOPAGO_ACCESS_TOKEN:
                sdk_tenant = mercadopago.SDK(store_token)
                payment_info = sdk_tenant.payment().get(payment_id)
                mp_status = payment_info.get("response", {}).get("status")

            if mp_status == "approved":
                await sync_to_async(update_paid_order)(order.id)
            elif mp_status in ("cancelled", "expired"):
                await sync_to_async(cancel_order_on_pix_expiry)(order.id)

    return {"status": "ok"}


def update_paid_order(order_id):
    from core.models import Order
    from core.tasks import process_new_order
    try:
        order = Order.objects.get(id=order_id)
        if order.status == Order.Status.PENDING:
            order.status = Order.Status.PREPARING
            order.save()
            process_new_order.delay(order.id)
    except Exception as e:
        logger.error("Error updating order %s to paid: %s", order_id, e)


def cancel_order_on_pix_expiry(order_id):
    from core.models import Order
    try:
        order = Order.objects.get(id=order_id)
        if order.status == Order.Status.PENDING:
            order.status = Order.Status.CANCELED
            order.save()
            logger.info("Order %s auto-canceled due to PIX expiry", order_id)
    except Exception as e:
        logger.error("Error canceling order %s on PIX expiry: %s", order_id, e)
