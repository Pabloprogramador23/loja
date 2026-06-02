from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_order_mp_preference_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[('online', 'Online (MP)'), ('cash', 'Dinheiro'), ('card', 'Cartão na Maquininha')],
                default='online',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='change_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Troco solicitado quando payment_method=cash. None = sem troco.',
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='card_type',
            field=models.CharField(
                blank=True,
                choices=[('credit', 'Crédito'), ('debit', 'Débito')],
                default='',
                help_text='Tipo de cartão quando payment_method=card.',
                max_length=10,
            ),
        ),
    ]
