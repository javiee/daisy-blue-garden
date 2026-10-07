from datetime import timedelta

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from django_q.tasks import async_task
from .models import PlantIdentification
from .serializers import PlantIdentificationSerializer


@api_view(['POST'])
def generate_care(request, item_id):
    """Manually trigger LLM care generation for a garden item."""
    from apps.garden.models import GardenItem
    from .tasks import generate_item_care_async

    try:
        GardenItem.objects.get(pk=item_id)
    except GardenItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    task_id = async_task('apps.llm.tasks.generate_item_care_async', item_id)
    return Response({'task_id': task_id, 'status': 'queued'})


MAX_IDENTIFY_PHOTO_BYTES = 10 * 1024 * 1024  # 10 MB
ABANDONED_RECORD_AGE = timedelta(hours=1)


def _sweep_abandoned_records():
    """Delete identify records abandoned by the client, with their photo files.

    The frontend deletes records when results are consumed or fail, but a
    cancelled navigation can leave orphans behind; this lazy sweep runs on
    every new identify request and covers any client that forgets to clean up.
    """
    cutoff = timezone.now() - ABANDONED_RECORD_AGE
    for old in PlantIdentification.objects.filter(created_at__lt=cutoff):
        if old.photo:
            old.photo.delete(save=False)
        old.delete()


@api_view(['POST'])
def identify_plant(request):
    """Upload a photo, queue async vision identification. Returns the record."""
    photo = request.FILES.get('photo')
    if not photo:
        return Response({'error': 'photo is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not (photo.content_type or '').startswith('image/'):
        return Response({'error': 'Only image files are supported'}, status=status.HTTP_400_BAD_REQUEST)
    if photo.size > MAX_IDENTIFY_PHOTO_BYTES:
        return Response({'error': 'Photo must be smaller than 10 MB'}, status=status.HTTP_400_BAD_REQUEST)

    _sweep_abandoned_records()
    record = PlantIdentification.objects.create(photo=photo)
    async_task('apps.llm.tasks.identify_plant_async', record.pk)
    return Response(PlantIdentificationSerializer(record).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'DELETE'])
def identification_detail(request, pk):
    """Poll identification status, or delete the record (and its photo)."""
    try:
        record = PlantIdentification.objects.get(pk=pk)
    except PlantIdentification.DoesNotExist:
        return Response({'error': 'Identification not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        if record.photo:
            record.photo.delete(save=False)
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(PlantIdentificationSerializer(record).data)


@api_view(['GET'])
def list_providers(request):
    """List available LLM providers."""
    providers = [
        {'id': 'openai', 'name': 'OpenAI', 'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']},
        {'id': 'anthropic', 'name': 'Anthropic', 'models': ['claude-opus-4-6', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001']},
        {'id': 'ollama', 'name': 'Ollama (Local)', 'models': ['llama3.2', 'mistral', 'phi4']},
    ]
    current = settings.LLM_PROVIDER
    return Response({'providers': providers, 'current': current})
