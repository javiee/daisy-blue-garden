from rest_framework import serializers
from .models import PlantIdentification


class PlantIdentificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantIdentification
        fields = [
            'id', 'photo', 'status', 'error',
            'name', 'type', 'description', 'cares',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields
