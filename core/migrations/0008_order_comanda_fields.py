from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_store_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='table_label',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
