from django.test import TestCase

from ..models import User


class UserTest(TestCase):

    VALID_EMAIL = 'superuser42@example42.com'
    VALID_PASSWORD = 'itismypassword42'

    def test_create_user(self):
        user = User.objects.create_user(self.VALID_EMAIL, self.VALID_PASSWORD)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active)

    def test_create_speruser(self):
        user = User.objects.create_superuser(self.VALID_EMAIL, self.VALID_PASSWORD)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)
