import json
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
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
from django.urls import reverse, NoReverseMatch
from django.views.decorators.http import require_POST
from .models import Notification
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from django.utils import timezone
from tasks.models import LeaveRequest


# Optional app models import
try:
    from tasks.models import Task
except Exception:
    Task = None

try:
    from resource.models import Resource
except Exception:
    Resource = None


def safe_reverse(url_name, default="#"):
    """Crash hone se bachane ke liye safe URL reverse"""
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return default

@login_required
def global_search_api(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})

    results = []

    try:
        # 1. Search Users with dynamic role check
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).select_related('profile')[:5]

        # Target fallback URL
        user_target_url = safe_reverse("accounts:employees_list", safe_reverse("accounts:attendance", "/accounts/attendance/"))

        for u in users:
            # Dynamic role detection
            if u.is_superuser:
                user_role = "Admin"
                user_icon = "fas fa-user-shield"
            elif hasattr(u, "profile") and getattr(u.profile, "role", None):
                user_role = u.profile.role.title()
                user_icon = "fas fa-user-tie" if user_role.lower() == "manager" else "fas fa-user"
            else:
                user_role = "Employee"
                user_icon = "fas fa-user"

            results.append({
                "type": user_role,
                "icon": user_icon,
                "title": u.get_full_name() or u.username,
                "subtitle": u.email or f"Active {user_role}",
                "url": user_target_url,
            })

        # 2. Search Tasks
        if Task:
            tasks = Task.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )[:5]
            task_target_url = safe_reverse("tasks:overview", safe_reverse("tasks:task_list", "/tasks/overview/"))
            for t in tasks:
                results.append({
                    "type": "Task",
                    "icon": "fas fa-tasks",
                    "title": t.title,
                    "subtitle": f"Status: {getattr(t, 'status', 'Active')}",
                    "url": task_target_url,
                })

        # 3. Search Resources
        if Resource:
            resources = Resource.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )[:5]
            res_target_url = safe_reverse("resource:resource_list", "/resource/")
            for r in resources:
                results.append({
                    "type": "Resource",
                    "icon": "fas fa-folder-open",
                    "title": r.title,
                    "subtitle": getattr(r, "category", "Resource File"),
                    "url": res_target_url,
                })

    except Exception as e:
        return JsonResponse({"results": [], "error": str(e)}, status=500)

    return JsonResponse({"results": results})

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
        
        messages.success(request, "Your profile has been updated successfully.")
        return redirect('accounts:profile')
        
    return render(request, 'accounts/edit_profile.html', {'profile': profile})


def login_user(request):
    # STEP 1: Sirf POST request (Form Submit ya AJAX) par check karein
    if request.method == 'POST':
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        # STEP 2: Agar User sahi hai (Success)
        if user is not None:
            login(request, user)
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Login successful!', 
                    'redirect_url': '/tasks/' 
                })
                
            return redirect('tasks:dashboard')
            
        # STEP 3: Agar details galat hain (Failed Login)
        else:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'status': 'error', 'message': 'Invalid username or password.'}, status=400)
            # Form wale user ko error dikhaye aur wapas login page par bhej de
            messages.error(request, 'Invalid username or password.')
            return redirect('accounts:login') 

    # STEP 4: Agar normal page refresh ho raha hai (GET request)
    form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def profile_view(request):
    # Ensure profile exists so it doesn't crash for new users
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        # 1. Profile Edit Logic
        if action == 'update_profile':
            user = request.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()

            profile.phone_number = request.POST.get('phone_number', profile.phone_number)
            profile.dob = request.POST.get('dob') or None
            profile.gender = request.POST.get('gender', profile.gender)
            profile.blood_group = request.POST.get('blood_group', profile.blood_group)
            profile.nationality = request.POST.get('nationality', profile.nationality)

            profile.country = request.POST.get('country', profile.country)
            profile.city = request.POST.get('city', profile.city)
            profile.postal_code = request.POST.get('postal_code', profile.postal_code)
            profile.address_line = request.POST.get('address_line', profile.address_line)

            # Profile Picture Upload Handled Here
            if 'profile_pic' in request.FILES:
                profile.profile_pic = request.FILES['profile_pic']

            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')

        # 2. Change Password Logic (supports "Forgot current password?" mode)
        elif action == 'change_password':
            forgot_mode = request.POST.get('forgot_mode') == '1'
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match!')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            elif not forgot_mode and not request.user.check_password(current_password):
                messages.error(request, 'Incorrect current password!')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keeps user logged in after password change
                messages.success(request, 'Password changed successfully!')

            return redirect('accounts:profile')

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
    if request.user.is_superuser or request.session.get('is_original_admin'):
        request.session['is_original_admin'] = True
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
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
        messages.error(request, "You don't have permission to perform this action.")
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

        messages.success(request, f"{manager_obj.first_name} : Your details have been updated successfully!")
        
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
        messages.error(request, "You don't have permission to perform this action.")
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

    today = date.today()

    active_leaves = LeaveRequest.objects.filter(
        status__iexact='approved',
        start_date__lte=today,
        end_date__gte=today
    )

    try:
        on_leave_user_ids = list(active_leaves.values_list('user_id', flat=True))
    except Exception:
        on_leave_user_ids = list(active_leaves.values_list('employee_id', flat=True))

    on_leave_count = len(set(on_leave_user_ids))

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
        'on_leave_count': on_leave_count,        
        'on_leave_user_ids': on_leave_user_ids,
    }
    
    return render(request, 'accounts/employees_list.html', context)

