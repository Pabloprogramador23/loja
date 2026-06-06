from django.db import models
from .utils import get_current_tenant
from decimal import Decimal
from django.core.validators import MinValueValidator

class TenantManager(models.Manager):
    """
    Manager para filtrar automaticamente queries pelo tenant (loja) atual.
    """
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return super().get_queryset().filter(store=tenant)
        return super().get_queryset()

class Store(models.Model):
    """
    Modelo representando um Tenant (Loja).
    """
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='store_logos/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='store_covers/', null=True, blank=True)
    mercadopago_access_token = models.CharField(max_length=255, blank=True, null=True, help_text="Token de acesso do MercadoPago para esta loja")
    delivery_fee = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Taxa de entrega cobrada nos pedidos online. 0,00 = entrega gratuita."
    )
    free_delivery_threshold = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True, default=None,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Pedidos com subtotal >= este valor ganham entrega gratuita. Nulo = recurso desativado."
    )
    delivery_enabled = models.BooleanField(
        default=True,
        help_text="Quando False, a loja não aceita novos pedidos online."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.OneToOneField(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_store',
    )

    def __str__(self):
        return self.name

class TenantAwareModel(models.Model):
    """
    Classe base abstrata para todos os modelos que precisam ser isolados por tenant.
    """
    store = models.ForeignKey(
        Store, 
        on_delete=models.CASCADE, 
        related_name="%(class)s_related"
    )

    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Define automaticamente a loja se não fornecida
        if not self.store_id:
            tenant = get_current_tenant()
            if tenant:
                self.store = tenant
        super().save(*args, **kwargs)

class Category(TenantAwareModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(TenantAwareModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Order(TenantAwareModel):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Comanda Aberta'
        PENDING = 'PENDING', 'Pendente'
        CONFIRMED = 'CONFIRMED', 'Confirmado'
        PREPARING = 'PREPARING', 'Preparando'
        DELIVERING = 'DELIVERING', 'Em trânsito'
        COMPLETED = 'COMPLETED', 'Concluído'
        CANCELED = 'CANCELED', 'Cancelado'

    class PaymentMethod(models.TextChoices):
        ONLINE = 'online', 'Online (MP)'
        CASH = 'cash', 'Dinheiro'
        CARD = 'card', 'Cartão na Maquininha'

    class CardType(models.TextChoices):
        CREDIT = 'credit', 'Crédito'
        DEBIT = 'debit', 'Débito'

    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.CharField(max_length=254, blank=True, default='')
    delivery_address = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.ONLINE,
    )
    change_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text='Troco solicitado quando payment_method=cash. None = sem troco.',
    )
    card_type = models.CharField(
        max_length=10,
        choices=CardType.choices,
        blank=True, default='',
        help_text='Tipo de cartão quando payment_method=card.',
    )
    mp_payment_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )
    mp_preference_id = models.CharField(max_length=255, blank=True, default='', db_index=True)
    table_label = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.customer_name}"

class OrderItem(TenantAwareModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.quantity}x {self.product.name} no Pedido #{self.order.id}"

class Address(TenantAwareModel):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    complement = models.CharField(max_length=255, blank=True)
    neighborhood = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=20)
    
    def save(self, *args, **kwargs):
        # Limita a máx 3 endereços por (user + store)
        # Nota: TenantAwareModel define self.store automaticamente
        is_new = self.pk is None
        if is_new:
            # Precisamos definir a loja primeiro para filtrar corretamente
            if not self.store_id:
                tenant = get_current_tenant()
                if tenant:
                    self.store = tenant

            if self.store:
                count = Address.objects.filter(user=self.user, store=self.store).count()
                if count >= 3:
                     # Requisito: opção de salvar até 3. Bloqueia o 4º.
                     from django.core.exceptions import ValidationError
                     raise ValidationError("Limite de 3 endereços atingido.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}"

class UserProfile(models.Model):
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='profile',
    )
    phone = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return f"Perfil de {self.user.username}"


class UserSettings(models.Model):
    """
    Preferências de apresentação por usuário (ex.: tema da interface).
    NÃO é TenantAwareModel: a preferência é global por usuário, não por loja.
    """
    class Theme(models.TextChoices):
        SYSTEM = 'system', 'Sistema'
        LIGHT = 'light', 'Claro'
        DARK = 'dark', 'Escuro'

    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='settings',
    )
    theme = models.CharField(
        max_length=10,
        choices=Theme.choices,
        default=Theme.SYSTEM,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings de {self.user} (tema: {self.theme})"
