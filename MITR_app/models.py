from django.contrib.auth.models import AbstractUser, User
from django.db import models
from MITR_v2.settings import AUTH_USER_MODEL
from django.conf import settings
from datetime import timedelta, datetime
from django import forms
from django.core.mail import send_mail
from celery import shared_task
from django.utils import timezone
from .tasks import send_reminder_email
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import send_initial_email
import logging
import pytz

logger = logging.getLogger(__name__)


settings.AUTH_USER_MODEL


class CustomUser(AbstractUser):
    company = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_superuser = models.BooleanField(default=False)


    def __str__(self):
        return self.username  # You can choose any field as a string representation
    
    def is_employee(self):
        return hasattr(self, 'employee')


class Task(models.Model):
    REMIND_CHOICES = (
        ('', '---------'),
        (timedelta(hours=1), '1 Hour'),
        (timedelta(hours=2), '2 Hours'),
        (timedelta(hours=3), '3 Hours'),
        (timedelta(hours=4), '4 Hours'),
        (timedelta(hours=5), '5 Hours'),
        (timedelta(hours=6), '6 Hours'),
        (timedelta(hours=12), '12 Hours'),
        (timedelta(days=1), '1 Day'),
        (timedelta(days=2), '2 Days'),
        (timedelta(days=3), '3 Days'),
        (timedelta(days=7), '1 Week'),
        (timedelta(weeks=2), '2 Weeks'),
        (timedelta(weeks=3), '3 Weeks'),
        (timedelta(weeks=4), '1 Month'),
    )
    task_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,  # Prevent manual editing in forms/admin
        default=None,
        null=True,  # Allow null initially for pre-save generation
        blank=True
    )
    title = models.CharField(max_length=100)
    description = models.TextField()
    email = models.EmailField()
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, null=True, blank=True)
    remind_every = models.DurationField()
    submission_date = models.DateField(default=datetime.now())
    date_added = models.DateTimeField(default=timezone.now)
    completed = models.BooleanField(default=False)
    client_company = models.CharField(max_length=100,null=True)
    client_phone_number = models.IntegerField()
    employee_marked_completed = models.BooleanField(default=False)
    next_reminder_date = models.DateTimeField(default=timezone.now)
    completed_date = models.DateTimeField(null=True, blank=True)
    overdue_reason = models.CharField(max_length=5000, null=True, default=False)
    completed_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='completed_tasks')
    completed_at = models.DateTimeField(null=True, blank=True)
    rework_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='reworked_tasks')
    rework_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.next_reminder_date:
            self.next_reminder_date = timezone.now() + self.remind_every
        super().save(*args, **kwargs)
        if self.completed and not self.completed_date:
            self.completed_date = timezone.now().date()
            
        super(Task, self).save(*args, **kwargs)

    def complete_task(self, user):
        self.completed = True
        self.completed_by = user
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return self.title

    
    def send_task_email(self):
        subject = self.title
        message = f"""
        Task Title: {self.title}
        Description: {self.description}
        Submission Date: {self.submission_date}
        """
        send_mail(
            subject,
            message,
            'mitr.reminder@gmail.com',
            [self.employee.email],
            fail_silently=False,
        )
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.schedule_reminder_emails()

    def schedule_reminder_emails(self):
        if not self.completed:
            countdown = self.remind_every.total_seconds()
            send_reminder_email.apply_async((self.id,), countdown=countdown)    

class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    company = models.CharField(max_length=100, default='TO_BE_ASSIGNED')

    def __str__(self):
        return self.name
