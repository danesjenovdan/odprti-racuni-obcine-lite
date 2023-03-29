from django import template
import math

register = template.Library()


def next_multiple(value, multiple_of):
    return math.ceil(value / multiple_of) * multiple_of


@register.simple_tag
def child_max_graph_scale(tree_node, precision=2, slice_count=6):
    value_max = math.ceil(max([child.get('amount', 0) for child in tree_node['children']]))
    num_digits = len(str(value_max))
    divisor = math.pow(10, num_digits - precision)
    factor = math.ceil(value_max / divisor)
    rounded_max = next_multiple(factor, 6) * divisor
    return rounded_max


@register.simple_tag
def graph_scale_values(value_max, slice_count=6):
    value_slice = value_max / slice_count
    values = [int(value_slice * i) for i in range(slice_count + 1)]
    return values
