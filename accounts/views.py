import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .forms import UserRegistrationForm, LoginForm
from .models import UserProfile

def register_user(request):
    # Agar user form submit karta hai
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # User save karein par abhi database me commit na karein
            user = form.save(commit=False)
            # Password ko secure (hash) karke save karein
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # User banne ke baad uski Profile create karein
            UserProfile.objects.create(
                user=user,
                role=form.cleaned_data.get('role'),
                phone_number=form.cleaned_data.get('phone_number')
            )
            messages.success(request, 'Registration successful! Please login.')
            return redirect('accounts:login')
    else:
        # Agar user sirf page open karta hai
        form = UserRegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        # JavaScript (Fetch API) se data aayega toh JSON format me hoga
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        else:
            # Agar normal form submit hota hai
            username = request.POST.get('username')
            password = request.POST.get('password')

        # Check karein ki username aur password database me match hota hai ya nahi
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user) # User ko login kara diya
            
            # Agar JavaScript se request aayi thi, toh JSON bhejein
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Login successful!', 
                    'redirect_url': '/accounts/profile/'
                })
            return redirect('accounts:profile')
        else:
            # Agar details galat hain
            if request.headers.get('Content-Type') == 'application/json':
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


# Agar file ke upar login_required import nahi hai, toh check kar lein ki ye line ho:
# from django.contrib.auth.decorators import login_required

@login_required
def team_list(request):
    # Database se saare team members ka data nikal rahe hain
    team_members = UserProfile.objects.all().select_related('user')
    return render(request, 'accounts/team.html', {'team_members': team_members})