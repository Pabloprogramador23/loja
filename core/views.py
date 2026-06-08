import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from decimal import Decimal

from .cart import Cart
from .models import (
    Address, Category, Order, OrderItem, Product, UserProfile, UserSettings,
)
from .tasks import process_new_order

logger = logging.getLogger(__name__)


def user_can_manage_store(request):
    if request.user.is_staff:
        return True
    if request.tenant is None:
        return False
    return getattr(request.user, 'owned_store', None) == request.tenant

def index(request):
    """
    Renderiza a página inicial.
    O tenant já está em request.tenant (via TenantMiddleware).
    """
    return render(request, 'core/index.html', {
        'categories': Category.objects.all(),
        'featured_products': Product.objects.filter(is_available=True).order_by('?')[:4]
    })

def catalog(request):
    """
    Renderiza o catálogo de produtos.
    Lida com requisições HTMX para filtrar produtos por categoria.
    """
    categories = Category.objects.all()
    products = Product.objects.filter(is_available=True)
    
    category_id = request.GET.get('category_id')
    if category_id:
        products = products.filter(category_id=category_id)
        
    context = {
        'categories': categories,
        'products': products,
        'selected_category_id': int(category_id) if category_id else None,
        'session_delivery_address': request.session.get('session_delivery_address', ''),
    }

    if request.htmx:
        return render(request, 'core/partials/product_list.html', context)
        
    return render(request, 'core/catalog.html', context)

@require_POST
def add_to_cart(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product)
    
    context = {'cart': cart}
    response = render(request, 'core/partials/add_to_cart_response.html', context)
    
    # Dispara evento client-side para toast e atualização do carrinho
    import json
    response['HX-Trigger'] = json.dumps({
        'showMessage': 'Produto adicionado!',
        'updateCart': True
    })
    return response

@require_POST
def clear_cart(request):
    cart = Cart(request)
    cart.clear()
    
    # Retorna o drawer do carrinho vazio
    return render(request, 'core/partials/cart_drawer.html', {'cart': cart})

@require_POST
def save_location(request):
    address = request.POST.get('delivery_address', '').strip()[:500]
    request.session['session_delivery_address'] = address
    return HttpResponse('')


def cart_detail(request):
    cart = Cart(request)
    addresses = []
    profile_phone = ''
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_phone = profile.phone

    return render(request, 'core/partials/cart_drawer.html', {
        'cart': cart,
        'addresses': addresses,
        'profile_phone': profile_phone,
        'session_delivery_address': request.session.get('session_delivery_address', ''),
    })

@require_POST
@login_required
def save_address(request):
    user = request.user
    
    # Tratamento simples do formulário manualmente para agilidade
    street = request.POST.get('street')
    number = request.POST.get('number')
    neighborhood = request.POST.get('neighborhood')
    city = request.POST.get('city')
    state = request.POST.get('state')
    zip_code = request.POST.get('zip_code')
    
    address_error = None
    if all([street, number, neighborhood, city, state]):
        try:
            Address.objects.create(
                user=user,
                street=street,
                number=number,
                neighborhood=neighborhood,
                city=city,
                state=state,
                zip_code=zip_code or ""
            )
        except ValidationError as e:
            address_error = str(e.message)

    addresses = Address.objects.filter(user=user)
    return render(request, 'core/partials/address_list.html', {
        'addresses': addresses,
        'address_error': address_error,
    })

@require_POST
@login_required
def delete_address(request, address_id):
    Address.objects.filter(id=address_id, user=request.user).delete()
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'core/partials/address_list.html', {'addresses': addresses})

def _checkout_error(request, cart, error):
    """Renderiza o drawer com erro mantendo contexto de endereços para usuários logados."""
    ctx = {
        'cart': cart,
        'error': error,
        'session_delivery_address': request.session.get('session_delivery_address', ''),
    }
    if request.user.is_authenticated:
        ctx['addresses'] = Address.objects.filter(user=request.user)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        ctx['profile_phone'] = profile.phone
    return render(request, 'core/partials/cart_drawer.html', ctx)


