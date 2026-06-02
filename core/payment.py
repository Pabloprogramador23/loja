import mercadopago
from django.conf import settings


def create_checkout_pro_preference(order):
    """Cria uma preference do Checkout Pro MP. Retorna dict com init_point e preference_id."""
    token = (
        order.store.mercadopago_access_token
        if order.store.mercadopago_access_token
        else settings.MERCADOPAGO_ACCESS_TOKEN
    )

    # Mock dev quando token dummy
    if token.startswith("TEST-0000"):
        mock_pref_id = f"MOCK_PREF_{order.id}"
        order.mp_preference_id = mock_pref_id
        order.save(update_fields=["mp_preference_id"])
        return {
            "init_point": f"/payment/mock/?order_id={order.id}",
            "preference_id": mock_pref_id,
        }

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    items = [
        {
            "id": str(item.product.id),
            "title": item.product.name[:256],
            "quantity": int(item.quantity),
            "unit_price": float(item.unit_price),
            "currency_id": "BRL",
        }
        for item in order.items.all()
    ]

    preference_data = {
        "items": items,
        "payer": {
            "email": order.user.email,
            "name": order.user.get_full_name() or order.user.username,
        },
        "back_urls": {
            "success": f"{site_url}/payment/success/",
            "pending": f"{site_url}/payment/pending/",
            "failure": f"{site_url}/payment/failure/",
        },
        "auto_return": "approved",
        "external_reference": str(order.id),
        "statement_descriptor": order.store.name[:22],
    }

    sdk = mercadopago.SDK(token)
    result = sdk.preference().create(preference_data)

    if result.get("status") == 403 or result.get("status") != 201:
        print(f"MP Preference Error {result.get('status')}: {result.get('response')}")
        # Fallback mock
        mock_pref_id = f"MOCK_PREF_{order.id}"
        order.mp_preference_id = mock_pref_id
        order.save(update_fields=["mp_preference_id"])
        return {
            "init_point": f"/payment/mock/?order_id={order.id}",
            "preference_id": mock_pref_id,
        }

    response = result["response"]
    pref_id = response["id"]
    order.mp_preference_id = pref_id
    order.save(update_fields=["mp_preference_id"])

    # Usar sandbox_init_point para tokens de teste
    init_point = response.get("sandbox_init_point") if token.startswith("TEST-") else response.get("init_point")
    return {
        "init_point": init_point,
        "preference_id": pref_id,
    }


def create_pix_payment(order, customer_email=None):
    token = (
        order.store.mercadopago_access_token
        if order.store.mercadopago_access_token
        else settings.MERCADOPAGO_ACCESS_TOKEN
    )

    payer_email = customer_email or (order.user.email if order.user and order.user.email else None)
    if not payer_email:
        print("⚠️ PIX: nenhum email de pagador disponível")
        payer_email = "guest@placeholder.invalid"

    sdk = mercadopago.SDK(token)

    payment_data = {
        "transaction_amount": float(order.total_amount),
        "description": f"Pedido #{order.id} - {order.store.name}",
        "payment_method_id": "pix",
        "payer": {"email": payer_email},
        "external_reference": str(order.id),
    }

    result = sdk.payment().create(payment_data)
    response = result.get("response", {})

    # Mock para desenvolvimento quando token dummy ou MP retorna erro
    if result.get("status") == 403 or token.startswith("TEST-0000"):
        mock_id = f"MOCK_{order.id}"
        order.mp_payment_id = mock_id
        order.save(update_fields=["mp_payment_id"])
        return {
            "payment_id": mock_id,
            "qr_code": "00020126580014BR.GOV.BCB.PIX0136123e4567-e89b-12d3-a456-426614174000520400005303986540510.005802BR5913Loja Exemplo6008Brasilia62070503***6304ABCD",
            "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
            "ticket_url": "https://mercadopago.com.br/fake",
            "status": "pending",
        }

    if result.get("status") != 201:
        print(f"MP Error {result.get('status')}: {response}")
        return None

    payment_id = response.get("id")
    if payment_id:
        order.mp_payment_id = str(payment_id)
        order.save(update_fields=["mp_payment_id"])

    return {
        "payment_id": payment_id,
        "qr_code": response.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code"),
        "qr_code_base64": response.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64"),
        "ticket_url": response.get("point_of_interaction", {}).get("transaction_data", {}).get("ticket_url"),
        "status": response.get("status"),
    }
