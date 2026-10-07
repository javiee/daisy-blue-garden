from rest_framework import serializers
from .models import AppSetting


class AppSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSetting
        fields = ['language', 'gardener_prompt', 'updated_at']
        read_only_fields = ['updated_at']
