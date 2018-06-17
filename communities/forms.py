from django import forms
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _

from .models import Community


class CommunitySearchForm(forms.Form):

    VERIFIED_CHOICES = [
        (None, _('All')),
        (True, _('Yes')),
        (False, _('No')),
    ]

    TYPE_CHOICES = [(None, _('All'))] + list(Community.TYPE_CHOICES)

    AGELIMIT_CHOICES = [(None, _('All'))] + list(Community.AGELIMIT_CHOICES)

    SORT_FIELD_CHOICES = [
        ('followers', 'Followers'),
        ('views_per_post', 'Views'),
        ('likes_per_view', 'Likes'),
    ]

    verified = forms.NullBooleanField(required=False, widget=widgets.Select(choices=VERIFIED_CHOICES))
    ctype = forms.ChoiceField(required=False, choices=TYPE_CHOICES, label=_('Type'))
    age_limit = forms.ChoiceField(required=False, choices=AGELIMIT_CHOICES)
    sort_field = forms.ChoiceField(choices=SORT_FIELD_CHOICES)
    inverse = forms.BooleanField(required=False)

    def __init__(self, data=None, *args, **kwargs):
        if data.get('sort_field') is None:
            data = data.copy()
            data['sort_field'] = 'followers'
            data['inverse'] = True
        super().__init__(data, *args, **kwargs)

    def clean(self):
        super().clean()
        self._remove_empty_fields()

    def _remove_empty_fields(self):
        cleaned_data = self.cleaned_data
        empty_field_names = [f for f, v in cleaned_data.items() if v in (None, '')]
        for field_name in empty_field_names:
            del cleaned_data[field_name]
