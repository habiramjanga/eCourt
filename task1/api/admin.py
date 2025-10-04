from django.contrib import admin
from .models import UserQueryLog

@admin.register(UserQueryLog)
class UserQueryLogAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'request_timestamp', 'status_code', 'ip_address')
    list_filter = ('endpoint', 'status_code', 'request_timestamp')
    search_fields = ('endpoint', 'request_data', 'response_data')
    date_hierarchy = 'request_timestamp'
    readonly_fields = ('request_timestamp', 'response_timestamp', 'ip_address', 'user_agent')
