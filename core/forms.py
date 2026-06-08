from django import forms
from django.contrib.auth.models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:shadow-outline-indigo focus:border-indigo-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5'}),
            'last_name': forms.TextInput(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:shadow-outline-indigo focus:border-indigo-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5'}),
            'email': forms.EmailInput(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:shadow-outline-indigo focus:border-indigo-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.email:
            self.fields['email'].help_text = "Para alterar seu e-mail, entre em contato com o suporte."

from .models import Product

class ProductForm(forms.ModelForm):
    new_category_name = forms.CharField(
        max_length=255,
        required=False,
        label='Nova categoria',
        help_text='Preencha para criar e usar uma nova categoria. Deixe em branco para usar a seleção acima.',
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'placeholder': 'Ex: Sobremesas'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_name = cleaned_data.get('new_category_name', '').strip()
        if not category and not new_name:
            raise forms.ValidationError('Selecione uma categoria existente ou preencha o campo "Nova categoria".')
        return cleaned_data

    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'description', 'image', 'is_available']
        labels = {
            'name': 'Nome do Produto',
            'category': 'Categoria',
            'price': 'Preço (R$)',
            'description': 'Descrição',
            'image': 'Imagem',
            'is_available': 'Disponível no Cardápio?'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'category': forms.Select(attrs={'class': 'mt-1 block w-full bg-white border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 pl-10 pr-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded'}),
            'image': forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
        }

from .models import Store

INPUT_CLASS = 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400'
PASSWORD_INPUT_CLASS = INPUT_CLASS


class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'logo', 'cover_image', 'mercadopago_access_token', 'delivery_fee', 'free_delivery_threshold', 'delivery_enabled', 'payment_online_enabled', 'payment_cash_enabled', 'payment_card_enabled']
        labels = {
            'name': 'Nome da Loja',
            'logo': 'Logotipo',
            'cover_image': 'Imagem de Capa',
            'mercadopago_access_token': 'Token de Acesso (Mercado Pago)',
            'delivery_fee': 'Taxa de entrega (R$)',
            'free_delivery_threshold': 'Entrega grátis acima de (R$)',
            'delivery_enabled': 'Aceitar pedidos online',
            'payment_online_enabled': 'Aceitar MercadoPago (PIX/Checkout Pro)',
            'payment_cash_enabled': 'Aceitar Dinheiro na entrega',
            'payment_card_enabled': 'Aceitar Cartão na maquininha',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400'}),
            'mercadopago_access_token': forms.TextInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400', 'placeholder': 'TEST-...'}),
            'logo': forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'cover_image': forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'delivery_fee': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400'}),
            'free_delivery_threshold': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400', 'id': 'id_free_delivery_threshold'}),
            'delivery_enabled': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700'}),
            'payment_online_enabled': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700'}),
            'payment_cash_enabled': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700'}),
            'payment_card_enabled': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700'}),
        }

    def clean_free_delivery_threshold(self):
        value = self.cleaned_data.get('free_delivery_threshold')
        if value == '' or value is None:
            return None
        return value


class SaasCreateStoreForm(forms.Form):
    store_name = forms.CharField(
        max_length=255,
        label='Nome da loja',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: Pizza do João'}),
    )
    subdomain = forms.SlugField(
        max_length=255,
        label='Subdomínio',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: pizzadojoao'}),
        help_text='Apenas letras minúsculas, números e hífens. Sem espaços.',
    )
    manager_email = forms.EmailField(
        label='E-mail do gerente',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'gerente@email.com'}),
    )
    manager_password = forms.CharField(
        label='Senha do gerente',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        min_length=8,
    )

    def clean_subdomain(self):
        subdomain = self.cleaned_data['subdomain']
        if Store.objects.filter(subdomain=subdomain).exists():
            raise forms.ValidationError('Este subdomínio já está em uso.')
        return subdomain

    def clean_manager_email(self):
        from django.contrib.auth.models import User
        email = self.cleaned_data['manager_email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self):
        from django.contrib.auth.models import User
        from django.db import transaction

        email = self.cleaned_data['manager_email']
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{counter}'
            counter += 1

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=self.cleaned_data['manager_password'],
                is_staff=True,
            )
            store = Store.objects.create(
                name=self.cleaned_data['store_name'],
                subdomain=self.cleaned_data['subdomain'],
                owner=user,
                is_active=True,
            )
        return store
