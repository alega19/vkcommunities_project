from django.contrib import admin

from .models import Community


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = (
        'vkid', 'ctype', 'verified', 'name', 'followers', 'age_limit',
        'deactivated', 'description', 'status', 'checked_at')
    list_filter = ('ctype', 'verified', 'deactivated', 'age_limit')
    ordering = ('vkid',)