@require_POST
def checkout(request):
    cart = Cart(request)

    store = request.tenant
    if store and not store.delivery_enabled:
        return _checkout_error(request, cart, 'A loja não está aceitando pedidos no momento.')

    if len(cart) == 0:
        return _checkout_error(request, cart, 'Carrinho vazio')

    name = request.POST.get('customer_name', '').strip()
    phone = request.POST.get('customer_phone', '').strip()
    address = request.POST.get('delivery_address', '').strip()
    customer_email = request.POST.get('customer_email', '').strip()

    # Para usuários logados: preenche lacunas com dados do perfil
    if request.user.is_authenticated:
        if not name:
            name = request.user.get_full_name() or request.user.username
        if not phone:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            phone = profile.phone
        if not address:
            saved = Address.objects.filter(user=request.user).first()
            if saved:
                address = f'{saved.street}, {saved.number} - {saved.neighborhood}, {saved.city} - {saved.state}'

    if not all([name, phone, address]):
        return _checkout_error(request, cart, 'Preencha todos os campos obrigatórios.')

    # Email obrigatório para convidados (usuários autenticados usam user.email)
    if not request.user.is_authenticated and not customer_email:
        return _checkout_error(request, cart, 'Informe seu email para receber o QR Code PIX.')

    store = request.tenant
    subtotal = cart.get_total_price()

    threshold = store.free_delivery_threshold if store else None
    if threshold is not None and subtotal >= threshold:
        effective_fee = Decimal('0.00')
    else:
        effective_fee = store.delivery_fee if store else Decimal('0.00')

    payment_method = request.POST.get('payment_method', 'online')
    if payment_method not in Order.PaymentMethod.values:
        payment_method = 'online'

    if store:
        allowed_methods = {
            'online': store.payment_online_enabled,
            'cash':   store.payment_cash_enabled,
            'card':   store.payment_card_enabled,
        }
        if not any(allowed_methods.values()):
            return _checkout_error(request, cart, 'Nenhum método de pagamento disponível no momento.')
        if not allowed_methods.get(payment_method, False):
            return _checkout_error(request, cart, 'Método de pagamento não disponível.')

    # Valida change_amount antes de criar o pedido
    change_amount = None
    if payment_method == Order.PaymentMethod.CASH:
        raw_change = request.POST.get('change_amount', '').strip()
        if raw_change:
            try:
                change_amount = Decimal(raw_change)
                if change_amount < 0:
                    raise ValueError
            except (Exception,):
                return _checkout_error(request, cart, 'Valor de troco inválido. Informe um valor positivo ou deixe em branco.')

    card_type = ''
    if payment_method == Order.PaymentMethod.CARD:
        raw_card = request.POST.get('card_type', '').strip()
        if raw_card in Order.CardType.values:
            card_type = raw_card

    with transaction.atomic():
        order = Order.objects.create(
            customer_name=name,
            customer_phone=phone,
            customer_email=customer_email,
            delivery_address=address,
            total_amount=subtotal + effective_fee,
            delivery_fee=effective_fee,
            status=Order.Status.CONFIRMED if payment_method != 'online' else Order.Status.PENDING,
            payment_method=payment_method,
            change_amount=change_amount,
            card_type=card_type,
        )

        if request.user.is_authenticated:
            order.user = request.user
            order.save()
        else:
            request.session['guest_order_id'] = order.id

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['price']
            )

        cart.clear()

    if request.user.is_authenticated and phone:
        UserProfile.objects.update_or_create(user=request.user, defaults={'phone': phone})

    if payment_method != 'online':
        from .tasks import process_new_order
        process_new_order.delay(order.id)
        return HttpResponse(f'<script>window.location.href="/payment/success/?order_id={order.id}";</script>')

    from .payment import create_checkout_pro_preference
    result = create_checkout_pro_preference(order)

    if not result:
        return render(request, 'core/partials/checkout_error.html', {'error': 'Erro ao gerar pagamento. Tente novamente.'})

    init_point = result['init_point']
    return HttpResponse(f'<script>window.location.href="{init_point}";</script>')


