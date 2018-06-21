from django import template


register = template.Library()


@register.filter
def intformat(num, ndigits):
    num = round(num)
    num_str = str(num)
    return round(num, ndigits - len(num_str))


@register.filter
def intspace(num):
    num_str = str(round(num))
    res = num_str[-3:]
    num_str = num_str[:-3]
    while num_str:
        res = num_str[-3:] + ' ' + res
        num_str = num_str[:-3]
    return res
