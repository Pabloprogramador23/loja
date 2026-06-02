from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_order_payment_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='uber_quote_id',
        ),
        migrations.DeleteModel(
            name='UberDirectDeliveryEvent',
        ),
        migrations.DeleteModel(
            name='UberDirectDelivery',
        ),
        migrations.DeleteModel(
            name='UberDirectConfig',
        ),
    ]