def payment_view(request, order_id):
    """Mantida para acesso histórico via sessão."""
    order = get_object_or_404(Order, id=order_id)
    payment_data = request.session.get(f'payment_data_{order_id}', {})
    return render(request, 'core/payment_pix.html', {'order': order, 'payment_data': payment_data})


def payment_success_view(request):
    payment_id = request.GET.get('payment_id', '')
    preference_id = request.GET.get('preference_id', '')
    status = request.GET.get('status', 'approved')
    order = None
    if preference_id:
        order = Order.objects.filter(mp_preference_id=preference_id).first()
    if order is None:
        order_id = request.GET.get('order_id') or request.session.get('guest_order_id')
        if order_id:
            order = Order.objects.filter(id=order_id).first()

    # Fallback: se o webhook ainda não chegou, atualiza o pedido aqui mesmo
    if order and status == 'approved' and order.status == Order.Status.PENDING:
        from core.api import update_paid_order
        update_paid_order(order.id)
        order.refresh_from_db()

    return render(request, 'core/payment_success.html', {
        'payment_id': payment_id,
        'preference_id': preference_id,
        'status': status,
        'order': order,
    })


def payment_pending_view(request):
    payment_id = request.GET.get('payment_id', '')
    preference_id = request.GET.get('preference_id', '')
    external_reference = request.GET.get('external_reference', '')
    order = None
    if preference_id:
        order = Order.objects.filter(mp_preference_id=preference_id).first()
    if order is None and external_reference:
        order = Order.objects.filter(id=external_reference).first()
    if order is None:
        order_id = request.GET.get('order_id') or request.session.get('guest_order_id')
        if order_id:
            order = Order.objects.filter(id=order_id).first()
    if order is None:
        logger.warning('018 payment_pending order not found: preference_id=%s ext=%s', preference_id, external_reference)
    return render(request, 'core/payment_pending.html', {'payment_id': payment_id, 'order': order})


def payment_failure_view(request):
    payment_id = request.GET.get('payment_id', '')
    preference_id = request.GET.get('preference_id', '')
    external_reference = request.GET.get('external_reference', '')
    order = None
    if preference_id:
        order = Order.objects.filter(mp_preference_id=preference_id).first()
    if order is None and external_reference:
        order = Order.objects.filter(id=external_reference).first()
    if order is None:
        order_id = request.GET.get('order_id') or request.session.get('guest_order_id')
        if order_id:
            order = Order.objects.filter(id=order_id).first()
    if order is None:
        logger.warning('018 payment_failure order not found: preference_id=%s ext=%s', preference_id, external_reference)
    return render(request, 'core/payment_failure.html', {'payment_id': payment_id, 'order': order})


def payment_waiting_view(request):
    order_id = request.GET.get('order_id') or request.session.get('guest_order_id')
    order = None
    if order_id:
        order = Order.objects.filter(id=order_id).first()
    return render(request, 'core/payment_waiting.html', {'order': order})


def payment_waiting_status_view(request):
    order_id = request.GET.get('order_id') or request.session.get('guest_order_id')
    order = None
    if order_id:
        order = Order.objects.filter(id=order_id).first()
    response = render(request, 'core/partials/payment_waiting_status.html', {'order': order})
    if order and order.status != Order.Status.PENDING:
        response['HX-Trigger'] = 'stopPolling'
    return response


def payment_mock_view(request):
    from django.conf import settings as conf_settings
    if not getattr(conf_settings, 'REVERSA_TESTING', False):
        return HttpResponse('Disponível apenas em modo de teste.', status=403)
    order_id = request.GET.get('order_id')
    if not order_id:
        return HttpResponse('order_id obrigatório.', status=400)
    from core.api import update_paid_order
    try:
        update_paid_order(int(order_id))
    except Exception:
        pass
    return redirect(f'/payment/success/?order_id={order_id}&status=approved')



