# Generated by Django 5.0.4 on 2025-05-14 00:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='detalleasiento',
            name='descripcion',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='detalleasiento',
            name='fecha',
            field=models.DateField(blank=True, null=True),
        ),
    ]
