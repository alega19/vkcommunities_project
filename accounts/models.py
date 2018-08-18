from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils import timezone

from .tasks import send_mail


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password):
        return self._create_user(email, password, is_staff=True, is_active=True)

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'

    def get_short_name(self):
        return self.email

    def get_full_name(self):
        return self.email

    def has_perm(self, *args, **kwargs):
        return True

    def has_module_perms(self, *args, **kwargs):
        return True

    def send_email(self, subject, message, fail_silently=False):
        return send_mail.delay(subject, message, None, [self.email], fail_silently=fail_silently)
