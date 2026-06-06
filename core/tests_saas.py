from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import Order, Store


def make_superuser(**kwargs):
    return User.objects.create_superuser(
        username=kwargs.get('username', 'admin'),
        email=kwargs.get('email', 'admin@test.com'),
        password='testpass123',
    )


def make_staff(**kwargs):
    return User.objects.create_user(
        username=kwargs.get('username', 'staff'),
        email=kwargs.get('email', 'staff@test.com'),
        password='testpass123',
        is_staff=True,
    )


def make_store(name='Loja Teste', subdomain='lojateste', owner=None, is_active=True):
    return Store.objects.create(
        name=name,
        subdomain=subdomain,
        owner=owner,
        is_active=is_active,
    )


# ── T003: Proteção de rota ──────────────────────────────────────────────────

class SaasRouteProtectionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = make_superuser()
        self.staff = make_staff()
        # loja do superusuário (para o middleware dev fallback)
        self.store = make_store(owner=self.superuser, subdomain='adminsaas')

    def test_superuser_acessa_listagem(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/saas/')
        self.assertEqual(response.status_code, 200)

    def test_staff_sem_superuser_redireciona_para_dashboard(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.get('/saas/')
        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)

    def test_anonimo_redireciona_para_login(self):
        response = self.client.get('/saas/')
        self.assertRedirects(response, '/login/', fetch_redirect_response=False)

    def test_superuser_acessa_nova_loja(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/saas/lojas/nova/')
        self.assertEqual(response.status_code, 200)

    def test_staff_sem_superuser_bloqueado_em_nova_loja(self):
        self.client.login(username='staff', password='testpass123')
        response = self.client.get('/saas/lojas/nova/')
        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)


# ── T004: Métricas de listagem ──────────────────────────────────────────────

class SaasMetricsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = make_superuser()
        self.store_a = make_store(name='Loja A', subdomain='lojaa')
        self.store_b = make_store(name='Loja B', subdomain='lojab')

        for _ in range(3):
            Order.objects.create(
                store=self.store_a,
                customer_name='Cliente',
                customer_phone='11999999999',
                delivery_address='Rua X',
                total_amount='30.00',
            )
        Order.objects.create(
            store=self.store_b,
            customer_name='Cliente',
            customer_phone='11999999999',
            delivery_address='Rua Y',
            total_amount='50.00',
        )

    def test_contadores_de_lojas_no_contexto(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/saas/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_count', response.context)
        self.assertIn('inactive_count', response.context)

    def test_total_orders_por_loja(self):
        from django.db.models import Count
        from .models import Store
        stores = Store.objects.annotate(total_orders=Count('order_related'))
        store_a_ann = stores.get(pk=self.store_a.pk)
        store_b_ann = stores.get(pk=self.store_b.pk)
        self.assertEqual(store_a_ann.total_orders, 3)
        self.assertEqual(store_b_ann.total_orders, 1)

    def test_orders_today_usa_localdate(self):
        from django.db.models import Count, Q
        today = timezone.localdate()
        stores = Store.objects.annotate(
            orders_today=Count('order_related', filter=Q(order_related__created_at__date=today))
        )
        store_a_ann = stores.get(pk=self.store_a.pk)
        self.assertEqual(store_a_ann.orders_today, 3)


# ── T005: SaasCreateStoreForm ───────────────────────────────────────────────

class SaasCreateStoreFormTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = make_superuser()

    def test_criar_loja_com_dados_validos(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.post('/saas/lojas/nova/', {
            'store_name': 'Novo Burguer',
            'subdomain': 'novoburguer',
            'manager_email': 'gerente@novo.com',
            'manager_password': 'senha12345',
        })
        self.assertRedirects(response, '/saas/', fetch_redirect_response=False)
        self.assertTrue(Store.objects.filter(subdomain='novoburguer').exists())
        manager = User.objects.filter(email='gerente@novo.com').first()
        self.assertIsNotNone(manager)
        self.assertTrue(manager.is_staff)

    def test_subdominio_duplicado_falha(self):
        make_store(subdomain='existente')
        self.client.login(username='admin', password='testpass123')
        response = self.client.post('/saas/lojas/nova/', {
            'store_name': 'Outra Loja',
            'subdomain': 'existente',
            'manager_email': 'outro@email.com',
            'manager_password': 'senha12345',
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('subdomain', form.errors)

    def test_campos_obrigatorios_ausentes_falham(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.post('/saas/lojas/nova/', {})
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)


# ── T006: Toggle is_active ──────────────────────────────────────────────────

class SaasToggleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = make_superuser()
        self.own_store = make_store(owner=self.superuser, subdomain='adminstore')
        self.other_store = make_store(subdomain='outraloja', is_active=True)

    def test_toggle_desativa_loja(self):
        self.client.login(username='admin', password='testpass123')
        self.client.post(f'/saas/lojas/{self.other_store.pk}/toggle/')
        self.other_store.refresh_from_db()
        self.assertFalse(self.other_store.is_active)

    def test_toggle_reativa_loja(self):
        self.other_store.is_active = False
        self.other_store.save()
        self.client.login(username='admin', password='testpass123')
        self.client.post(f'/saas/lojas/{self.other_store.pk}/toggle/')
        self.other_store.refresh_from_db()
        self.assertTrue(self.other_store.is_active)

    def test_guard_propria_loja_bloqueado(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(f'/saas/lojas/{self.own_store.pk}/toggle/')
        self.assertEqual(response.status_code, 403)
        self.own_store.refresh_from_db()
        self.assertTrue(self.own_store.is_active)
