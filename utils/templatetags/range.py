from django import template


register = template.Library()


@register.filter(name='range')
def range_(value):
    return list(range(int(value)))
