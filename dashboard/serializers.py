from rest_framework.serializers import ModelSerializer

from .models import Dashboard


class DashboardSerializer(ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ['preferences', 'cached_metrics', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']