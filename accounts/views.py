import json
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .forms import UserRegistrationForm, LoginForm
from .models import UserProfile
from .forms import UserUpdateForm
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.core.paginator import Paginator
from tasks.models import Task
from django.utils import timezone


def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False) 
            user.set_password(form.cleaned_data['password'])  
            user.save()
            UserProfile.objects.create(
                user=user,
                role='employee', 
                phone_number=form.cleaned_data.get('phone_number'),
                department=form.cleaned_data.get('department') 
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Registration successful! Please login.', 
                'redirect_url': '/accounts/login/'
            })
            
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}) 
            
    else:
        form = UserRegistrationForm() 
        
    return render(request, 'accounts/register.html', {'form': form})

def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.save()
        
        profile.phone = request.POST.get('phone', '')
        profile.save()
        
        messages.success(request, "Aapki profile update ho gayi hai!")
        return redirect('accounts:profile')
        
    return render(request, 'accounts/edit_profile.html', {'profile': profile})


def login_user(request):
    # 🟢 STEP 1: Sirf POST request (Form Submit ya AJAX) par check karein
    if request.method == 'POST':
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        # 🟢 STEP 2: Agar User sahi hai (Success)
        if user is not None:
            login(request, user)
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Login successful!', 
                    'redirect_url': '/tasks/' 
                })
                
            return redirect('tasks:dashboard')
            
        # 🟢 STEP 3: Agar details galat hain (Failed Login)
        else:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'status': 'error', 'message': 'Invalid username or password.'}, status=400)
            
            # Form wale user ko error dikhaye aur wapas login page par bhej de
            messages.error(request, 'Invalid username or password.')
            return redirect('accounts:login') 

    # 🟢 STEP 4: Agar normal page refresh ho raha hai (GET request)
    # Yahan koi error message nahi chalega, sirf khali form dikhega
    form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'admin' if request.user.is_superuser else 'employee'}
    )
    # Keep an existing profile in sync if someone was promoted to
    # superuser after their profile was already created
    if request.user.is_superuser and profile.role != 'admin':
        profile.role = 'admin'
        profile.save(update_fields=['role'])

    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def logout_user(request):
    logout(request)
    return redirect('accounts:login')


 # ==========================================
@login_required
def manager_dashboard(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        return redirect('tasks:dashboard') 
    my_team = UserProfile.objects.filter(manager=request.user).select_related('user')
    available_employees = UserProfile.objects.filter(role='employee', manager__isnull=True).select_related('user')

    context = {
        'my_team': my_team,
        'available_employees': available_employees
    }
    return render(request, 'accounts/manager_team.html', context)



# MANAGER: ADD EMPLOYEE ACTION (Button click hone par)
@login_required
def add_employee_to_team(request, profile_id):
    if request.method == 'POST' and hasattr(request.user, 'profile') and request.user.profile.role == 'manager':
        employee_profile = get_object_or_404(UserProfile, id=profile_id, role='employee', manager__isnull=True)
        employee_profile.manager = request.user
        employee_profile.save()
    return redirect('accounts:manager_dashboard')

def switch_role(request, role):
    # Only a genuine superuser, or someone mid-simulation who was
    # originally a superuser, may switch roles.
    if request.user.is_superuser or request.session.get('is_original_admin'):

        request.session['is_original_admin'] = True

        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)

        # 🔒 Safety fix: we NEVER touch user.is_superuser or
        # user.is_staff here anymore. Flipping those to False used to
        # permanently strip Django admin/superuser access from the
        # account in the database — if the session was lost before
        # switching back (logout, expired session, cleared cookies),
        # there was no way back in except manually editing the DB.
        # Only UserProfile.role changes now, which is app-level and
        # trivially reversible (re-run this same switch, or fix it
        # via /admin/ if needed).
        if role in ('admin', 'manager', 'employee'):
            profile.role = role
            profile.save()
            request.session['current_role'] = role
            messages.success(request, f"Now viewing as {role.title()}. Your real admin access is unaffected.")

    return redirect(request.META.get('HTTP_REFERER', '/tasks/dashboard/'))




