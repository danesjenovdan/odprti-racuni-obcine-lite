import math
import re

from django import template
from django.utils.text import capfirst

register = template.Library()


def next_multiple(value, multiple_of):
    return math.ceil(value / multiple_of) * multiple_of


def get_max_amount(node):
    return max([node.get("amount", 0), node.get("planned", 0), node.get("realized", 0)])


@register.simple_tag
def child_max_graph_scale(tree_node, precision=2, slice_count=6):
    children = (tree_node or {}).get("children", []) or [{"amount": 0}]
    child_amounts = [get_max_amount(child) for child in children]
    value_max = math.ceil(max(child_amounts))
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


@register.simple_tag
def amount_percentage(tree_type, summary, amount_type, amount, precision=0):
    amount_type = "realized" if amount_type == "amount" else amount_type
    key = f"{amount_type}_{tree_type}"
    if all := summary.get(key, 0):
        return round(amount / all * 100, precision)
    return 0


@register.filter
def capfirst_if_allcaps(value):
    if not value:
        return value
    if not isinstance(value, str):
        value = str(value)
    if value == value.upper():
        return capfirst(value.lower())
    return capfirst(value)


@register.filter
def remove_obcina_from_name(name):
    return re.sub(r"^\s*Občina\s+", "", name, flags=re.IGNORECASE)
