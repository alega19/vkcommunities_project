from django import forms
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


class AbstractForm(forms.Form):

    def _validate_range(self, minimum_field_name, maximum_field_name):
        minimum = self.cleaned_data.get(minimum_field_name)
        maximum = self.cleaned_data.get(maximum_field_name)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise forms.ValidationError(
                _('The minimum more than the maximum'),
                code='invalid_range'
            )


class CommunitySearchForm(AbstractForm):

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
    followers_min = forms.IntegerField(required=False, min_value=0)
    followers_max = forms.IntegerField(required=False, min_value=0)
    views_per_post_min = forms.IntegerField(required=False, min_value=0)
    views_per_post_max = forms.IntegerField(required=False, min_value=0)
    likes_per_view_min = forms.IntegerField(required=False, min_value=0)
    likes_per_view_max = forms.IntegerField(required=False, min_value=0)
    sort_by = forms.ChoiceField(choices=SORTING_CHOICES)
    inverse = forms.BooleanField(required=False)

    def clean_likes_per_view_min(self):
        value = self.cleaned_data.get('likes_per_view_min')
        if value is not None:
            return value * 0.001
        else:
            return value

    def clean_likes_per_view_max(self):
        value = self.cleaned_data.get('likes_per_view_max')
        if value is not None:
            return value * 0.001
        else:
            return value

    def clean(self):
        super().clean()
        self._validate_range('followers_min', 'followers_max')
        self._validate_range('views_per_post_min', 'views_per_post_max')
        self._validate_range('likes_per_view_min', 'likes_per_view_max')


class PostSearchForm(AbstractForm):

    SORTING_CHOICES = [
        ('published_at', 'Date'),
        ('views', 'Views'),
        ('post_likes_per_view', 'Likes/1000Views'),
    ]

    community_id = forms.IntegerField(required=False, min_value=0)
    search = forms.CharField(required=False, empty_value=None)
    marked_as_ads = YesNoAllField()
    has_links = YesNoAllField()
    date_min = forms.DateTimeField(required=False)
    date_max = forms.DateTimeField(required=False)
    views_min = forms.IntegerField(required=False, min_value=0)
    views_max = forms.IntegerField(required=False, min_value=0)
    likes_per_view_min = forms.IntegerField(required=False, min_value=0)
    likes_per_view_max = forms.IntegerField(required=False, min_value=0)
    sort_by = forms.ChoiceField(choices=SORTING_CHOICES)
    inverse = forms.BooleanField(required=False)

    def clean_likes_per_view_min(self):
        value = self.cleaned_data.get('likes_per_view_min')
        if value is not None:
            return value * 0.001
        else:
            return value

    def clean_likes_per_view_max(self):
        value = self.cleaned_data.get('likes_per_view_max')
        if value is not None:
            return value * 0.001
        else:
            return value

    def clean(self):
        super().clean()
        self._validate_range('date_min', 'date_max')
        self._validate_range('views_min', 'views_max')
        self._validate_range('likes_per_view_min', 'likes_per_view_max')
