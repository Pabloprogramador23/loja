from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Store
from core.utils import set_current_tenant, reset_current_tenant


class AuthModalViewTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Modal Store", subdomain="modal-store", is_active=True)
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'modal-store'}

    def test_unauthenticated_sees_modal(self):
        response = self.client.get(reverse('auth_modal'), **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Identificação')

    def test_authenticated_redirects_to_checkout(self):
        user = User.objects.create_user(username='u1', email='u1@test.com', password='pass123')
        self.client.login(username='u1', password='pass123')
        response = self.client.get(reverse('auth_modal'), **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'window.location.href')
        self.assertContains(response, '/checkout/')


class CheckoutSignupViewTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Signup Store", subdomain="signup-store", is_active=True)
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'signup-store'}

    def test_valid_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('checkout_signup'), {
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao@test.com',
            'phone': '85999990000',
            'password1': 'SenhaForte@123',
            'password2': 'SenhaForte@123',
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'window.location.href')
        user = User.objects.get(email='joao@test.com')
        self.assertEqual(user.first_name, 'João')
        self.assertEqual(user.last_name, 'Silva')

    def test_signup_saves_phone_to_profile(self):
        self.client.post(reverse('checkout_signup'), {
            'first_name': 'Maria',
            'last_name': 'Lima',
            'email': 'maria@test.com',
            'phone': '85911112222',
            'password1': 'SenhaForte@123',
            'password2': 'SenhaForte@123',
        }, **self.headers)
        from core.models import UserProfile
        user = User.objects.get(email='maria@test.com')
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.phone, '85911112222')

    def test_duplicate_email_returns_error(self):
        User.objects.create_user(username='existing', email='dup@test.com', password='pass123')
        response = self.client.post(reverse('checkout_signup'), {
            'first_name': 'Dup',
            'last_name': 'User',
            'email': 'dup@test.com',
            'phone': '',
            'password1': 'SenhaForte@123',
            'password2': 'SenhaForte@123',
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'window.location.href')


class CheckoutLoginViewTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Login Store", subdomain="login-store", is_active=True)
        self.headers = {'HTTP_X_TENANT_SUBDOMAIN': 'login-store'}
        self.user = User.objects.create_user(
            username='loginuser', email='login@test.com', password='SenhaForte@123'
        )

    def test_valid_credentials_login_and_redirect(self):
        response = self.client.post(reverse('checkout_login'), {
            'email': 'login@test.com',
            'password': 'SenhaForte@123',
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'window.location.href')

    def test_invalid_credentials_return_error(self):
        response = self.client.post(reverse('checkout_login'), {
            'email': 'login@test.com',
            'password': 'senhaerrada',
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'window.location.href')
        self.assertContains(response, 'incorretos')
