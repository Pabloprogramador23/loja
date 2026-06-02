from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

RESERVED_SUBDOMAINS = {
    'www', 'api', 'admin', 'mail', 'smtp', 'ftp',
    'catalog', 'checkout', 'cart', 'dashboard',
    'account', 'order', 'orders', 'static', 'media',
}

subdomain_validator = RegexValidator(
    regex=r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$',
    message='Use apenas letras minúsculas, números e hífens. Não pode começar ou terminar com hífen.',
)


class CustomerSignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='E-mail',
        help_text='Usado para receber o QR Code PIX após o pedido.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CheckoutSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label='Nome')
    last_name = forms.CharField(max_length=150, required=True, label='Sobrenome')
    email = forms.EmailField(required=True, label='E-mail')
    phone = forms.CharField(max_length=20, required=False, label='Celular')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        # username gerado a partir do email
        base = self.cleaned_data['email'].split('@')[0]
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{counter}'
            counter += 1
        user.username = username
        if commit:
            user.save()
        return user


class StoreRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='E-mail',
    )
    store_name = forms.CharField(
        max_length=255,
        label='Nome da loja',
    )
    subdomain = forms.CharField(
        max_length=100,
        min_length=3,
        label='Subdomínio',
        validators=[subdomain_validator],
        help_text='Mínimo 3 caracteres. Apenas letras minúsculas, números e hífens.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'store_name', 'subdomain')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean_subdomain(self):
        from core.models import Store
        subdomain = self.cleaned_data.get('subdomain', '').lower().strip()
        if subdomain in RESERVED_SUBDOMAINS:
            raise forms.ValidationError('Subdomínio reservado. Escolha outro nome.')
        if Store.objects.filter(subdomain=subdomain).exists():
            raise forms.ValidationError('Este subdomínio já está em uso.')
        return subdomain
