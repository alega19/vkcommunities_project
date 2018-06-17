from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def url_query(context, **kwargs):
    req = context['request']
    query = req.GET.copy()
    for key, val in kwargs.items():
        query[key] = val
    return query.urlencode()
