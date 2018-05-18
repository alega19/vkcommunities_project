from django.db import models
from django.utils import timezone


class Community(models.Model):

    TYPE_PUBLIC_PAGE = 0
    TYPE_OPEN_GROUP = 1
    TYPE_CLOSED_GROUP = 2
    TYPE_PRIVATE_GROUP = 3
    _TYPE_CHOICES = (
        (TYPE_PUBLIC_PAGE, "Public page"),
        (TYPE_OPEN_GROUP, "Open group"),
        (TYPE_CLOSED_GROUP, "Closed group"),
        (TYPE_PRIVATE_GROUP, "Private group")
    )

    AGELIMIT_UNKNOWN = -1
    AGELIMIT_NONE = 0
    AGELIMIT_16 = 16
    AGELIMIT_18 = 18
    _AGELIMIT_CHOICES = (
        (AGELIMIT_UNKNOWN, 'Unknown'),
        (AGELIMIT_NONE, 'None'),
        (AGELIMIT_16, '16+'),
        (AGELIMIT_18, '18+')
    )

    vkid = models.PositiveIntegerField(primary_key=True)
    deactivated = models.BooleanField()
    ctype = models.SmallIntegerField(db_column='type', choices=_TYPE_CHOICES)
    verified = models.NullBooleanField()
    age_limit = models.SmallIntegerField(choices=_AGELIMIT_CHOICES, default=AGELIMIT_UNKNOWN)
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)
    followers = models.PositiveIntegerField(blank=True, null=True)
    status = models.TextField(blank=True)
    icon50url = models.TextField(blank=True)
    icon100url = models.TextField(blank=True)
    checked_at = models.DateTimeField(blank=True, null=True)
    posts_per_week = models.PositiveSmallIntegerField(blank=True, null=True)
    views_per_post = models.FloatField(blank=True, null=True)
    likes_per_view = models.FloatField(blank=True, null=True)
    growth_per_day = models.IntegerField(blank=True, null=True)
    growth_per_week = models.IntegerField(blank=True, null=True)


class CommunityHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    community = models.ForeignKey('Community', on_delete=models.CASCADE)
    checked_at = models.DateTimeField()
    followers = models.PositiveIntegerField()
