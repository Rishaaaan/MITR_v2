from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task
from .views import plot_employee_progress  # Import the function from views.py

@receiver(post_save, sender=Task)
def update_employee_progress(sender, instance, **kwargs):
    plot_employee_progress(instance.employee.id)