def managers_list(request):
    # 1. Sirf un users ko nikalo jinka role 'manager' hai
    managers = UserProfile.objects.filter(role='manager').select_related('user').order_by('-id')

    # 2.  SEARCH FILTER LOGIC
    search_query = request.GET.get('search', '')
    if search_query:
        managers = managers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # 3.TOP 4 CARDS (Metrics)
    total_managers = managers.count()
    active_managers = managers.filter(user__is_active=True).count()
    inactive_managers = total_managers - active_managers
    top_performers = 0 # (Isko hum baad me task module se link karenge)

    # 4.PAGINATION LOGIC (Ek page par 10 managers)
    paginator = Paginator(managers, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    available_employees = UserProfile.objects.filter(role='employee', user__is_active=True)
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_managers': total_managers,
        'active_managers': active_managers,
        'inactive_managers': inactive_managers,
        'top_performers': top_performers,
        'available_employees': available_employees,
    }
    
    return render(request, 'accounts/managers_list.html', context)
def make_manager(request, user_id):
    if request.user.is_superuser or request.session.get('is_original_admin'):
        profile = get_object_or_404(UserProfile, user__id=user_id)
        profile.role = 'manager'
        profile.save()
        messages.success(request, f"{profile.user.first_name} is now a Manager!")
    return redirect('accounts:managers_list')



def toggle_user_status(request, user_id):
    if request.user.is_superuser or request.session.get('is_original_admin'):
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active # True ko False, False ko True karega
        user.save()
        status = "Active" if user.is_active else "Inactive"
        messages.success(request, f"User status changed to {status}.")
    return redirect(request.META.get('HTTP_REFERER', 'accounts:managers_list'))

def delete_user(request, user_id):
    if request.user.is_superuser or request.session.get('is_original_admin'):
        user = get_object_or_404(User, id=user_id)
        user.delete() # Database se permanently delete
        messages.error(request, "User deleted successfully.")
    return redirect(request.META.get('HTTP_REFERER', 'accounts:managers_list'))

def edit_manager(request, user_id):
    # Sirf Admin ko allow karein
    if not (request.user.is_superuser or request.session.get('is_original_admin')):
        messages.error(request, "Aapko permission nahi hai.")
        return redirect('tasks:dashboard') 

    # Database se Manager (User) aur uski Profile nikaalein
    manager_obj = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=manager_obj)

    if request.method == 'POST':
        # 1. User details update karein
        manager_obj.first_name = request.POST.get('first_name')
        manager_obj.last_name = request.POST.get('last_name')
        manager_obj.email = request.POST.get('email')
        manager_obj.save()

        # 2. Profile update karein (Phone, Role)
        profile.phone = request.POST.get('phone', '') 
        profile.role = request.POST.get('role')
        profile.save()

        messages.success(request, f"{manager_obj.first_name} ki details successfully update ho gayi!")
        
        # Agar edit karte waqt role "Employee" kar diya, toh usko employees list me bhej do
        if profile.role == 'employee':
            return redirect('accounts:employees_list')
        
        # Warna wapas managers list par
        return redirect('accounts:managers_list')

    # GET request hone par form wala page dikhayein
    context = {
        'manager': manager_obj,
        'profile': profile
    }
    return render(request, 'accounts/edit_manager.html', context)

@login_required
def manager_detail(request, user_id):
    # Admin-only — enforced at the backend, not just hidden in UI
    if not (request.user.is_superuser or request.session.get('is_original_admin')):
        messages.error(request, "Aapko permission nahi hai.")
        return redirect('tasks:dashboard')

    manager_obj = get_object_or_404(User, id=user_id)
    manager_profile = get_object_or_404(UserProfile, user=manager_obj, role='manager')

    team_profiles = UserProfile.objects.filter(manager=manager_obj, role='employee').select_related('user')

    # KPI cards — all computed from real data
    total_employees = team_profiles.count()
    active_employees = team_profiles.filter(user__is_active=True).count()

    team_user_ids = team_profiles.values_list('user_id', flat=True)
    team_tasks = Task.objects.filter(assigned_to_id__in=team_user_ids)
    total_tasks = team_tasks.count()
    completed_tasks = team_tasks.filter(status='Done').count()
    completion_rate = round((completed_tasks / total_tasks) * 100) if total_tasks else 0
    overdue_tasks = team_tasks.filter(due_date__lt=timezone.localdate()).exclude(status='Done').count()

    # Last login is the closest real signal we have to "recent activity"
    # — there's no session-duration tracking in this project, so we
    # show recency rather than a fabricated "average time active".
    last_login_display = manager_obj.last_login.strftime('%b %d, %Y %I:%M %p') if manager_obj.last_login else 'Never logged in'

    # Pagination — 8 employees per page
    paginator = Paginator(team_profiles.order_by('user__first_name'), 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'manager': manager_obj,
        'manager_profile': manager_profile,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'overdue_tasks': overdue_tasks,
        'last_login_display': last_login_display,
        'page_obj': page_obj,
    }
    return render(request, 'accounts/manager_detail.html', context)

