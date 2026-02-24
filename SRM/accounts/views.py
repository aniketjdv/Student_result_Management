from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm
from .models import User, LoginHistory
from .forms import (
    LoginForm, UserRegistrationForm, UserProfileForm, 
    AdminUserCreationForm, PasswordResetRequestForm, PasswordResetForm
)
from django.core.paginator import Paginator

# Helper function to get client IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============= AUTHENTICATION VIEWS =============

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('redirect_dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Set session expiry
                    if not remember_me:
                        request.session.set_expiry(0)  # Session expires on browser close
                    else:
                        request.session.set_expiry(1209600)  # 2 weeks
                    
                    # Log login history
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        session_key=request.session.session_key
                    )
                    
                    # Update last login IP
                    user.last_login_ip = get_client_ip(request)
                    user.save(update_fields=['last_login_ip'])
                    
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')
                    
                    # Redirect based on role
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('redirect_dashboard')
                else:
                    messages.error(request, 'Your account has been disabled.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    # Update logout time in login history
    try:
        last_login = LoginHistory.objects.filter(
            user=request.user,
            session_key=request.session.session_key
        ).latest('login_time')
        last_login.logout_time = timezone.now()
        last_login.save()
    except LoginHistory.DoesNotExist:
        pass
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def redirect_dashboard(request):
    """Redirect users to their respective dashboards based on role"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.is_admin:
        return redirect('admin_dashboard')
    elif request.user.is_teacher:
        return redirect('teacher_dashboard')
    elif request.user.is_student:
        return redirect('student_dashboard')
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('login')


# ============= PROFILE VIEWS =============

@login_required
def profile_view(request):
    """View user profile"""
    user = request.user
    profile = user.get_profile()
    
    # Get recent login history
    recent_logins = LoginHistory.objects.filter(user=user).order_by('-login_time')[:10]
    
    context = {
        'user': user,
        'profile': profile,
        'recent_logins': recent_logins,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


# ============= ADMIN USER MANAGEMENT VIEWS =============

def is_admin(user):
    """Check if user is admin"""
    return user.role == 'admin'


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard"""
    from students.models import Student
    from teachers.models import Teacher
    from courses.models import Program, Subject
    from results.models import SemesterResult
    
    # Get statistics
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.filter(is_active=True).count()
    total_programs = Program.objects.filter(is_active=True).count()
    total_subjects = Subject.objects.filter(is_active=True).count()
    
    # Recent activities
    recent_students = Student.objects.select_related('user').order_by('-id')[:5]
    recent_teachers = Teacher.objects.select_related('user').order_by('-id')[:5]
    
    # User statistics
    total_users = User.objects.count()
    admin_users = User.objects.filter(role='admin').count()
    teacher_users = User.objects.filter(role='teacher').count()
    student_users = User.objects.filter(role='student').count()
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_programs': total_programs,
        'total_subjects': total_subjects,
        'recent_students': recent_students,
        'recent_teachers': recent_teachers,
        'total_users': total_users,
        'admin_users': admin_users,
        'teacher_users': teacher_users,
        'student_users': student_users,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def user_list(request):
    """List all users with filtering and search"""
    users = User.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(users, 20)  # Show 20 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_users': users.count(),
    }
    
    return render(request, 'accounts/user_list.html', context)


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Create new user (admin only)"""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Create New User',
        'button_text': 'Create User'
    })


@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    """Edit user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.username}" updated successfully!')
            return redirect('user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserCreationForm(instance=user)
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'user': user,
        'title': 'Edit User',
        'button_text': 'Update User'
    })


@login_required
@user_passes_test(is_admin)
def user_detail(request, pk):
    """View user details (admin only)"""
    user = get_object_or_404(User, pk=pk)
    profile = user.get_profile()
    login_history = LoginHistory.objects.filter(user=user).order_by('-login_time')[:20]
    
    context = {
        'view_user': user,
        'profile': profile,
        'login_history': login_history,
    }
    
    return render(request, 'accounts/user_detail.html', context)


@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    """Delete user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if user == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully!')
        return redirect('user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'view_user': user})


@login_required
@user_passes_test(is_admin)
def user_toggle_status(request, pk):
    """Toggle user active status (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account!')
        return redirect('user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User "{user.username}" {status} successfully!')
    
    return redirect('user_list')


# ============= PASSWORD RESET VIEWS =============

def password_reset_request(request):
    """Request password reset"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Here you would typically send an email with reset link
                # For now, just show a success message
                messages.success(request, 'Password reset instructions have been sent to your email.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email address.')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    """Confirm password reset with token"""
    # This is a simplified version
    # In production, you'd validate the token and expiry
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # Reset password logic here
            messages.success(request, 'Your password has been reset successfully!')
            return redirect('login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reset_confirm.html', {'form': form})


# ============= REGISTRATION VIEW =============

def register_view(request):
    """User registration (if enabled)"""
    # You might want to disable this in production or add approval workflow
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})
