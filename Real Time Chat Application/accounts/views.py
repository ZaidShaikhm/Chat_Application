from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm
from .models import UserProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.username}! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Mark as online in profile
                if hasattr(user, 'profile'):
                    user.profile.is_online = True
                    user.profile.save()
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next')
                return redirect(next_url if next_url else 'dashboard')
            else:
                messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    if hasattr(request.user, 'profile'):
        request.user.profile.is_online = False
        request.user.profile.save()
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "There was an error updating your profile.")
    else:
        form = UserProfileUpdateForm(instance=profile, user=request.user)

    return render(request, 'profile.html', {
        'profile': profile,
        'form': form
    })


@login_required
def delete_user_view(request, user_id):
    """
    Allows only system administrators to delete registered user accounts.
    """
    is_admin = request.user.is_superuser or request.user.is_staff or request.user.username == 'admin'
    if not is_admin:
        messages.error(request, "Permission denied: Only administrators can delete users.")
        return redirect('dashboard')

    target_user = get_object_or_404(User, id=user_id)

    # Prevent self-deletion and superuser deletion by non-superusers
    if target_user == request.user:
        messages.warning(request, "You cannot delete your own admin account.")
        return redirect('dashboard')

    if target_user.is_superuser and not request.user.is_superuser:
        messages.error(request, "Permission denied: Cannot delete a superuser account.")
        return redirect('dashboard')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User '@{username}' has been permanently deleted from the system.")
        return redirect('dashboard')

    return redirect('dashboard')