def employees_list(request):
    # 1. Sirf 'employee' role wale users nikalenge
    employees = UserProfile.objects.filter(role='employee').select_related('user').order_by('-id')

    # 2.SEARCH FILTER LOGIC
    search_query = request.GET.get('search', '')
    if search_query:
        employees = employees.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # 3.TOP CARDS METRICS
    total_employees = employees.count()
    active_employees = employees.filter(user__is_active=True).count()
    inactive_employees = total_employees - active_employees

    # 4.PAGINATION LOGIC
    paginator = Paginator(employees, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
    }
    
    return render(request, 'accounts/employees_list.html', context)

def edit_employee(request, user_id):
    # Sirf Admin allow hoga
    if not (request.user.is_superuser or request.session.get('is_original_admin')):
        messages.error(request, "Aapko permission nahi hai.")
        return redirect('tasks:dashboard')

    employee_obj = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=employee_obj)

    if request.method == 'POST':
        # 1. User table update
        employee_obj.first_name = request.POST.get('first_name')
        employee_obj.last_name = request.POST.get('last_name')
        employee_obj.email = request.POST.get('email')
        employee_obj.save()

        # 2. Profile table update (Phone, Role)
        profile.phone = request.POST.get('phone', '') 
        profile.role = request.POST.get('role')
        profile.save()

        messages.success(request, f"{employee_obj.first_name} ki details update ho gayi!")
        
        # Agar role change karke 'Manager' kar diya, toh managers list me bhejo
        if profile.role == 'manager':
            return redirect('accounts:managers_list')
        
        return redirect('accounts:employees_list')

    context = {
        'employee': employee_obj,
        'profile': profile
    }
    return render(request, 'accounts/edit_employee.html', context)


def add_user(request):
    # Sirf Admin naye users add kar sakta hai
    if not (request.user.is_superuser or request.session.get('is_original_admin')):
        messages.error(request, "Aapko naye users add karne ki permission nahi hai.")
        return redirect('tasks:dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone', '')
        role = request.POST.get('role', 'employee')

        # Check karna ki is email se koi pehle se toh nahi hai
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            messages.error(request, "Is email id se user pehle se exist karta hai!")
            return redirect('accounts:add_user')

        # 1. Naya User Create Karna (Username ko hi email maan rahe hain)
        user = User.objects.create_user(
            username=email, 
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # 2. Uski Profile Create Karna (Phone aur Role ke sath)
        UserProfile.objects.create(
            user=user,
            phone=phone,
            role=role
        )

        messages.success(request, f"{first_name} successfully added as {role.title()}!")
        
        # User jis role ka bana hai, usi list me redirect kar do
        if role == 'manager':
            return redirect('accounts:managers_list')
        else:
            return redirect('accounts:employees_list')

    # Agar GET request hai, toh form dikhao
    return render(request, 'accounts/add_user.html')

@login_required
def manager_roster_view(request):
    if request.user.profile.role != 'manager' and not request.user.is_superuser:
        messages.error(request, "Access Denied: Only managers have a squad.")
        return redirect('tasks:dashboard')

    # Current Manager ke employees
    my_squad = User.objects.filter(profile__manager=request.user).select_related('profile')
    
    # 🟢 NEW: Wo employees jinka abhi koi manager nahi hai (Add karne ke liye)
    available_employees = User.objects.filter(profile__role__iexact='employee', profile__manager__isnull=True)

    context = {
        'my_squad': my_squad,
        'squad_count': my_squad.count(),
        'available_employees': available_employees,
        'page_title': 'My Squad',
    }
    return render(request, 'accounts/manager_roster.html', context)

# 🟢 NEW: Employee ko squad me Add karne ka logic
@login_required
def add_to_squad(request):
    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        if emp_id:
            emp = get_object_or_404(User, id=emp_id)
            emp.profile.manager = request.user
            emp.profile.save()
            messages.success(request, f"{emp.first_name} has been added to your squad!")
    return redirect('accounts:manager_roster')

# 🟢 NEW: Employee ko squad se Remove karne ka logic
@login_required
def remove_from_squad(request, emp_id):
    emp = get_object_or_404(User, id=emp_id)
    if emp.profile.manager == request.user:
        emp.profile.manager = None
        emp.profile.save()
        messages.success(request, f"{emp.first_name} was removed from your squad.")
    return redirect('accounts:manager_roster')