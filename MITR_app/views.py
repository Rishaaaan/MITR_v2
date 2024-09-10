# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_backends, logout
from django.contrib.auth.models import User
from .models import Task, CustomUser, Employee
from .forms import TaskForm, RegistrationForm, LoginForm, EmployeeForm, DateForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from datetime import date, datetime, timedelta
from django.http import HttpResponse
from django.utils.timezone import now
import matplotlib.pyplot as plt
import os
import pandas as pd
import xlsxwriter
from django.utils import timezone
from django.db.models import F
import pytz
from django.views.decorators.csrf import csrf_protect

User = get_user_model()


def login_register_view(request):
    if request.method == 'POST':
        if 'login' in request.POST:  # Distinguish between login and register forms
            login_form = LoginForm(request.POST)
            register_form = RegistrationForm()

            if login_form.is_valid():
                email = login_form.cleaned_data['email']
                password = login_form.cleaned_data['password']
                user = authenticate(request, email=email, password=password)
                if user is not None:
                    login(request, user)
                    # Check if the user is an employee
                    is_employee = Employee.objects.filter(email=email).exists()
                    request.session['is_employee'] = is_employee
                    return redirect('dashboard')
                else:
                    messages.error(request, "Invalid email or password.")
            else:
                messages.error(request, "Login form is invalid.")

        elif 'register' in request.POST:  # Handle registration form submission
            login_form = LoginForm()
            register_form = RegistrationForm(request.POST)

            if register_form.is_valid():
                user = register_form.save(commit=False)
                user.username = register_form.cleaned_data['email']  # Use email as the username
                user.save()

                # Authenticate the user immediately after registration
                user = authenticate(
                    request, 
                    username=register_form.cleaned_data['email'], 
                    password=register_form.cleaned_data['password1']
                )

                if user is not None:
                    # Get the list of available backends
                    backends = get_backends()

                    # Set the backend on the user object
                    for backend in backends:
                        if backend.get_user(user.id) is not None:
                            user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
                            break

                    login(request, user)  # Log the user in after registration
                    return redirect('dashboard')
                else:
                    messages.error(request, "Authentication failed after registration.")
            else:
                # Log form errors
                print("Registration form is invalid:", register_form.errors)
                messages.error(request, f"Registration failed. Please check the form for errors: {register_form.errors}")

    else:
        login_form = LoginForm()
        register_form = RegistrationForm()

    return render(request, 'login_register.html', {
        'login_form': login_form,
        'register_form': register_form
    })

def logout_view(request):
    logout(request)
    return redirect('login_register')

@login_required
def dashboard_view(request):
    from .tasks import send_initial_email
    # CURRENT USER
    user = request.user
    company = user.company  # Get the company
    is_employee = request.session.get('is_employee', False)  # Get employee status from session
    is_superuser = request.user.is_superuser

    # FILTER TASKS BASED ON USER STATUS
    if is_employee:
        tasks = Task.objects.filter(employee__email=user.email)
    else:
        tasks = Task.objects.filter(employee__company=company)

    # HANDLE TASK FORM
    form = TaskForm(user=request.user)
    form_has_errors = False
    employee_form = EmployeeForm()
    print("start")
    if request.method == 'POST':
        print("post toh hai")
        if 'taskForm' in request.POST:
            print("taskform")
            form = TaskForm(user=request.user, data=request.POST)
            if form.is_valid():
                task = form.save(commit=False)
                task.date_added = timezone.now()
                task.task_id = timezone.now().astimezone(pytz.timezone('Asia/Kolkata')).strftime('%d%m%Y%H%M%S')
                task.save()
                send_initial_email.delay(task.id)
                print("works")
                return redirect('dashboard')  # Redirect to the dashboard
            else:
                form_has_errors = True
        elif 'addEmployeeForm' in request.POST:
            print("employeeform")
            employee_form = EmployeeForm(request.POST)
            if employee_form.is_valid():
                employee = employee_form.save(commit=False)
                employee.company = company
                employee.save()
                return redirect('dashboard')  # Redirect to the dashboard

    else:
        # If GET request, create empty forms
        form = TaskForm(user=request.user)
        employee_form = EmployeeForm()

    # SEARCH
    search_query = request.GET.get('search', '')

    if search_query:
        tasks = tasks.filter(title__icontains=search_query)

    # RETURN VALUES
    return render(request, 'dashboard.html',
    {
        'is_employee': is_employee,
        'is_superuser': is_superuser,
        'today': date.today(),
        'tasks': tasks,
        'search_query': search_query,
        'form': form,
        'form_has_errors': form_has_errors,
        'employee_form': employee_form
    })
    
 
# @login_required
# def dashboard_view(request):

#     # IMPORTS
#     from .tasks import send_initial_email

