from django.db import models
from django.db.models.aggregates import Aggregate


class VkAccount(models.Model):
    phone = models.CharField(max_length=16, blank=True, null=True, unique=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    password = models.TextField()
    api_token = models.CharField(max_length=85, blank=True, null=True, unique=True)
    enabled = models.BooleanField(default=True)
    note = models.TextField(blank=True)


class Median(Aggregate):
    function = 'PERCENTILE_CONT'
    template = '%(function)s(0.5) WITHIN GROUP (ORDER BY %(expressions)s)'
