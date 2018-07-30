from datetime import time as Time

from django import template

from ..models import Community


register = template.Library()


@register.filter
def type2str(type_):
    if type_ == Community.TYPE_PUBLIC_PAGE:
        return 'PP'
    elif type_ == Community.TYPE_OPEN_GROUP:
        return 'OG'
    elif type_ == Community.TYPE_CLOSED_GROUP:
        return 'CG'
    elif type_ == Community.TYPE_PRIVATE_GROUP:
        return 'PG'
    else:
        raise ValueError('unexpected community type = {0}'.format(type_))


@register.filter
def age_limit2str(age_limit):
    if age_limit == Community.AGELIMIT_UNKNOWN:
        return ''
    elif age_limit == Community.AGELIMIT_NONE:
        return ''
    elif age_limit == Community.AGELIMIT_16:
        return '16+'
    elif age_limit == Community.AGELIMIT_18:
        return '18+'
    else:
        raise ValueError('unexpected age_limit = {0}'.format(age_limit))


@register.filter
def verified2str(verified):
    if verified is None:
        return ''
    elif verified:
        return '(V)'
    else:
        return '(N)'


@register.filter
def get_item(dictionary, key):
    return dictionary[key]


@register.filter
def duration2str(seconds):
    t = Time(
        hour=seconds // 3600,
        minute=(seconds // 60) % 60,
        second=seconds % 60
    )
    if t.hour:
        return t.strftime('%H:%M:%S')
    else:
        return t.strftime('%M:%S')
