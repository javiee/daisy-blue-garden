from django.apps import AppConfig


class GardenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.garden'
    label = 'garden'

    def ready(self):
        import apps.garden.signals  # noqa
