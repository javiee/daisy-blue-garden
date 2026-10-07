from django.test import TestCase
from apps.core.models import AppSetting


class AppSettingModelTest(TestCase):
    def test_current_creates_singleton_with_default_language(self):
        AppSetting.objects.all().delete()
        self.assertFalse(AppSetting.objects.exists())
        setting = AppSetting.current()
        self.assertEqual(setting.pk, 1)
        self.assertEqual(setting.language, 'en')

    def test_current_returns_existing_row(self):
        first = AppSetting.current()
        second = AppSetting.current()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(AppSetting.objects.count(), 1)

    def test_set_language_updates_singleton(self):
        AppSetting.set_language('es')
        setting = AppSetting.current()
        self.assertEqual(setting.language, 'es')
        self.assertEqual(AppSetting.objects.count(), 1)

    def test_get_language_returns_stored_value(self):
        AppSetting.set_language('es')
        self.assertEqual(AppSetting.get_language(), 'es')

    def test_gardener_prompt_defaults_to_empty(self):
        AppSetting.objects.all().delete()
        setting = AppSetting.current()
        self.assertEqual(setting.gardener_prompt, '')

    def test_get_gardener_prompt_returns_stored_value(self):
        setting = AppSetting.current()
        setting.gardener_prompt = 'You are a gardener in Málaga, Mediterranean climate.'
        setting.save(update_fields=['gardener_prompt'])
        self.assertEqual(
            AppSetting.get_gardener_prompt(),
            'You are a gardener in Málaga, Mediterranean climate.',
        )
