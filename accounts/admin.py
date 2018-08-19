from django.contrib import admin
from django.contrib import auth

from .models import User


class UserCreationForm(auth.forms.UserCreationForm):

    class Meta:
        model = User
        fields = ['email']


class UserChangeForm(auth.forms.UserChangeForm):

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(auth.admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm

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
