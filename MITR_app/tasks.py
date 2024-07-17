from celery import shared_task
from django.core.mail import send_mail
from datetime import timedelta, datetime
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task
def send_initial_email(task_id):
    from .models import Task, Employee
    try:
        task = Task.objects.get(id=task_id)
        send_mail(
            f"NEW TASK ALERT!",
            f"""
Dear {task.employee},
You've been assigned a new task. Details have been listed below 
Task Name:-{task.title}
Task Description:-{task.description}
Client Name: {task.client_company}
Client Email: {task.email}
due date: {task.submission_date}

Please ensure it's completed before the due date.
It's essential that we complete this task before the due date to ensure our commitment to delivering high-quality service to our clients.
Your prompt action and attention to detail are greatly appreciated.

Thank you.

Best regards,
Admin
            
            """,
            'mitr.taskreminder@gmail.com',
            [task.employee.email],
            fail_silently=False,
        )
        logger.info(f"Initial email sent for task {task_id}")
    except Exception as e:
        logger.error(f"Error sending initial email for task {task_id}: {e}")

@shared_task
def send_reminder_email(task_id):
    from .models import Task, Employee
    try:
        task = Task.objects.get(id=task_id)
        current_time = timezone.now()

        if current_time >= task.next_reminder_date and not task.completed:
            send_mail(
                f"Reminder: {task.title}",
                f"""
Dear {task.employee},

Just a reminder about the task assigned to you.

Task Name: {task.title}
Task Description: {task.description}
Client Name: {task.client_company}
Client Email: {task.email}

Please make sure to complete it before the due date {task.submission_date}.

Thank you 

Best regards,
Admin
                """,
                'mitr.taskreminder@gmail.com',
                [task.employee.email],
                fail_silently=False,
            )
            logger.info(f"Reminder email sent for task {task_id}")

            # Calculate next reminder date
            task.next_reminder_date = current_time + task.remind_every
            task.save()

        # Schedule the next reminder
        send_reminder_email.apply_async((task.id,), eta=task.next_reminder_date)
    except Task.DoesNotExist:
        logger.error(f"Task {task_id} does not exist")
    except Exception as e:
        logger.error(f"Error sending reminder email for task {task_id}: {e} as NOT the right time")

@shared_task
def send_overdue_reminder(task_id):
    from .models import Task
    try:
        task = Task.objects.get(id=task_id)
        today = datetime.now().date()
        overdue_since = today - task.submission_date

        if overdue_since.days <= 30 and not task.completed:
            send_mail(
                f"Overdue Task Reminder: {task.title}",
                f"""
Dear {task.employee},

The task assigned to you is overdue.

Task Name: {task.title}
Task Description: {task.description}
Client Name: {task.client_company}
Client Email: {task.email}

Please complete it as soon as possible.

Thank you 

Best regards,
Admin
                """,
                'mitr.taskreminder@gmail.com',
                [task.employee.email],
                fail_silently=False,
            )
            logger.info(f"Overdue reminder email sent for task {task_id}")

            # Schedule the next overdue reminder
            send_overdue_reminder.apply_async((task.id,), eta=datetime.now() + timedelta(hours=12))
        else:
            logger.info(f"No more reminders needed for task {task_id}")
    except Exception as e:
        logger.error(f"Error sending overdue reminder for task {task_id}: {e}")

@shared_task
def check_overdue_tasks(task_id):
    from .models import Task
    from datetime import datetime, timedelta

    try:
        today = datetime.now().date()
        overdue_tasks = Task.objects.filter(completed=False, submission_date__lt=today, id=task_id)

        for task in overdue_tasks:
            overdue_since = today - task.submission_date
            if overdue_since.days <= 30:
                send_overdue_reminder.delay(task.id)
        
        logger.info("Checked for overdue tasks and scheduled reminders")
    except Exception as e:
        logger.error(f"Error checking overdue tasks: {e}")