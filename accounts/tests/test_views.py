from urllib.parse import urlparse
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.core import mail

from ..models import User, send_mail


def find_links(s):
    words = s.split()
    return [w for w in words if w.startswith('http')]


class SignupTest(TestCase):

    VALID_EMAIL = 'superuser42@example42.com'
    VALID_PASSWORD = 'itismypassword42'

    def test_registration(self):
        with patch('accounts.models.send_mail.delay', side_effect=send_mail):
            resp = self.client.post(reverse('accounts:signup'), {
                'email': self.VALID_EMAIL,
                'password1': self.VALID_PASSWORD,
                'password2': self.VALID_PASSWORD
            })
        self.assertRedirects(resp, reverse('accounts:confirm_email_sent'))

        user = User.objects.get(email=self.VALID_EMAIL)
        self.assertFalse(user.is_active)

        self.assertEqual(len(mail.outbox), 1)
        links = find_links(str(mail.outbox[0].message()))
        self.assertEqual(len(links), 1)

        path = urlparse(links[0]).path
        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('accounts/activated.html')

        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 404)

        user = User.objects.get(email=self.VALID_EMAIL)
        self.assertTrue(user.is_active)

    def test_registration_when_inactive_account_with_that_email_exists(self):
        User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD)
        with patch('accounts.models.send_mail.delay', side_effect=send_mail):
            resp = self.client.post(reverse('accounts:signup'), {
                'email': self.VALID_EMAIL,
                'password1': self.VALID_PASSWORD,
                'password2': self.VALID_PASSWORD
            })
        self.assertRedirects(resp, reverse('accounts:confirm_email_sent'))

        user = User.objects.get(email=self.VALID_EMAIL)
        self.assertFalse(user.is_active)

        self.assertEqual(len(mail.outbox), 1)
        links = find_links(str(mail.outbox[0].message()))
        self.assertEqual(len(links), 1)

        path = urlparse(links[0]).path
        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('accounts/activated.html')

        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 404)

        user = User.objects.get(email=self.VALID_EMAIL)
        self.assertTrue(user.is_active)

    def test_registration_when_active_account_with_that_email_exists(self):
        User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD, is_active=True)
        resp = self.client.post(reverse('accounts:signup'), {
            'email': self.VALID_EMAIL,
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        })
        self.assertRedirects(resp, reverse('accounts:confirm_email_sent'))

        user = User.objects.get(email=self.VALID_EMAIL)
        self.assertTrue(user.is_active)

        self.assertEqual(len(mail.outbox), 0)


class LoginTest(TestCase):

    VALID_EMAIL = 'superuser42@example42.com'
    VALID_PASSWORD = 'itismypassword42'

    def test_login(self):
        User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD, is_active=True)
        resp = self.client.post(reverse('accounts:login'), {
            'email': self.VALID_EMAIL,
            'password': self.VALID_PASSWORD
        }, follow=True)
        self.assertRedirects(resp, reverse('communities:community_list'))
        self.assertEqual(resp.context['user'].email, self.VALID_EMAIL)

    def test_inactive_user_is_rejected(self):
        User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD)
        resp = self.client.post(reverse('accounts:login'), {
            'email': self.VALID_EMAIL,
            'password': self.VALID_PASSWORD
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['user'].is_authenticated)
        self.assertTemplateUsed(resp, 'accounts/login.html')

    def test_redirect_param_next_after_successful_auth(self):
        User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD, is_active=True)
        resp = self.client.post(reverse('accounts:login'), {
            'email': self.VALID_EMAIL,
            'password': self.VALID_PASSWORD,
            'next': '/page42'
        })
        self.assertRedirects(resp, '/page42', fetch_redirect_response=False)


class LogoutTest(TestCase):

    VALID_EMAIL = 'superuser42@example42.com'
    VALID_PASSWORD = 'itismypassword42'

    def test_logout(self):
        User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD, is_active=True)
        ok = self.client.login(email=self.VALID_EMAIL, password=self.VALID_PASSWORD)
        self.assertTrue(ok)
        resp = self.client.post(reverse('accounts:logout'), follow=True)
        self.assertFalse(resp.context['user'].is_authenticated)
        self.assertRedirects(resp, reverse('accounts:login'))


class RecoverAccountTest(TestCase):

    VALID_EMAIL = 'superuser42@example42.com'
    VALID_PASSWORD = 'itismypassword42'

    def test_recover(self):
        User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD, is_active=True)
        with patch('accounts.models.send_mail.delay', side_effect=send_mail):
            resp = self.client.post(reverse('accounts:recover'), {'email': self.VALID_EMAIL})
        self.assertRedirects(resp, reverse('accounts:recovery_email_sent'))

        self.assertEqual(len(mail.outbox), 1)
        links = find_links(str(mail.outbox[0].message()))
        self.assertEqual(len(links), 1)

        path = urlparse(links[0]).path
        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/reset_password.html')

        resp = self.client.post(path, {
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD + '!'
        })
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(path, {
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        })
        self.assertRedirects(resp, reverse('accounts:login'))

        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 404)

    def test_recover_account_with_unknown_email(self):
        resp = self.client.post(reverse('accounts:recover'), {'email': self.VALID_EMAIL})
        self.assertRedirects(resp, reverse('accounts:recovery_email_sent'))

        self.assertEqual(len(mail.outbox), 0)
