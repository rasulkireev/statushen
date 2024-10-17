# Generated by Django 5.0.4 on 2024-10-17 08:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_servicestatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilestatetransition',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='state_transitions', to='core.profile'),
        ),
    ]