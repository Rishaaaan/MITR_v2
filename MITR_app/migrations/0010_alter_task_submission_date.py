# Generated by Django 4.2.4 on 2024-08-06 20:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MITR_app', '0009_alter_task_submission_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='submission_date',
            field=models.DateField(default=datetime.datetime(2024, 8, 7, 2, 28, 11, 497819)),
        ),
    ]
