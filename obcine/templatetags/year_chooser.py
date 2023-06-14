from django import template

register = template.Library()

@register.simple_tag
def line_percent(list_length, index):
    if list_length > 1:
        return 100 / (list_length - 1) * index
    else:
        return 50
