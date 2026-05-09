from django import template

register = template.Library()

@register.filter
def add(value, arg):
    """Прибавляет к значению аргумент."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value