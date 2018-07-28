from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.password_validation import validate_password

from .models import User


class EmailField(forms.EmailField):
    widget = forms.EmailInput(attrs={'placeholder': 'Email'})

    def __init__(self, *args, **kwargs):
        super().__init__(max_length=254, *args, **kwargs)


class PasswordField(forms.CharField):
    widget = forms.PasswordInput(attrs={'placeholder': 'Password'})

    def __init__(self, *args, **kwargs):
        super().__init__(max_length=50, *args, **kwargs)


class UserPasswordForm(forms.ModelForm):
    password1 = PasswordField()
    password2 = PasswordField()

    def clean(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                _('Passwords do not match'),
                code='different_passwords'
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class SignupForm(UserPasswordForm):

    class Meta:
        model = User
        fields = ['email']

    def clean(self):
        super().clean()
        password = self.cleaned_data.get('password1')
        if password:
            self.instance.email = self.cleaned_data.get('email')
            validate_password(password, self.instance)


class LoginForm(forms.Form):
    email = EmailField()
    password = PasswordField()

    def set_incorrect_email_or_password_error(self):
        self.add_error(None, _('Incorrect email or password'))


class RecoverAccountForm(forms.Form):
    email = EmailField()


class ResetPasswordForm(UserPasswordForm):

    class Meta:
        model = User
        fields = []

    def clean(self):
        super().clean()
        password = self.cleaned_data.get('password1')
        if password:
            validate_password(password, self.instance)
