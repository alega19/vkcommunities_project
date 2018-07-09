from django.test import TestCase, SimpleTestCase

from ..forms import SignupForm, ResetPasswordForm
from ..models import User


class SignupFormTest(TestCase):

    VALID_EMAIL = 'superuser42@example42.com'
    VALID_PASSWORD = 'itismypassword42'
    VALID_BUT_SIMILAR_TO_EMAIL_PASSWORDS = [
        VALID_EMAIL,
        VALID_EMAIL.replace('@', ''),
        *VALID_EMAIL.rsplit('@', 1)
    ]

    def test_valid_data(self):
        data = {
            'email': self.VALID_EMAIL,
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        }
        form = SignupForm(data)
        self.assertTrue(form.is_valid())

        another_email = 'test@test.com'
        for password in self.VALID_BUT_SIMILAR_TO_EMAIL_PASSWORDS:
            valid_data = {
                'email': another_email,
                'password1': password,
                'password2': password
            }
            form = SignupForm(valid_data)
            self.assertTrue(
                form.is_valid(),
                'password "{}" must be valid'.format(password)
            )

    def test_invalid_email(self):
        data = {
            'email': 'admin.example.com',
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        }
        form = SignupForm(data)
        self.assertFalse(form.is_valid())

        data = {
            'email': '@example.com',
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        }
        form = SignupForm(data)
        self.assertFalse(form.is_valid())

        data = {
            'email': 'admin@',
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        }
        form = SignupForm(data)
        self.assertFalse(form.is_valid())

    def test_max_length_of_email(self):
        valid_data = {
            'email': 'a'*242 + '@example.com',  # 254 characters
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        }
        form = SignupForm(valid_data)
        r = form.is_valid()
        print(form.errors)
        self.assertTrue(r)

        invalid_data = {
            'email': 'a'*243 + '@example.com',  # 255 characters
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        }
        form = SignupForm(invalid_data)
        self.assertFalse(form.is_valid())

    def test_max_length_of_password(self):
        password = '1?' + 'a'*48  # 50 characters
        valid_data = {
            'email': self.VALID_EMAIL,
            'password1': password,
            'password2': password
        }
        form = SignupForm(valid_data)
        self.assertTrue(form.is_valid())

        password = '1?' + 'a'*49  # 51 characters
        invalid_data = {
            'email': self.VALID_EMAIL,
            'password1': password,
            'password2': password
        }
        form = SignupForm(invalid_data)
        self.assertFalse(form.is_valid())

    def test_password_similar_to_email(self):
        for password in self.VALID_BUT_SIMILAR_TO_EMAIL_PASSWORDS:
            invalid_data = {
                'email': self.VALID_EMAIL,
                'password1': password,
                'password2': password
            }
            form = SignupForm(invalid_data)
            self.assertFalse(
                form.is_valid(),
                'password "{}" is similar to email "{}"'.format(password, self.VALID_EMAIL)
            )

    def test_too_weak_password(self):
        weak_passwords = [
            '0123456789',  # only digits
            'password',  # dictionary of top passwords must be used
            'a!@42?d'  # too short
        ]
        for password in weak_passwords:
            invalid_data = {
                'email': self.VALID_EMAIL,
                'password1': password,
                'password2': password
            }
            form = SignupForm(invalid_data)
            self.assertFalse(form.is_valid(), password + ' is a weak password')

    def test_existing_email(self):
        User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD)
        data = {
            'email': self.VALID_EMAIL,
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        }
        form = SignupForm(data)
        self.assertTrue(
            form.is_valid(),
            'no one should know about users'
        )


class ResetPasswordFormTest(SimpleTestCase):

    VALID_EMAIL = 'superuser42@example42.com'
    VALID_PASSWORD = 'itismypassword42'
    VALID_BUT_SIMILAR_TO_EMAIL_PASSWORDS = [
        VALID_EMAIL,
        VALID_EMAIL.replace('@', ''),
        *VALID_EMAIL.rsplit('@', 1)
    ]

    def test_valid_data(self):
        user = User(email=self.VALID_EMAIL)
        data = {
            'password1': self.VALID_PASSWORD,
            'password2': self.VALID_PASSWORD
        }
        form = ResetPasswordForm(data, instance=user)
        self.assertTrue(form.is_valid())

        another_email = 'test@test.com'
        user = User(email=another_email)
        for password in self.VALID_BUT_SIMILAR_TO_EMAIL_PASSWORDS:
            valid_data = {
                'password1': password,
                'password2': password
            }
            form = ResetPasswordForm(valid_data, instance=user)
            self.assertTrue(
                form.is_valid(),
                'password "{}" must be valid'.format(password)
            )

    def test_max_length_of_password(self):
        user = User(email=self.VALID_EMAIL)
        password = '1?' + 'a'*48  # 50 characters
        valid_data = {
            'password1': password,
            'password2': password
        }
        form = ResetPasswordForm(valid_data, instance=user)
        self.assertTrue(form.is_valid())

        password = '1?' + 'a'*49  # 51 characters
        invalid_data = {
            'password1': password,
            'password2': password
        }
        form = ResetPasswordForm(invalid_data, instance=user)
        self.assertFalse(form.is_valid())

    def test_password_similar_to_email(self):
        user = User(email=self.VALID_EMAIL)
        for password in self.VALID_BUT_SIMILAR_TO_EMAIL_PASSWORDS:
            invalid_data = {
                'password1': password,
                'password2': password
            }
            form = ResetPasswordForm(invalid_data, instance=user)
            self.assertFalse(
                form.is_valid(),
                'password "{}" is similar to email "{}"'.format(password, self.VALID_EMAIL)
            )

    def test_too_weak_password(self):
        user = User(email=self.VALID_EMAIL)
        weak_passwords = [
            '0123456789',  # only digits
            'password',  # dictionary of top passwords must be used
            'a!@42?d'  # too short
        ]
        for password in weak_passwords:
            invalid_data = {
                'password1': password,
                'password2': password
            }
            form = ResetPasswordForm(invalid_data, instance=user)
            self.assertFalse(form.is_valid(), password + ' is a weak password')
