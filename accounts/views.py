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
    if request.method == 'POST':
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)#Check karein ki username aur password database me match hota hai ya nahi
        
        if user is not None:
            login(request, user) # User ko login kara diya
            
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'status': 'success', 
                'message': 'Login successful!', 
                'redirect_url': '/tasks/' 
            })
            
        return redirect('tasks:dashboard')
    else:
            if request.headers.get('Content-Type') == 'application/json': # Agar details galat hain
                return JsonResponse({'status': 'error', 'message': 'Invalid username or password.'}, status=400)
            
            messages.error(request, 'Invalid username or password.')
    
    form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required 
def profile(request):
    return render(request, 'accounts/profile.html')

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
    # Check karega ki kya aap asali admin ho, YA phir admin the aur swap kiya tha
    if request.user.is_superuser or request.session.get('is_original_admin'):
        
        # Ek secret token save kar lo taaki aap wapas Admin ban sako
        request.session['is_original_admin'] = True 
        
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)

        if role == 'admin':
            # Wapas sab powers de do
            user.is_superuser = True
            user.is_staff = True
            profile.role = 'admin'
        
        elif role == 'manager':
            # Superuser hatao, sirf Manager banao
            user.is_superuser = False
            user.is_staff = False
            profile.role = 'manager'
            
        elif role == 'employee':
            # Superuser hatao, sirf Employee banao
            user.is_superuser = False
            user.is_staff = False
            profile.role = 'employee'

        # Dono ko save karo (User aur Profile)
        user.save()
        profile.save()
        
        # Session me UI ke liye current role update karo
        request.session['current_role'] = role
        messages.success(request, f"Swapped to {role.title()} successfully! Real testing activated.")
    
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