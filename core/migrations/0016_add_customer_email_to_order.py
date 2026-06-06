from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_remove_uber_direct'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='customer_email',
            field=models.CharField(blank=True, default='', max_length=254),
        ),
    ]