#     # CURRENT USER
#     user = request.user
#     company = user.company                                       # Get the company
#     is_employee = request.session.get('is_employee', False)      # Get employee status from session
#     is_superuser = request.user.is_superuser      
#     # Filter user details
#     if is_employee:
#         tasks = Task.objects.filter(employee__email=user.email)
#     if not user.is_superuser:
#         tasks = Task.objects.filter(employee__email=user.email)
#     else:
#         tasks = Task.objects.filter(employee__company=company)   # Company wise sort

#     # ADD TASK FUNCTIONS
#     form = TaskForm(user=request.user)                           # Pass the user to the form
#     form_has_errors = False

#     if request.method == 'POST':
#         form = TaskForm(user=request.user, data=request.POST)    # Pass the user and form data to the form
#         if form.is_valid():
#             task = form.save(commit=False)
#             task.date_added = timezone.now()
#             task.task_id = timezone.now().astimezone(pytz.timezone('Asia/Kolkata')).strftime('%d%m%Y%H%M%S')
#             task.save()
#             send_initial_email.delay(task.id)
#             return redirect('dashboard')                         # Redirect to the dashboard
#         else:
#             form_has_errors = True

#     # SEARCH
#     search_query = request.GET.get('search', '')

#     # Filter search tasks 
#     if search_query:
#         tasks = tasks.filter(title__icontains=search_query)


#     # RETURN VALUES
#     return render(request, 'dashboard.html', 
#     {
#         'is_employee': is_employee,
#         'is_superuser': is_superuser,

#         'today': date.today(),
#         'tasks': tasks,

#         'search_query': search_query,

#         'form': form, 
#         'form_has_errors': form_has_errors
#     })


@login_required
# def new_dashView(request):

#     # form = TaskForm(user=request.user)  # Pass the user to the form
#     # form_has_errors = False

#     search_query = request.GET.get('search', '')  # Get the search query from the request
#     user = request.user  # Get the logged-in user
#     company = user.company  # Get the company of the logged-in user
#     is_employee = request.session.get('is_employee', False)  # Get employee status from session
#     #superusers = User.objects.filter(is_superuser=True)
#     # tasks = Task.objects.all()

#     if user.is_superuser:
#         is_employee = False

#     if is_employee:
#         # Filter tasks assigned to the logged-in employee
#         tasks = Task.objects.filter(employee__email=user.email)

#     if not user.is_superuser:
#         tasks = Task.objects.filter(employee__email=user.email)

#     else:
#         # Filter tasks based on employees who belong to the same company as the logged-in user
#         tasks = Task.objects.filter(employee__company=company)

#     if search_query:
#         # Filter tasks based on the search query
#         tasks = tasks.filter(title__icontains=search_query)

#     return render(request, 'dashboard.html', {
#         'tasks': tasks,
#         'today': date.today(),
#         'search_query': search_query,
#         'is_employee': is_employee,
#         'is_superuser': user.is_superuser,  # Pass is_superuser flag to the template
#         # 'form': form, 'form_has_errors': form_has_errors
#     })


 
# def add_task_view(request):
#     from .tasks import send_initial_email
#     form = TaskForm(user=request.user)  # Pass the user to the form
#     form_has_errors = False
#     if request.method == 'POST':
#         form = TaskForm(user=request.user, data=request.POST)  # Pass the user and form data to the form
#         if form.is_valid():
#             task = form.save(commit=False)
#             task.date_added = timezone.now()
#             task.task_id = timezone.now().astimezone(pytz.timezone('Asia/Kolkata')).strftime('%d%m%Y%H%M%S')
#             task.save()
#             send_initial_email.delay(task.id)
#             return redirect('dashboard')  # Redirect to the dashboard
            
#         else:
#             form_has_errors = True
            
#     return render(request, 'add_task.html', {'form': form, 'form_has_errors': form_has_errors})

 
def add_employee_view(request):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')

    # Retrieve the logged-in user's company
    company = request.user.company

    if request.method == 'POST':
        # Create a form instance and populate it with data from the request
        form = EmployeeForm(request.POST)
        if form.is_valid():
            # Create a new employee object but don't save it yet
            employee = form.save(commit=False)
            # Associate the employee with the user's company
            employee.company = company
            # Save the employee to the database
            employee.save()
            # Redirect to a success page or another relevant page
            return redirect('dashboard')
    else:
        # If it's a GET request, create an empty form
        form = EmployeeForm()

    return render(request, 'add_employee.html', {'form': form})

 
