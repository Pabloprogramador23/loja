from .cart import Cart
from decimal import Decimal

def cart(request):
    cart_obj = Cart(request)
    tenant = getattr(request, 'tenant', None)

    store_delivery_fee = Decimal('0.00')
    free_delivery_threshold = None
    effective_delivery_fee = Decimal('0.00')

    if tenant:
        store_delivery_fee = tenant.delivery_fee or Decimal('0.00')
        free_delivery_threshold = tenant.free_delivery_threshold
        subtotal = cart_obj.get_total_price()
        if free_delivery_threshold is not None and subtotal >= free_delivery_threshold:
            effective_delivery_fee = Decimal('0.00')
        else:
            effective_delivery_fee = store_delivery_fee

    subtotal = cart_obj.get_total_price()
    cart_total_with_fee = subtotal + effective_delivery_fee

    # Diferença para atingir o threshold (para mensagem motivacional)
    threshold_gap = None
    if free_delivery_threshold is not None and effective_delivery_fee > Decimal('0.00'):
        threshold_gap = max(Decimal('0.00'), free_delivery_threshold - subtotal)

    return {
        'cart': cart_obj,
        'store_delivery_fee': store_delivery_fee,
        'free_delivery_threshold': free_delivery_threshold,
        'effective_delivery_fee': effective_delivery_fee,
        'cart_total_with_fee': cart_total_with_fee,
        'threshold_gap': threshold_gap,
        'delivery_enabled': tenant.delivery_enabled if tenant else True,
    }

def theme_preference(request):
    """
    Expõe a preferência de tema do usuário logado para os templates.

    Lê de UserSettings de forma defensiva: usuário anônimo, sem registro
    ou qualquer erro de leitura resulta no padrão 'system'. O valor é usado
    para renderizar a classe `dark` server-side (anti-FOUC) no <html>.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'theme_pref': 'system'}

    settings_obj = getattr(user, 'settings', None)
    theme = getattr(settings_obj, 'theme', None) if settings_obj else None
    return {'theme_pref': theme or 'system'}
