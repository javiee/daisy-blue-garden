from django.db import migrations

def create_schedule(apps, schema_editor):
    Schedule = apps.get_model('django_q', 'Schedule')
    Schedule.objects.get_or_create(
        func='apps.notifications.tasks.check_and_send_notifications',
        defaults={
            'name': 'Check and send notifications',
            'schedule_type': 'H',   # H = hourly
            'repeats': -1,          # -1 means repeat forever
        }
    )

def remove_schedule(apps, schema_editor):
    Schedule = apps.get_model('django_q', 'Schedule')
    Schedule.objects.filter(
        func='apps.notifications.tasks.check_and_send_notifications'
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0001_initial'),
        ('django_q', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_schedule, remove_schedule),
    ]