# Generated by Django 5.0.4 on 2024-10-17 06:57

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=250, unique=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='slug',
            field=models.SlugField(max_length=250, unique=True),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=250)),
                ('type', models.CharField(choices=[('WEBSITE', 'Website'), ('API', 'API')], default='WEBSITE', max_length=20)),
                ('url', models.URLField(blank=True, max_length=500)),
                ('check_interval', models.PositiveIntegerField(default=5, help_text='Check interval in minutes')),
                ('additional_data', models.JSONField(blank=True, help_text='Additional data for service checks (e.g., auth headers, connection strings)', null=True)),
                ('is_public', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='core.project')),
            ],
            options={
                'unique_together': {('project', 'name')},
            },
        ),
    ]