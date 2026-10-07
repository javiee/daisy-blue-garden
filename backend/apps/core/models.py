from django.db import models


class AppSetting(models.Model):
    """Singleton row holding global application settings."""

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
    ]

    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    gardener_prompt = models.TextField(
        blank=True,
        default='',
        help_text='Custom gardener persona for AI generation. Empty = default expert.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AppSetting(language={self.language})"

    @classmethod
    def current(cls) -> 'AppSetting':
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    @classmethod
    def get_language(cls) -> str:
        return cls.current().language

    @classmethod
    def get_gardener_prompt(cls) -> str:
        return cls.current().gardener_prompt

    @classmethod
    def set_language(cls, language: str) -> 'AppSetting':
        instance = cls.current()
        instance.language = language
        instance.save(update_fields=['language', 'updated_at'])
        return instance
