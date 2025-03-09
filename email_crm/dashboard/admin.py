from django.contrib import admin
from .models import Activity

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'timestamp')
    search_fields = ('user__username', 'activity_type', 'description')
    list_filter = ('timestamp', 'activity_type')
