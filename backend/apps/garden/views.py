from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import GardenItem
from .serializers import GardenItemSerializer


class GardenItemViewSet(viewsets.ModelViewSet):
    queryset = GardenItem.objects.all()
    serializer_class = GardenItemSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    search_fields = ['name', 'type', 'description']
    ordering_fields = ['name', 'created_at', 'type']
    filterset_fields = ['type']
