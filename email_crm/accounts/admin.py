from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'position', 'phone')
    search_fields = ('user__username', 'user__email', 'company_name')
    list_filter = ('created_at',)
