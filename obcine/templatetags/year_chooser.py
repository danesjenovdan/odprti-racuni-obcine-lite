from django import template

register = template.Library()

@register.simple_tag
def line_percent(list_length, index):
    return 100 / (list_length - 1) * index
