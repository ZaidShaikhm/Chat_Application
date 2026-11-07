from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'is_online', 'email_notifications', 'last_seen')
    list_filter = ('is_online', 'email_notifications', 'last_seen')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
