from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='mp_preference_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=255),
        ),
    ]