@login_required
def task_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    user = request.user
    is_employee = request.session.get('is_employee', False)  # Correctly call the method on the user object
    form = TaskForm(request.POST or None, instance=task)

    if request.method == 'POST':
        if is_employee and 'mark_as_completed' in request.POST:
            # Check if the form is valid and if the overdue_reason is provided
            overdue_reason = request.POST.get('overdue_reason', '').strip()
            if not overdue_reason and task.submission_date <= datetime.now().date():
                form.add_error('overdue_reason', 'Reason for overdue is required if you mark the task as completed.')
            else:
                task.employee_marked_completed = True
                task.completed_date = datetime.now()
                task.overdue_reason = overdue_reason
                task.save()
                return redirect('task_view', task_id=task.id)
        elif not is_employee and 'complete_task' in request.POST:
            task.completed = True
            task.completed_at = datetime.now()  # Update completion date
            task.completed_by = user  # Set the user who completed the task
            task.save()
            return redirect('task_view', task_id=task.id)
        elif not is_employee and 'rework_task' in request.POST:
            # Handle reworking the task
            task.rework_by = user
            task.rework_date = timezone.now()
            task.save()
            return redirect('task_view', task_id=task.id)

    context = {
        'task': task,
        'today': now().astimezone(pytz.timezone('Asia/Kolkata')).date(),
        'is_employee': is_employee,
        'form': form  # Pass the form to the template
    }
    return render(request, 'task_view.html', context)

 
def delete_task_view(request, task_id):
    # Get the task object or return a 404 error if not found
    task = get_object_or_404(Task, id=task_id)

    # Check if the user is authorized to delete the task (e.g., only employers)
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)  # Return an unauthorized response

    # Delete the task
    task.delete()

    # Redirect to the dashboard or any other appropriate page after deletion
    return redirect('dashboard')

 
def set_incomplete_view(request, task_id):
    # Get the task object or return a 404 error if not found
    task = get_object_or_404(Task, id=task_id)

    # Check if the user is authorized to set the task as incomplete
    # For example, only employers or users with specific permissions can do this
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)  # Return an unauthorized response

    # Set the task as incomplete
    task.completed = False
    task.save()

    # Redirect to the task view or any other appropriate page after updating
    return redirect('task_view', task_id=task.id)

 
def employee_list_view(request):
    company = request.user.company
    employees = Employee.objects.filter(company=company)
    return render(request, 'employee_list.html', {'employees': employees})

 
def remove_employee_view(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee removed successfully.')
        return redirect('employee_list')
    return render(request, 'confirm_remove_employee.html', {'employee': employee})

 
def confirm_remove_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')  # Redirect to the dashboard after deletion

    return render(request, 'confirm_remove_employee.html', {'employee': employee})

 
def collect_employee_data(employee_id):
    employee = Employee.objects.get(id=employee_id)
    total_tasks = Task.objects.filter(employee=employee).count()
    completed_tasks = Task.objects.filter(employee=employee, completed=True).count()
    overdue_tasks = Task.objects.filter(employee=employee, completed=False, submission_date__lt=datetime.now().date()).count()
    pending_tasks = Task.objects.filter(employee=employee, completed=False, submission_date__gt=datetime.now().date()).count()

    data = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'pending_tasks' : pending_tasks
    }

    return employee.name, data

 
def plot_employee_progress(employee_id):
    employee_name, data = collect_employee_data(employee_id)
    colors = ['grey', 'green', 'red', 'blue']
    df = pd.DataFrame([data], index=[employee_name])
    ax = df.plot(kind='bar', figsize=(10, 6), color=colors)

    plt.title(f'{employee_name} Task Progress')
    plt.xlabel('Tasks')
    plt.ylabel('Number of Tasks')
    plt.xticks(rotation=0)
    plt.legend(['Total Tasks', 'Completed Tasks', 'Overdue Tasks', 'Pending Tasks'])
    plt.tight_layout()

    # Save the plot as an image file, overwriting any existing file
    image_filename = f'employee_progress_{employee_id}.png'
    image_dir = os.path.join('static', 'images')  # Ensure 'images' directory exists inside 'static'
    os.makedirs(image_dir, exist_ok=True)  # Create directory if it doesn't exist
    image_path = os.path.join(image_dir, image_filename)

    plt.savefig(image_path)
    plt.close()

    return os.path.join('images', image_filename)

 
