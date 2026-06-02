from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_store_delivery_fee_order_delivery_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='uber_quote_id',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.CreateModel(
            name='UberDirectConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uber_store_id', models.CharField(help_text='Store ID fornecido pela Uber', max_length=255)),
                ('client_id', models.CharField(blank=True, max_length=255)),
                ('client_secret', models.CharField(blank=True, max_length=255)),
                ('webhook_signing_key', models.CharField(blank=True, max_length=255)),
                ('pickup_address', models.CharField(blank=True, help_text='Endereço físico do restaurante para criação da corrida', max_length=512)),
                ('pickup_phone', models.CharField(blank=True, help_text='Telefone do restaurante no formato +5511999998888', max_length=20)),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('store', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='uber_config', to='core.store')),
            ],
        ),
        migrations.CreateModel(
            name='UberDirectDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uberdirectdelivery_related', to='core.store')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='uber_delivery', to='core.order')),
                ('uber_delivery_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('uber_quote_id', models.CharField(blank=True, max_length=255)),
                ('fee', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('status', models.CharField(
                    choices=[
                        ('PENDING', 'Pendente'),
                        ('SCHEDULED', 'Agendado'),
                        ('EN_ROUTE_TO_PICKUP', 'A caminho da coleta'),
                        ('ARRIVED_AT_PICKUP', 'No restaurante'),
                        ('EN_ROUTE_TO_DROPOFF', 'A caminho do cliente'),
                        ('ARRIVED_AT_DROPOFF', 'No endereço do cliente'),
                        ('COMPLETED', 'Entregue'),
                        ('FAILED', 'Falhou'),
                        ('CANCELED', 'Cancelado'),
                        ('RETURNED', 'Devolvido'),
                    ],
                    default='PENDING',
                    max_length=50,
                )),
                ('tracking_url', models.URLField(blank=True, max_length=512, null=True)),
                ('dropoff_address', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UberDirectDeliveryEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='core.uberdirectdelivery')),
                ('event_type', models.CharField(max_length=100)),
                ('status_from', models.CharField(blank=True, max_length=50)),
                ('status_to', models.CharField(max_length=50)),
                ('raw_payload', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
