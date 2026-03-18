from rest_framework import serializers
from .models import CalendarEvent
from apps.garden.serializers import GardenItemSerializer


class CalendarEventSerializer(serializers.ModelSerializer):
    item_detail = GardenItemSerializer(source='item', read_only=True)

    class Meta:
        model = CalendarEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
