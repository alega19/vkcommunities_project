from django.contrib import admin

from .models import VkAccount


@admin.register(VkAccount)
class VkAccountAdmin(admin.ModelAdmin):
    list_display = ('phone', 'email', 'password', 'api_token', 'enabled', 'note')
    ordering = ('phone', 'email')
