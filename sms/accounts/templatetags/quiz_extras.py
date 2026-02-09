
from django import template

register = template.Library()

@register.filter
def get_option(question, option):
    return getattr(question, f"option_{option.lower()}")
