from django.contrib import admin
from .models import Dispute, DisputeComment


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['id', 'contract', 'raised_by', 'reason', 'status', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['contract__job__title', 'raised_by__email', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(DisputeComment)
class DisputeCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'dispute', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__email', 'content']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
