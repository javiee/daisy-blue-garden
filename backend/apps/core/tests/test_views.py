from rest_framework.test import APITestCase
from rest_framework import status
from apps.core.models import AppSetting


class AppSettingAPITest(APITestCase):
    def test_get_settings_returns_default(self):
        response = self.client.get('/api/v1/settings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['language'], 'en')
        self.assertEqual(response.data['gardener_prompt'], '')

    def test_patch_language(self):
        response = self.client.patch(
            '/api/v1/settings/', {'language': 'es'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['language'], 'es')
        self.assertEqual(AppSetting.get_language(), 'es')

    def test_put_language(self):
        response = self.client.put(
            '/api/v1/settings/', {'language': 'es'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AppSetting.get_language(), 'es')

    def test_patch_invalid_language_returns_400(self):
        response = self.client.patch(
            '/api/v1/settings/', {'language': 'fr'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AppSetting.get_language(), 'en')

    def test_patch_without_language_keeps_current(self):
        AppSetting.set_language('es')
        response = self.client.patch('/api/v1/settings/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AppSetting.get_language(), 'es')

    def test_patch_gardener_prompt(self):
        custom = 'You are a gardener in Málaga, Mediterranean climate.'
        response = self.client.patch(
            '/api/v1/settings/', {'gardener_prompt': custom}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['gardener_prompt'], custom)
        self.assertEqual(AppSetting.get_gardener_prompt(), custom)

    def test_patch_gardener_prompt_empty_resets_to_default(self):
        setting = AppSetting.current()
        setting.gardener_prompt = 'Custom persona.'
        setting.save(update_fields=['gardener_prompt'])
        response = self.client.patch(
            '/api/v1/settings/', {'gardener_prompt': ''}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['gardener_prompt'], '')
        self.assertEqual(AppSetting.get_gardener_prompt(), '')