def edit_employee(request, user_id):
    # Sirf Admin allow hoga
    if not (request.user.is_superuser or request.session.get('is_original_admin')):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('tasks:dashboard')

    employee_obj = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=employee_obj)

    if request.method == 'POST':
        # 1. User table update
        employee_obj.first_name = request.POST.get('first_name', '').strip()
        employee_obj.last_name = request.POST.get('last_name', '').strip()
        employee_obj.email = request.POST.get('email', '').strip()
        employee_obj.save()

        # 2. Profile table update (Phone, Role, Department)
        profile.phone = request.POST.get('phone', '').strip()
        
        new_role = request.POST.get('role')
        if new_role:
            profile.role = new_role

        # 🟢 Department update handling
        new_dept = request.POST.get('department')
        if new_dept:
            profile.department = new_dept.strip()

        profile.save()

        messages.success(request, f"{employee_obj.first_name}: Your details have been updated successfully!")
        
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
        messages.error(request, "You don't have permission to add new users.")
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
            messages.error(request, "A user with this email address already exists!")
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

    # Current Manager ke assigned employees
    my_squad = User.objects.filter(profile__manager=request.user).select_related('profile')
    
    # Wo employees jo kisi bhi manager ke under assigned nahi hain
    available_employees = User.objects.filter(
        profile__role__iexact='employee',
        profile__manager__isnull=True
    ).select_related('profile')

    # Available employees ke distinct departments list (Filter pills ke liye)
    departments = (
        available_employees.exclude(profile__department__isnull=True)
        .exclude(profile__department__exact='')
        .values_list('profile__department', flat=True)
        .distinct()
        .order_by('profile__department')
    )

    context = {
        'my_squad': my_squad,
        'squad_count': my_squad.count(),
        'available_employees': available_employees,
        'departments': list(departments),
        'page_title': 'My Squad',
    }
    return render(request, 'accounts/manager_roster.html', context)

# NEW: Employee ko squad me Add karne ka logic
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

# NEW: Employee ko squad se Remove karne ka logic
@login_required
def remove_from_squad(request, emp_id):
    emp = get_object_or_404(User, id=emp_id)
    if emp.profile.manager == request.user:
        emp.profile.manager = None
        emp.profile.save()
        messages.success(request, f"{emp.first_name} was removed from your squad.")
    return redirect('accounts:manager_roster')

@login_required
def role_management(request):
    # Security: Sirf Admins is page ko dekh sakte hain
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        messages.error(request, "Access Denied! Only admins can manage roles.")
        return redirect('accounts:profile')

    # Card Stats Calculation (Sabhi users ka data count karne ke liye)
    all_profiles = UserProfile.objects.select_related('user').all()
    
    total_users = all_profiles.count()
    total_admins = all_profiles.filter(role='admin').count()
    active_admins = all_profiles.filter(role='admin', user__is_active=True).count()
    inactive_admins = total_admins - active_admins

    # Form Submission Logic (Add New Admin/User)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_user':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            role = request.POST.get('role')
            password = request.POST.get('password')

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists!")
            else:
                user = User.objects.create_user(username=email, email=email, password=password, first_name=first_name, last_name=last_name)
                UserProfile.objects.create(user=user, role=role, phone_number=phone_number)
                messages.success(request, f"New {role.title()} added successfully!")
            
            return redirect('accounts:role_management')
            
        elif action == 'delete_user':
            user_id = request.POST.get('user_id')
            user_to_delete = get_object_or_404(User, id=user_id)
            if user_to_delete == request.user:
                messages.error(request, "You cannot delete yourself!")
            else:
                user_to_delete.delete()
                messages.success(request, "User deleted successfully!")
            return redirect('accounts:role_management')

        elif action == 'edit_user':
            user_id = request.POST.get('user_id')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            new_role = request.POST.get('new_role')

            user_obj = get_object_or_404(User, id=user_id)
            profile = get_object_or_404(UserProfile, user=user_obj)

            # Check if updated username or email is already taken by another user
            if User.objects.filter(username=username).exclude(id=user_id).exists():
                messages.error(request, "Username is already taken.")
            elif User.objects.filter(email=email).exclude(id=user_id).exists():
                messages.error(request, "Email is already taken.")
            else:
                user_obj.first_name = first_name
                user_obj.last_name = last_name
                user_obj.username = username
                user_obj.email = email
                user_obj.save()

                profile.phone_number = phone_number
                profile.role = new_role
                profile.save()

                messages.success(request, f"User {user_obj.username} updated successfully!")

            return redirect('accounts:role_management')

    # SIRF ADMINS KO TABLE ME DIKHANE KE LIYE FILTER
    admin_profiles = all_profiles.filter(role='admin').order_by('-created_at')

    context = {
        'profiles': admin_profiles, # Table me sirf admin_profiles jayega
        'total_users': total_users,
        'total_admins': total_admins,
        'active_admins': active_admins,
        'inactive_admins': inactive_admins,
    }
    return render(request, 'accounts/role_management.html', context)

@login_required
def get_notifications_api(request):
    """Fetch unread count & top 6 latest notifications"""
    notifications = Notification.objects.filter(user=request.user)[:6]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    results = []
    for n in notifications:
        results.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'link': n.link or '#',
            'is_read': n.is_read,
            'time_ago': n.created_at.strftime('%d %b, %H:%M')
        })

    return JsonResponse({
        'unread_count': unread_count,
        'notifications': results
    })

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark single notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)

@login_required
@csrf_exempt
def mark_all_notifications_read(request):
    """Marks all notifications as read for the logged-in user"""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user).update(is_read=True)
        return JsonResponse({'status': 'success', 'message': 'All marked as read'})
    return JsonResponse({'status': 'error'}, status=400)