from django.conf import settings
from django.views.decorators.http import require_http_methods, require_GET
from django.views.generic import View
from django.urls import reverse
from django.utils.http import is_safe_url, urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import redirect, render, render_to_response, get_object_or_404
from django.contrib import auth
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.template.loader import render_to_string
from django.http import Http404

from .models import User
from .forms import LoginForm, SignupForm, RecoverAccountForm, ResetPasswordForm


@require_http_methods(['GET', 'POST'])
def signup(req):
    form = SignupForm(req.POST or None)
    if form.is_valid():
        try:
            user = User.objects.get(email=form.cleaned_data['email'])
            if not user.is_active:
                user.set_password(form.cleaned_data['password1'])
                user.save()
        except User.DoesNotExist:
            user = form.save()

        if not user.is_active:
            uidb64 = urlsafe_base64_encode(user.email.encode('utf-8'))
            token = token_generator.make_token(user)
            url = req.scheme + '://' + req.get_host() + reverse('accounts:activate', args=[uidb64, token])
            message = render_to_string('accounts/confirm_email.txt', {'url': url})
            user.send_email('Activate your account', message, fail_silently=True)

        return redirect(reverse('accounts:confirm_email_sent'))
    return render(req, 'accounts/signup.html', {'form': form})


@require_GET
def activate(req, uidb64, token):
    try:
        email = urlsafe_base64_decode(uidb64).decode('utf-8')
    except ValueError:
        raise Http404()
    user = get_object_or_404(User, email=email, is_active=False)
    if not token_generator.check_token(user, token):
        raise Http404()
    user.is_active = True
    user.save()
    return render_to_response('accounts/activated.html')


@require_http_methods(['GET', 'POST'])
def login(req):
    next_url = req.GET.get('next') or req.POST.get('next')
    if not is_safe_url(next_url):
        next_url = reverse(settings.LOGIN_REDIRECT_URL)
    form = LoginForm(req.POST or None)
    if form.is_valid():
        user = auth.authenticate(
            req,
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password']
        )
        if user is not None:
            auth.login(req, user)
            return redirect(next_url)
        else:
            form.set_incorrect_email_or_password_error()
    return render(req, 'accounts/login.html', {'form': form, 'next_url': next_url})


class LogoutView(View):

    def post(self, req):
        auth.logout(req)
        return redirect(settings.LOGOUT_REDIRECT_URL)


@require_http_methods(['GET', 'POST'])
def recover(req):
    form = RecoverAccountForm(req.POST or None)
    if form.is_valid():
        try:
            user = User.objects.get(email=form.cleaned_data['email'], is_active=True)
        except User.DoesNotExist:
            pass
        else:
            uidb64 = urlsafe_base64_encode(user.email.encode('utf-8'))
            token = token_generator.make_token(user)
            url = req.scheme + '://' + req.get_host() + reverse('accounts:reset_password', args=[uidb64, token])
            message = render_to_string('accounts/recovery_email.txt', {'url': url})
            user.send_email('Recover your account', message, fail_silently=True)
        return redirect(reverse('accounts:recovery_email_sent'))
    return render(req, 'accounts/recover.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def reset_password(req, uidb64, token):
    try:
        email = urlsafe_base64_decode(uidb64).decode('utf-8')
    except ValueError:
        raise Http404()
    user = get_object_or_404(User, email=email, is_active=True)
    if not token_generator.check_token(user, token):
        raise Http404()

    form = ResetPasswordForm(req.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect(reverse('accounts:login'))
    return render(req, 'accounts/reset_password.html', {'form': form})
