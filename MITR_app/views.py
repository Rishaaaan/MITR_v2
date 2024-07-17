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

User=get_user_model()

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
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
            messages.error(request, "Form is invalid.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']  # Use email as the username
            user.save()

            # Authenticate the user immediately after registration
            user = authenticate(request, username=form.cleaned_data['email'], password=form.cleaned_data['password1'])

            if user is not None:
                # Get the list of available backends
                backends = get_backends()

                # Set the backend on the user object
                for backend in backends:
                    if backend.get_user(user.id) is not None:
                        user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
                        break

                return redirect('login')
        else:
            # Log form errors
            print("Form is invalid:", form.errors)
            messages.error(request, "Registration failed. Please check the form for errors.")
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})



@login_required
def dashboard_view(request):
    search_query = request.GET.get('search', '')  # Get the search query from the request
    user = request.user  # Get the logged-in user
    company = user.company  # Get the company of the logged-in user
    is_employee = request.session.get('is_employee', False)  # Get employee status from session

    if user.is_superuser:
        is_employee = False  # Superuser should be treated as an employer
        print('henlo me preethi')

    elif is_employee:
        # Filter tasks assigned to the logged-in employee
        tasks = Task.objects.filter(employee__email=user.email)
        print('balle balle de sahava shava')
    else:
        
        # Filter tasks based on employees who belong to the same company as the logged-in user
        tasks = Task.objects.filter(employee__company=company)
        
    if search_query:
        # Filter tasks based on the search query
        tasks = tasks.filter(title__icontains=search_query)

    return render(request, 'dashboard.html', {
        'tasks': tasks,
        'today': date.today(),
        'search_query': search_query,
        'is_employee': is_employee,
        'is_superuser': user.is_superuser  # Pass is_superuser flag to the template
    })  


def add_task_view(request):  
    from .tasks import send_initial_email
    form = TaskForm(user=request.user)  # Pass the user to the form
    form_has_errors = False

    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST)  # Pass the user and form data to the form
        if form.is_valid():
            task = form.save(commit=False)
            task.save()
            send_initial_email.delay(task.id)
            return redirect('dashboard')  # Redirect to the dashboard
        else:
            form_has_errors = True

    return render(request, 'add_task.html', {'form': form, 'form_has_errors': form_has_errors})

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

    if request.method == 'POST':
        if is_employee and 'mark_as_completed' in request.POST:
            task.employee_marked_completed = True
            task.save()
        elif not is_employee and 'complete_task' in request.POST:
            task.completed = True
            task.completed_date = datetime.today().date()
            task.save()
        return redirect('task_view', task_id=task.id)
    
    context = {
        'task': task,
        'today': now().date(),
        'is_employee': is_employee,
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

    data = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks
    }
    
    return employee.name, data

def plot_employee_progress(employee_id):
    employee_name, data = collect_employee_data(employee_id)
    colors=['blue', 'green', 'red']
    df = pd.DataFrame([data], index=[employee_name])
    ax = df.plot(kind='bar', figsize=(10, 6),color=colors)
    
    plt.title(f'{employee_name} Task Progress')
    plt.xlabel('Tasks')
    plt.ylabel('Number of Tasks')
    plt.xticks(rotation=0)
    plt.legend(['Total Tasks', 'Completed Tasks', 'Overdue Tasks'])
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
        start_date = selected_date
        end_date = selected_date

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

    # Create an in-memory output file for the new workbook.
    output = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    output['Content-Disposition'] = f'attachment; filename="summary_report_{date}_{report_type}_{status_filter}.xlsx"'

    # Create an Excel workbook and worksheet
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Define the columns
    columns = [
        'Task Title', 'Description', 'Client Company', 'Email', 'Client Phone Number',
        'Date Added', 'Submission Date', 'Completed Date', 'Status', 'Employee'
    ]

    # Write the column headers
    for col_num, column_title in enumerate(columns):
        worksheet.write(0, col_num, column_title)

    # Write the data
    for row_num, task in enumerate(all_tasks, start=1):
        if task.completed:
            if task.completed_date > task.submission_date:
                status = 'Completed Overdue'
            else:
                status = 'Completed'
        elif task.submission_date < selected_date:
            status = 'Overdue'
        else:
            status = 'Pending'

        row = [
            task.title, task.description, task.client_company, task.email, task.client_phone_number,
            task.date_added, task.submission_date, task.completed_date,
            status, str(task.employee)
        ]

        for col_num, cell_value in enumerate(row):
            worksheet.write(row_num, col_num, cell_value)

    # Close the workbook
    workbook.close()

    return output
