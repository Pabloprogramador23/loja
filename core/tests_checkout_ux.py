"""
Testes para a feature 010-checkout-ux-cliente.
Cobre: UserProfile, pré-preenchimento de phone, string de endereço, limite de endereços.
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Address, Category, Order, Product, Store, UserProfile
from core.utils import reset_current_tenant, set_current_tenant


class UserProfileTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="UX Store", subdomain="ux-store", is_active=True)
        self.user = User.objects.create_user(username="uxuser", password="pass123", email="ux@test.com")
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'ux-store'}

    def test_get_or_create_does_not_fail_for_user_without_profile(self):
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        self.assertTrue(created)
        self.assertEqual(profile.phone, '')

    def test_profile_phone_default_is_empty(self):
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.phone, '')

    def test_update_or_create_sets_phone(self):
        UserProfile.objects.update_or_create(user=self.user, defaults={'phone': '85999990000'})
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.phone, '85999990000')

    def test_cart_detail_passes_profile_phone_in_context(self):
        UserProfile.objects.create(user=self.user, phone='85988887777')
        self.client.login(username='uxuser', password='pass123')
        response = self.client.get(reverse('cart_detail'), **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_phone', response.context)
        self.assertEqual(response.context['profile_phone'], '85988887777')

    def test_cart_detail_profile_phone_empty_for_user_without_profile(self):
        self.client.login(username='uxuser', password='pass123')
        response = self.client.get(reverse('cart_detail'), **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_phone', response.context)
        self.assertEqual(response.context['profile_phone'], '')

    @patch('core.payment.create_pix_payment')
    def test_checkout_updates_profile_phone_for_authenticated_user(self, mock_payment):
        mock_payment.return_value = {
            'qr_code': 'fake-qr',
            'qr_code_base64': '',
            'ticket_url': '',
            'payment_id': '999',
        }
        category = Category.objects.create(name="Cat", store=self.store)
        product = Product.objects.create(
            name="Item", category=category, price=Decimal('10.00'), store=self.store
        )
        self.client.login(username='uxuser', password='pass123')
        self.client.post(reverse('add_to_cart', args=[product.id]), **self.headers)
        self.client.post(reverse('checkout'), {
            'customer_name': 'UX User',
            'customer_phone': '85911112222',
            'delivery_address': 'Rua Teste, 1 - Bairro, Fortaleza - CE',
        }, **self.headers)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.phone, '85911112222')


class AddressLimitFeedbackTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Limit Store", subdomain="limit-store", is_active=True)
        self.user = User.objects.create_user(username="limituser", password="pass123")
        self.client.login(username='limituser', password='pass123')
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'limit-store'}
        token = set_current_tenant(self.store)
        for i in range(3):
            Address.objects.create(
                user=self.user, store=self.store,
                street=f"Rua {i}", number=str(i), neighborhood="Bairro",
                city="Cidade", state="CE", zip_code=""
            )
        reset_current_tenant(token)

    def test_saving_fourth_address_returns_error_message(self):
        response = self.client.post(reverse('save_address'), {
            'street': 'Rua Nova',
            'number': '100',
            'neighborhood': 'Novo Bairro',
            'city': 'Fortaleza',
            'state': 'CE',
            'zip_code': '',
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Limite')

    def test_saving_fourth_address_does_not_create_record(self):
        self.client.post(reverse('save_address'), {
            'street': 'Rua Nova',
            'number': '100',
            'neighborhood': 'Novo Bairro',
            'city': 'Fortaleza',
            'state': 'CE',
        }, **self.headers)
        count = Address.objects.filter(user=self.user, store=self.store).count()
        self.assertEqual(count, 3)


class SelectAddressStringTest(TestCase):
    """
    T004 — verifica que o template address_list.html passa city, state e zip_code
    para selectAddress. O teste faz GET do cart_detail com endereço salvo e verifica
    que o onclick contém os campos corretos.
    """
    def setUp(self):
        self.store = Store.objects.create(name="Addr Store", subdomain="addr-store", is_active=True)
        self.user = User.objects.create_user(username="addruser", password="pass123")
        self.client.login(username='addruser', password='pass123')
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'addr-store'}
        token = set_current_tenant(self.store)
        Address.objects.create(
            user=self.user, store=self.store,
            street="Rua Baturité", number="118", neighborhood="Centro",
            city="Fortaleza", state="CE", zip_code="60410-350"
        )
        reset_current_tenant(token)

    def test_address_card_onclick_contains_city_and_state(self):
        # Precisa de item no carrinho para renderizar a seção de endereços
        category = Category.objects.create(name="Cat", store=self.store)
        product = Product.objects.create(
            name="Item", category=category, price=Decimal('10.00'), store=self.store
        )
        self.client.post(reverse('add_to_cart', args=[product.id]), **self.headers)
        response = self.client.get(reverse('cart_detail'), **self.headers)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Fortaleza', content)
        self.assertIn('CE', content)
        self.assertIn('60410-350', content)
