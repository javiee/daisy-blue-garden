from django.db import migrations


def create_default(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    if not AppSetting.objects.exists():
        AppSetting.objects.create(pk=1, language='en')


def remove_default(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSetting.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default, remove_default),
    ]