@login_required
def dashboard(request):
    if not user_can_manage_store(request):
        return redirect('index')

    from django.db.models import Sum, Count
    from django.utils import timezone
    
    today = timezone.localdate()
    
    # Stats
    total_orders_pending = Order.objects.filter(
        status__in=[Order.Status.PENDING, Order.Status.CONFIRMED]
    ).count()
    total_sales = Order.objects.filter(status=Order.Status.COMPLETED).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    todays_orders = Order.objects.filter(created_at__date=today).count()
    
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    return render(request, 'core/manager/dashboard.html', {
        'total_orders_pending': total_orders_pending,
        'total_sales': total_sales,
        'todays_orders': todays_orders,
        'recent_orders': recent_orders
    })

@login_required
def account_dashboard(request):
    addresses = Address.objects.filter(user=request.user)
    last_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    if request.method == 'POST':
        from .forms import UserProfileForm
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('account_dashboard')
    else:
        from .forms import UserProfileForm
        form = UserProfileForm(instance=request.user)

    return render(request, 'core/account/dashboard.html', {
        'form': form,
        'addresses': addresses,
        'last_orders': last_orders
    })

@login_required
def account_addresses(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'core/account/addresses.html', {'addresses': addresses})

@login_required
def account_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/account/orders.html', {'orders': orders})

@login_required
def account_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/account/order_detail.html', {'order': order})

# Alias for backward compatibility if needed, or redirect
@login_required
def my_orders(request):
    return redirect('account_orders')

from django.http import HttpResponse

@login_required
def order_details_modal(request, order_id):
    if not user_can_manage_store(request):
        return HttpResponse(status=403)

    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/partials/order_modal.html', {'order': order})

@login_required
def manager_orders(request):
    if not user_can_manage_store(request):
        return redirect('index')

    status_filter = request.GET.get('status')
    orders = Order.objects.exclude(status='OPEN').order_by('-created_at')
    if status_filter and status_filter in Order.Status.values:
        orders = orders.filter(status=status_filter)

    return render(request, 'core/manager/orders.html', {
        'orders': orders,
        'current_status': status_filter,
        'Order': Order,
    })


@login_required
def manager_orders_rows(request):
    if not user_can_manage_store(request):
        return HttpResponse(status=403)

    status_filter = request.GET.get('status')
    orders = Order.objects.exclude(status='OPEN').order_by('-created_at')
    if status_filter and status_filter in Order.Status.values:
        orders = orders.filter(status=status_filter)

    return render(request, 'core/manager/partials/orders_rows.html', {'orders': orders})

@login_required
def manager_products(request):
    if not user_can_manage_store(request):
        return redirect('index')
    
    products = Product.objects.all().order_by('category', 'name')
    return render(request, 'core/manager/products.html', {'products': products})

@login_required
def manager_product_create(request):
    if not user_can_manage_store(request):
        return redirect('index')
        
    if request.method == 'POST':
        from .forms import ProductForm
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            nome = form.cleaned_data.get('new_category_name', '').strip()
            if nome:
                category, _ = Category.objects.get_or_create(name__iexact=nome, defaults={'name': nome})
                form.instance.category = category
            form.save()
            return redirect('manager_products')
    else:
        from .forms import ProductForm
        form = ProductForm()

    return render(request, 'core/manager/product_form.html', {'form': form, 'title': 'Novo Produto'})

@login_required
def manager_product_edit(request, product_id):
    if not user_can_manage_store(request):
        return redirect('index')
        
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        from .forms import ProductForm
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            nome = form.cleaned_data.get('new_category_name', '').strip()
            if nome:
                category, _ = Category.objects.get_or_create(name__iexact=nome, defaults={'name': nome})
                form.instance.category = category
            form.save()
            return redirect('manager_products')
    else:
        from .forms import ProductForm
        form = ProductForm(instance=product)

    return render(request, 'core/manager/product_form.html', {'form': form, 'title': f'Editar {product.name}', 'product': product})

@login_required
def manager_settings(request):
    if not user_can_manage_store(request):
        return redirect('index')
    
    tenant = request.tenant

    from .forms import StoreSettingsForm

    if request.method == 'POST':
        form = StoreSettingsForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            form.save()
            return redirect('manager_settings')
    else:
        form = StoreSettingsForm(instance=tenant)

    return render(request, 'core/manager/settings.html', {'form': form})

