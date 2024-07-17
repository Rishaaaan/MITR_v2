from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.apps import apps
from celery import Celery
from celery.schedules import crontab

app = Celery('MITR_v2')

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    beat_schedule={
        'check-overdue-tasks-every-day': {
            'task': 'MITR_app.tasks.check_overdue_tasks',
            'schedule': crontab(hour=0, minute=0),  # Every day at midnight
        },
        'send-reminder-emails': {
            'task': 'MITR_app.tasks.send_reminder_email',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes
            'args': (1,),  # Example task_id argument; update as needed
        },
    },
)

app.autodiscover_tasks(['MITR_app'])
# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MITR_v2.settings')

app = Celery('MITR_v2')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
# should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

from MITR_app import tasks

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
