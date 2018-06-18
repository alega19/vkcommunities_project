from json import dumps as to_json

from django import template
from django.core.serializers.json import DjangoJSONEncoder


register = template.Library()


unsafe2safe = {
    '&': r'\u0026',
    '<': r'\u003c',
    '>': r'\u003e',
    '\u2028': r'\u2028',
    '\u2029': r'\u2029',
}


@register.filter
def json(obj):
    s = to_json(obj, cls=DjangoJSONEncoder)
    for old, new in unsafe2safe.items():
        s = s.replace(old, new)
    return s