@require_POST
@login_required
def toggle_delivery_view(request):
    if not user_can_manage_store(request):
        return HttpResponse(status=403)
    store = request.tenant
    store.delivery_enabled = not store.delivery_enabled
    store.save(update_fields=['delivery_enabled'])
    logger.info('Store %s delivery_enabled set to %s by user %s', store.id, store.delivery_enabled, request.user)
    return render(request, 'core/manager/partials/delivery_toggle.html', {'delivery_enabled': store.delivery_enabled})


def cancel_order_on_pix_expiry(order_id):
    """Cancela pedido PENDING quando PIX expira no MercadoPago (chamado pelo webhook)."""
    try:
        order = Order.objects.get(id=order_id)
        if order.status == Order.Status.PENDING:
            order.status = Order.Status.CANCELED
            order.save()
    except Order.DoesNotExist:
        pass


@require_POST
@login_required
def update_order_status(request, order_id):
    import logging
    import mercadopago
    from django.conf import settings

    logger = logging.getLogger(__name__)

    if not user_can_manage_store(request):
        return HttpResponse(status=403)

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')

    if new_status not in Order.Status.values:
        return render(request, 'core/manager/partials/order_row.html', {'order': order})

    previous_status = order.status
    order.status = new_status
    order.save()

    # Estorno/cancelamento automático no MercadoPago ao cancelar pedido com PIX
    if new_status == Order.Status.CANCELED and previous_status != Order.Status.CANCELED and order.mp_payment_id:
        token = order.store.mercadopago_access_token or settings.MERCADOPAGO_ACCESS_TOKEN
        sdk = mercadopago.SDK(token)
        try:
            if previous_status == Order.Status.PENDING:
                sdk.payment().update(order.mp_payment_id, {"status": "cancelled"})
            else:
                sdk.payment().refund(order.mp_payment_id)
        except Exception as e:
            logger.error("MP refund/cancel failed for order %s: %s", order.id, e)

    return render(request, 'core/manager/partials/order_row.html', {'order': order})

