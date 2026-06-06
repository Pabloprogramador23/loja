from django.urls import path
from .saas_views import (
    SaasDashboardView,
    SaasStoreCreateView,
    SaasStoreDetailView,
    SaasStoreToggleView,
)

urlpatterns = [
    path('', SaasDashboardView.as_view(), name='saas_dashboard'),
    path('lojas/nova/', SaasStoreCreateView.as_view(), name='saas_store_create'),
    path('lojas/<int:pk>/', SaasStoreDetailView.as_view(), name='saas_store_detail'),
    path('lojas/<int:pk>/toggle/', SaasStoreToggleView.as_view(), name='saas_store_toggle'),
]
