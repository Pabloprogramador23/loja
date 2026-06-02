"""
Testes para a feature 011-D: localização pré-catálogo.
"""
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Category, Product, Store


class SaveLocationTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(
            name='Loc Store', subdomain='loc-store', is_active=True,
        )
        self.client = Client()
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'loc-store'}

    def test_post_saves_address_to_session(self):
        response = self.client.post(
            reverse('save_location'),
            {'delivery_address': 'Rua das Flores, 42'},
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.session.get('session_delivery_address'),
            'Rua das Flores, 42',
        )

    def test_post_empty_address_saves_empty_string(self):
        self.client.post(
            reverse('save_location'),
            {'delivery_address': ''},
            **self.headers,
        )
        self.assertEqual(self.client.session.get('session_delivery_address'), '')

    def test_post_long_address_is_truncated(self):
        long_address = 'A' * 600
        self.client.post(
            reverse('save_location'),
            {'delivery_address': long_address},
            **self.headers,
        )
        saved = self.client.session.get('session_delivery_address', '')
        self.assertLessEqual(len(saved), 500)

    def test_get_not_allowed(self):
        response = self.client.get(reverse('save_location'), **self.headers)
        self.assertEqual(response.status_code, 405)

    def test_post_overwrites_previous_address(self):
        self.client.post(
            reverse('save_location'),
            {'delivery_address': 'Endereço Antigo'},
            **self.headers,
        )
        self.client.post(
            reverse('save_location'),
            {'delivery_address': 'Endereço Novo'},
            **self.headers,
        )
        self.assertEqual(
            self.client.session.get('session_delivery_address'),
            'Endereço Novo',
        )


class CatalogLocationContextTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(
            name='Cat Loc Store', subdomain='cat-loc-store', is_active=True,
        )
        self.category = Category.objects.create(name='Cat', store=self.store)
        Product.objects.create(
            name='Item', category=self.category, price=10, store=self.store, is_available=True,
        )
        self.client = Client()
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'cat-loc-store'}

    def test_catalog_context_has_empty_address_by_default(self):
        response = self.client.get(reverse('catalog'), **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('session_delivery_address', ''), '')

    def test_catalog_context_reflects_session_address(self):
        session = self.client.session
        session['session_delivery_address'] = 'Av. Paulista, 1000'
        session.save()
        response = self.client.get(reverse('catalog'), **self.headers)
        self.assertEqual(response.context['session_delivery_address'], 'Av. Paulista, 1000')
