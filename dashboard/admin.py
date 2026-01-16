from django.contrib import admin
from .models import Dashboard

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__phone')