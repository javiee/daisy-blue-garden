from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


@api_view(['POST'])
def generate_care(request, item_id):
    """Manually trigger LLM care generation for a garden item."""
    from apps.garden.models import GardenItem
    from .tasks import generate_item_care_async

    try:
        GardenItem.objects.get(pk=item_id)
    except GardenItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    task = generate_item_care_async.delay(item_id)
    return Response({'task_id': task.id, 'status': 'queued'})


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
