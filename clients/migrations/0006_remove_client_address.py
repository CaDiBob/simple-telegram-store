# Generated by Django 4.0 on 2023-03-07 17:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0005_client_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client',
            name='address',
        ),
    ]
