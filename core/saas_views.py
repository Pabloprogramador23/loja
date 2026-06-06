from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .forms import SaasCreateStoreForm
from .models import Order, Store
from .utils import set_current_tenant


class SuperuserRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        if not request.user.is_superuser:
            return redirect('/dashboard/')
        # Zera o tenant no ContextVar — TenantManager retorna queryset global
        set_current_tenant(None)
        return super().dispatch(request, *args, **kwargs)


class SaasDashboardView(SuperuserRequiredMixin, View):
    def get(self, request):
        today = timezone.localdate()
        stores = (
            Store.objects
            .annotate(
                total_orders=Count('order_related'),
                orders_today=Count(
                    'order_related',
                    filter=Q(order_related__created_at__date=today),
                ),
            )
            .select_related('owner')
            .order_by('name')
        )
        active_count = Store.objects.filter(is_active=True).count()
        inactive_count = Store.objects.filter(is_active=False).count()
        return render(request, 'core/saas/dashboard.html', {
            'stores': stores,
            'active_count': active_count,
            'inactive_count': inactive_count,
        })


class SaasStoreToggleView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        store = get_object_or_404(Store, pk=pk)
        if store.owner_id and store.owner_id == request.user.pk:
            return HttpResponse('Não é possível alterar o status da sua própria loja.', status=403)
        store.is_active = not store.is_active
        store.save(update_fields=['is_active'])
        return render(request, 'core/saas/partials/store_toggle.html', {'store': store})


class SaasStoreCreateView(SuperuserRequiredMixin, View):
    def get(self, request):
        return render(request, 'core/saas/store_create.html', {'form': SaasCreateStoreForm()})

    def post(self, request):
        form = SaasCreateStoreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Loja "{form.cleaned_data["store_name"]}" criada com sucesso.')
            return redirect('saas_dashboard')
        return render(request, 'core/saas/store_create.html', {'form': form})


class SaasStoreDetailView(SuperuserRequiredMixin, View):
    def get(self, request, pk):
        store = get_object_or_404(Store, pk=pk)
        orders = Order.objects.filter(store=store).order_by('-created_at')[:10]
        token = store.mercadopago_access_token or ''
        masked_token = f'****{token[-6:]}' if len(token) >= 6 else ('****' if token else '—')
        return render(request, 'core/saas/store_detail.html', {
            'store': store,
            'orders': orders,
            'masked_token': masked_token,
        })
