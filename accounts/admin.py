from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, Group
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import User
from .forms import SignupForm


class UserChangeForm(forms.ModelForm):

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ['email', 'is_active', 'is_staff']

    def clean_password(self):
        return self.initial["password"]


@admin.register(User)
class MyUserAdmin(UserAdmin):

    form = UserChangeForm
    add_form = SignupForm

    list_display = ('email', 'is_staff', 'is_active', 'last_login', 'joined_at')
    list_filter = ()

    fieldsets = (
        (None, {'fields': ('email', 'password', 'is_active', 'is_staff')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
         ),
    )

    ordering = ('-joined_at',)
    filter_horizontal = ()


admin.site.unregister(Group)
