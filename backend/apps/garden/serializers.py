from rest_framework import serializers
from .models import GardenItem
from .images import optimize_image_file


class GardenItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GardenItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_photo(self, photo):
        """Optimize uploads so phone photos are stored small (see images.py)."""
        return optimize_image_file(photo)
