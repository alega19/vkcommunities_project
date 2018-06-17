from django import template


register = template.Library()


@register.filter
def round_left(num, ndigits):
    num = int(num)
    num_str = str(num)
    v = round(num, ndigits - len(num_str))
    return int(v)


@register.filter
def separate_by_spaces(num):
    num_str = str(int(num))
    res = ''
    while num_str:
        res = num_str[-3:] + ' ' + res
        num_str = num_str[:-3]
    return res