def employee_progress(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    tasks = Task.objects.filter(employee=employee)
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    pending_tasks = tasks.filter(completed=False).count()
    overdue_tasks = Task.objects.filter(employee=employee, completed=False, submission_date__lt=datetime.now().date()).count()
    progress_graph_url = plot_employee_progress(employee_id)
    today = datetime.today().date()

    context = {
        'employee': employee,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'tasks': tasks,
        'progress_graph_url': progress_graph_url,
        'today': today,
        'overdue_tasks' : overdue_tasks,
    }

    return render(request, 'employee_progress.html', context)

 
def generate_summary(date):
    start_date = datetime.datetime.combine(date, datetime.time.min)
    end_date = datetime.datetime.combine(date, datetime.time.max)

    created_tasks = Task.objects.filter(created_at__range=(start_date, end_date))
    completed_tasks = Task.objects.filter(completed_at__range=(start_date, end_date))
    overdue_tasks = Task.objects.filter(submission_date__lt=date, completed=False)

    summary = {
        'date': date,
        'created_tasks': created_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
    }

    return summary

 
def summary_report(request):
    selected_date_str = request.GET.get('date', datetime.now().strftime('%Y-%m-%d'))
    report_type = request.GET.get('report_type', 'daily')
    status_filter = request.GET.get('status_filter', 'all')

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    if report_type == 'weekly':
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)
    elif report_type == 'monthly':
        start_date = selected_date.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:  # Daily
        start_date = selected_date - timedelta(days=1)
        end_date = selected_date + timedelta(days=1)

    tasks_created = set(Task.objects.filter(date_added__range=[start_date, end_date]))
    tasks_completed = set(Task.objects.filter(completed_date__range=[start_date, end_date], completed=True))
    tasks_overdue = set(Task.objects.filter(submission_date__lt=selected_date, completed=False))

    all_tasks = tasks_created | tasks_completed | tasks_overdue

    # Apply the status filter
    if status_filter != 'all':
        if status_filter == 'completed':
            all_tasks = {task for task in all_tasks if task.completed and task.completed_date <= task.submission_date}
        elif status_filter == 'pending':
            all_tasks = {task for task in all_tasks if not task.completed and task.submission_date >= selected_date}
        elif status_filter == 'overdue':
            all_tasks = {task for task in all_tasks if not task.completed and task.submission_date < selected_date}
        elif status_filter == 'completed_overdue':
            all_tasks = {task for task in all_tasks if task.completed and task.completed_date > task.submission_date}

    return render(request, 'summary_report.html', {
        'all_tasks': all_tasks,
        'selected_date': selected_date,
        'report_type': report_type,
        'status_filter': status_filter
    })

 
def remove_timezone_from_datetime(dt):
    """Remove timezone information from a datetime object."""
    if dt is not None:
        return dt.replace(tzinfo=None)
    return dt

def download_summary_report(request, date, report_type, status_filter):
    selected_date = datetime.strptime(date, '%Y-%m-%d').date()

    if report_type == 'weekly':
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)
    elif report_type == 'monthly':
        start_date = selected_date.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:  # Daily
        start_date = selected_date
        end_date = selected_date

    # Ensure tasks_created and tasks_completed are filtered correctly
    tasks_created = Task.objects.filter(date_added__date__range=[start_date, end_date])
    tasks_completed = Task.objects.filter(completed_date__date__range=[start_date, end_date], completed=True)
    tasks_overdue = Task.objects.filter(submission_date__lt=selected_date, completed=False)

    all_tasks = tasks_created | tasks_completed | tasks_overdue

    # Apply the status filter
    if status_filter != 'all':
        if status_filter == 'completed':
            all_tasks = all_tasks.filter(completed=True, completed_date__date__lte=F('submission_date'))
        elif status_filter == 'pending':
            all_tasks = all_tasks.filter(completed=False, submission_date__date__gte=selected_date)
        elif status_filter == 'overdue':
            all_tasks = all_tasks.filter(completed=False, submission_date__date__lt=selected_date)
        elif status_filter == 'completed_overdue':
            all_tasks = all_tasks.filter(completed=True, completed_date__date__gt=F('submission_date'))

    # Create an in-memory output file for the new workbook.
    output = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    output['Content-Disposition'] = f'attachment; filename="summary_report_{date}_{report_type}_{status_filter}.xlsx"'

    # Create an Excel workbook and worksheet
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Define the columns
    columns = [
        'Task ID','Task Title', 'Description', 'Client Company', 'Email', 'Client Phone Number',
        'Date Added', 'Submission Date', 'Completed Date', 'Status', 'Employee', 'Overdue_Reason'
    ]

    # Write the column headers
    for col_num, column_title in enumerate(columns):
        worksheet.write(0, col_num, column_title)

    # Write the data
    for row_num, task in enumerate(all_tasks, start=1):
        status = 'Pending'
        if task.completed:
            if task.completed_date and task.completed_date.date() > task.submission_date:
                status = 'Completed Overdue'
            else:
                status = 'Completed'
        elif task.submission_date < selected_date:
            status = 'Overdue'

        row = [
            task.task_id, task.title, task.description, task.client_company, task.email, task.client_phone_number,
            remove_timezone_from_datetime(task.date_added),
            remove_timezone_from_datetime(task.completed_date) if task.completed_date else '',
            status, str(task.employee), task.overdue_reason
        ]

        for col_num, cell_value in enumerate(row):
            if isinstance(cell_value, datetime):
                cell_value = cell_value.strftime('%Y-%m-%d %H:%M:%S')  # Format datetime for Excel
            worksheet.write(row_num, col_num, cell_value)

    # Close the workbook
    workbook.close()

    return output
