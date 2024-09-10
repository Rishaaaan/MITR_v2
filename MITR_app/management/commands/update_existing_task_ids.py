from django.core.management.base import BaseCommand
from MITR_app.models import Task  # Ensure to replace with the correct app name

class Command(BaseCommand):
    help = 'Update task_id for existing tasks to ensure uniqueness'

    def handle(self, *args, **kwargs):
        tasks = Task.objects.all() # Only tasks without a task_id
        updated_count = 0

        for task in tasks:
            new_task_id = task.generate_task_id()
            if task.task_id != new_task_id:
                task.task_id = new_task_id
                task.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} tasks with unique task IDs'))