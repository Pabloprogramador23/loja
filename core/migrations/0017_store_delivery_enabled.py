from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_customer_email_to_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='delivery_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Quando False, a loja não aceita novos pedidos online.'
            ),
        ),
    ]
