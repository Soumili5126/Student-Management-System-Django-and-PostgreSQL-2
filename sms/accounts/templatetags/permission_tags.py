from django import template

register = template.Library()

@register.filter
def has_permission(user, code):
    if not user.is_authenticated:
        return False

    # Admin bypass
    if user.role and user.role.name.lower() == 'admin':
        return True

    return user.permissions.filter(code=code).exists()