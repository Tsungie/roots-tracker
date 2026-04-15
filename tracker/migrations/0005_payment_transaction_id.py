from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0004_delete_dashboard'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=100,
                help_text='Bank reference, EcoCash transaction ID, or receipt number',
            ),
        ),
    ]
