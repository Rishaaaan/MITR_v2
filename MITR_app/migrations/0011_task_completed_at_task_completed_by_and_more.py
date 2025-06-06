# Generated by Django 4.2.4 on 2024-08-07 20:45

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('MITR_app', '0010_alter_task_submission_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='completed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_tasks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='task',
            name='client_phone_number',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='task',
            name='submission_date',
            field=models.DateField(default=datetime.datetime(2024, 8, 8, 2, 15, 44, 217340)),
        ),
    ]
