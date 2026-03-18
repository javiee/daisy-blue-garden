from rest_framework import serializers
from .models import GardenItem


class GardenItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GardenItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
