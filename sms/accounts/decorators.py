from functools import wraps
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.contrib import messages


def role_required(allowed_roles):
    """
    allowed_roles = ['admin', 'faculty']
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect('login')

            if not request.user.role:
                return render(request, '403.html', status=403)

            role_name = request.user.role.name.lower()

            if role_name not in [r.lower() for r in allowed_roles]:
                return render(request, '403.html', status=403)

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


# Optional convenience decorators

def admin_only(view_func):
    return role_required(['admin'])(view_func)


def faculty_only(view_func):
    return role_required(['faculty'])(view_func)


def student_only(view_func):
    return role_required(['student'])(view_func)

from django.http import HttpResponseForbidden
from functools import wraps


def permission_required(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return HttpResponseForbidden()

            # Admin bypass (full access)
            if request.user.role and request.user.role.name.lower() == 'admin':
                return view_func(request, *args, **kwargs)

            if request.user.permissions.filter(code=permission_code).exists():
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden()

        return wrapper
    return decorator

