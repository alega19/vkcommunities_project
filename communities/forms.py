from django import forms
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _

from .models import Community


class YesNoAllField(forms.NullBooleanField):

    widget = forms.Select(choices=[
        (None, _('All')),
        ('1', _('Yes')),
        ('0', _('No')),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(required=False, *args, **kwargs)


class IntChoiceField(forms.TypedChoiceField):

    def __init__(self, *args, **kwargs):
        super().__init__(coerce=int, empty_value=None, *args, **kwargs)


class CommunitySearchForm(forms.Form):

    TYPE_CHOICES = [
        (None, _('All')),
        (Community.TYPE_PUBLIC_PAGE, _('Public page')),
        (Community.TYPE_OPEN_GROUP, _('Open group')),
        (Community.TYPE_CLOSED_GROUP, _('Closed group')),
    ]

    AGELIMIT_CHOICES = [(None, _('All'))] + list(Community.AGELIMIT_CHOICES)

    SORTING_CHOICES = [
        ('followers', 'Followers'),
        ('views_per_post', 'Views'),
        ('likes_per_view', 'Likes'),
    ]

    verified = YesNoAllField()
    ctype = IntChoiceField(required=False, choices=TYPE_CHOICES, label=_('Type'))
    age_limit = IntChoiceField(required=False, choices=AGELIMIT_CHOICES)
    sort_by = forms.ChoiceField(choices=SORTING_CHOICES)
    inverse = forms.BooleanField(required=False)
