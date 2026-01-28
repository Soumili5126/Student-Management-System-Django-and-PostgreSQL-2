from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from functools import wraps
from django.shortcuts import render


# ---Admin-only decorator---
def admin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        messages.error(request, "You are not authorized to access this page.")
        return redirect('login')
    return wrapper

# ---Faculty-only decorator---
def faculty_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'faculty':
            return view_func(request, *args, **kwargs)
        messages.error(request, "You are not authorized to access this page.")
        return redirect('login')
    return wrapper

# ---Student-only decorator---
def student_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'student':
            return view_func(request, *args, **kwargs)
        messages.error(request, "You are not authorized to access this page.")
        return redirect('login')
    return wrapper

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                return render(request, '403.html', status=403)
            return render(request, '403.html', status=403)
        return wrapper
    return decorator