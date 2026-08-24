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

def register_user(request):
    # Agar user form submit karta hai (Frontend se Fetch API ke through)
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            # User save karein par abhi database me commit na karein
            user = form.save(commit=False) 
            # Password ko secure (hash) karke save karein
            user.set_password(form.cleaned_data['password'])  
            user.save()
            
            # 🟢 PRO LOGIC: Naya account hamesha by default 'employee' banega
            UserProfile.objects.create(
                user=user,
                role='employee', 
                phone_number=form.cleaned_data.get('phone_number')
                # Manager set karne ki zaroorat nahi, wo by default azaad (None) rahega
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Registration successful! Please login.', 
                'redirect_url': '/accounts/login/'
            })
            
        else:
            # Agar form me galti hai, toh errors JSON me bhejenge
            return JsonResponse({'status': 'error', 'errors': form.errors}) 
            
    else:
        # GET request - Khali form dikhayein
        form = UserRegistrationForm() 
        
    return render(request, 'accounts/register.html', {'form': form})


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


@login_required # Ye page bina login ke open nahi hoga
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required
def logout_user(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def team_list(request):
    user = request.user
    
    # 1. ADMIN LOGIC: Saari company ki team dikhegi
    if user.is_superuser:
        team_members = UserProfile.objects.select_related('user').all()
        
    # 2. MANAGER LOGIC: Manager ko wo khud aur uske under kaam karne wale employees dikhenge
    elif hasattr(user, 'profile') and user.profile.role == 'manager':
        team_members = UserProfile.objects.filter(
            Q(user=user) | Q(manager=user)
        ).select_related('user')
        
    # 3. EMPLOYEE LOGIC: Employee ko sirf apne manager ki team ke baaki log dikhenge
    else:
        if hasattr(user, 'profile') and user.profile.manager:
            # Apne manager ki puri team dekho
            team_members = UserProfile.objects.filter(
                manager=user.profile.manager
            ).select_related('user')
        else:
            # Agar koi manager nahi hai, toh sirf khud ko dekho
            team_members = UserProfile.objects.filter(user=user)
            
    return render(request, 'accounts/team.html', {'team_members': team_members})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user) #form me 'instance=request.user' likhne se purana data pehle se bhara hua aayega
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')  #Save hone ke baad wapas profile par bhej dega
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})

def is_admin(user): #1.Security Check: Ye check karega ki delete karne wala Admin hai ya nahi
    return user.is_superuser

@user_passes_test(is_admin) # Agar admin nahi hai, toh ye function nahi chalega
def delete_member(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id) # User ko database me dhoondho
    
    if user_to_delete == request.user: # Smart Check: Admin galti se khud ka account delete na kar de!
        messages.error(request, "Are sir Kya kar rahe ho apna hi account kyu delete kar rahe ho.")
        return redirect('accounts:team_list') # Apne team page ka sahi URL name check kar lena
     
    user_to_delete.delete()  # User ko delete karo
    messages.success(request, f"Team member {user_to_delete.username} successfully deleted!")
    return redirect('accounts:team_list')


@user_passes_test(is_admin)
def edit_member(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id) #User aur uski Profile (Custom fields) dono nikal lo
    profile = user_to_edit.profile 
    if request.method == 'POST':
        user_to_edit.first_name = request.POST.get('first_name', '')
        user_to_edit.last_name = request.POST.get('last_name', '')
        user_to_edit.email = request.POST.get('email', '')
        user_to_edit.save()
        
        profile.role = request.POST.get('role', 'employee')
        profile.phone_number = request.POST.get('phone_number', '')
        profile.save()
        
        messages.success(request, f"{user_to_edit.first_name} ki details update ho gayi hain!")
        return redirect('accounts:team_list') 
    return render(request, 'accounts/edit_member.html', {'member_user': user_to_edit, 'profile': profile})




    # ==========================================
# MANAGER: MY TEAM DASHBOARD (Page dikhane ke liye)
# ==========================================
@login_required
def manager_dashboard(request):
    # Security: Agar user Manager nahi hai, toh use Tasks wale page par wapas bhej do
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
        return redirect('tasks:dashboard') 

    # 1. Meri Team: Wo employees jinka manager ye current user hai
    my_team = UserProfile.objects.filter(manager=request.user).select_related('user')

    # 2. Azaad Employees: Wo employees jinka role employee hai aur koi boss nahi hai
    available_employees = UserProfile.objects.filter(role='employee', manager__isnull=True).select_related('user')

    context = {
        'my_team': my_team,
        'available_employees': available_employees
    }
    return render(request, 'accounts/manager_team.html', context)


# ==========================================
# MANAGER: ADD EMPLOYEE ACTION (Button click hone par)
# ==========================================
@login_required
def add_employee_to_team(request, profile_id):
    # Sirf POST request aur Manager hi isko chala sakta hai
    if request.method == 'POST' and hasattr(request.user, 'profile') and request.user.profile.role == 'manager':
        
        # Us azaad employee ko database me dhoondo
        employee_profile = get_object_or_404(UserProfile, id=profile_id, role='employee', manager__isnull=True)
        
        # Is current Manager ko uska Boss bana do!
        employee_profile.manager = request.user
        employee_profile.save()
        
    # Add karne ke baad wapas My Team page par bhej do
    return redirect('accounts:manager_dashboard')