def order_track(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/order_track.html', {'order': order})


@login_required
def order_print(request, order_id):
    if not user_can_manage_store(request):
        return HttpResponse(status=403)
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/manager/order_print.html', {'order': order})

@login_required
def comanda_list(request):
    if not user_can_manage_store(request):
        return redirect('index')
    comandas = Order.objects.filter(status='OPEN').order_by('-created_at')
    return render(request, 'core/manager/comanda_list.html', {'comandas': comandas})


@login_required
def comanda_create(request):
    if not user_can_manage_store(request):
        return redirect('index')
    if request.method == 'POST':
        table_label = request.POST.get('table_label', '').strip()
        if not table_label:
            return render(request, 'core/manager/comanda_list.html', {
                'comandas': Order.objects.filter(status='OPEN').order_by('-created_at'),
                'error': 'O identificador da comanda não pode ser vazio.',
            })
        order = Order.objects.create(
            status='OPEN',
            table_label=table_label,
            customer_name=table_label,
            customer_phone='',
            delivery_address=table_label,
            total_amount=Decimal('0.00'),
        )
        return redirect('comanda_detail', comanda_id=order.id)
    return redirect('comanda_list')


@login_required
def comanda_detail(request, comanda_id):
    if not user_can_manage_store(request):
        return redirect('index')
    order = get_object_or_404(Order, id=comanda_id, status='OPEN')
    products = Product.objects.filter(is_available=True).order_by('category__name', 'name')
    return render(request, 'core/manager/comanda_detail.html', {
        'order': order,
        'products': products,
        'pix_data': None,
    })


@require_POST
@login_required
def comanda_add_item(request, comanda_id):
    if not user_can_manage_store(request):
        return HttpResponse(status=403)
    order = get_object_or_404(Order, id=comanda_id, status='OPEN')
    try:
        product_id = int(request.POST.get('product_id'))
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except (TypeError, ValueError):
        return render(request, 'core/manager/_comanda_items.html', {'order': order})
    product = get_object_or_404(Product, id=product_id)
    OrderItem.objects.create(order=order, product=product, quantity=quantity, unit_price=product.price)
    order.total_amount = sum(i.quantity * i.unit_price for i in order.items.all())
    order.save()
    return render(request, 'core/manager/_comanda_items.html', {'order': order})


@require_POST
@login_required
def comanda_remove_item(request, comanda_id, item_id):
    if not user_can_manage_store(request):
        return HttpResponse(status=403)
    order = get_object_or_404(Order, id=comanda_id, status='OPEN')
    order.items.filter(id=item_id).delete()
    order.total_amount = sum(i.quantity * i.unit_price for i in order.items.all())
    order.save()
    return render(request, 'core/manager/_comanda_items.html', {'order': order})


@require_POST
@login_required
def comanda_close(request, comanda_id):
    if not user_can_manage_store(request):
        return HttpResponse(status=403)
    order = get_object_or_404(Order, id=comanda_id, status='OPEN')
    payment_method = request.POST.get('payment_method')
    products = Product.objects.filter(is_available=True).order_by('category__name', 'name')

    if payment_method == 'presencial':
        order.status = Order.Status.PREPARING
        order.save()
        return redirect('manager_orders')

    if payment_method == 'pix':
        if order.total_amount <= 0:
            return render(request, 'core/manager/comanda_detail.html', {
                'order': order,
                'products': products,
                'pix_data': None,
                'error_msg': 'Adicione ao menos um item antes de fechar via PIX.',
            })
        from .payment import create_pix_payment
        pix_data = create_pix_payment(order)
        order.status = Order.Status.PENDING
        order.save()
        return render(request, 'core/manager/comanda_detail.html', {
            'order': order,
            'products': products,
            'pix_data': pix_data,
        })

    return redirect('comanda_detail', comanda_id=order.id)


@login_required
def manager_create_order(request):
    if not user_can_manage_store(request):
        return HttpResponse(status=403)
        
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        
        # Parse quantities from POST data
        items_to_add = []
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                try:
                    qty = int(value)
                    if qty > 0:
                        product_id = int(key.split('_')[1])
                        items_to_add.append({'product_id': product_id, 'quantity': qty})
                except (ValueError, IndexError):
                    continue
        
        if customer_name and items_to_add:
            with transaction.atomic():
                order = Order.objects.create(
                    customer_name=customer_name,
                    customer_phone="",
                    delivery_address="Balcão / Retirada",
                    status=Order.Status.PREPARING,
                    total_amount=0,
                    delivery_fee=Decimal('0.00'),
                )
                
                total = 0
                # Fetch only needed products
                product_ids = [item['product_id'] for item in items_to_add]
                products = Product.objects.filter(id__in=product_ids)
                product_map = {p.id: p for p in products}
                
                for item in items_to_add:
                    product = product_map.get(item['product_id'])
                    if product:
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=item['quantity'],
                            unit_price=product.price
                        )
                        total += product.price * item['quantity']
                
                order.total_amount = total
                order.save()
                
            return redirect('dashboard')

    products = Product.objects.filter(is_available=True).select_related('category')
    categories = Category.objects.all()
    return render(request, 'core/manager_create_order.html', {
        'products': products,
        'categories': categories
    })




@login_required
@require_POST
def set_theme(request):
    """
    Persiste a preferência de tema do usuário autenticado.

    Valida `theme` contra as choices de UserSettings.Theme; grava via
    get_or_create. Resposta sem corpo (204): a troca visual já ocorreu no
    cliente, este POST só persiste. Idempotente.
    """
    theme = request.POST.get('theme')
    valid = {choice.value for choice in UserSettings.Theme}
    if theme not in valid:
        return HttpResponseBadRequest('tema inválido')

    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    settings_obj.theme = theme
    settings_obj.save(update_fields=['theme', 'updated_at'])
    return HttpResponse(status=204)
