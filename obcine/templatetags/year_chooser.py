from django import template

register = template.Library()

@register.simple_tag
def line_percent(list_length, index, center=False):
    if list_length <= 1:
        return 50
    if not center: # go edge to edge
        return 100 / (list_length - 1) * index
    else: # center under each bar chart column
        return 100 / list_length * (index + 0.5)
