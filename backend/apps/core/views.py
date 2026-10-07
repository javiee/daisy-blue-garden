from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import AppSetting
from .serializers import AppSettingSerializer


class AppSettingView(APIView):
    """Read/update the singleton app settings (GET, PUT, PATCH)."""

    def get(self, request):
        serializer = AppSettingSerializer(AppSetting.current())
        return Response(serializer.data)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)

    def _update(self, request):
        setting = AppSetting.current()
        serializer = AppSettingSerializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if 'language' in data:
            setting.language = data['language']
        if 'gardener_prompt' in data:
            setting.gardener_prompt = data['gardener_prompt']
        setting.save()
        setting.refresh_from_db()
        return Response(AppSettingSerializer(setting).data)
