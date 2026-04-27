from django.db import migrations

def create_schedule(apps, schema_editor):
    Schedule = apps.get_model('django_q', 'Schedule')
    Schedule.objects.get_or_create(
        func='apps.events.scheduler.expand_all_recurring_events',
        defaults={
            'name': 'Expand recurring calendar events',
            'schedule_type': 'D',   # D = daily
            'repeats': -1,
        }
    )

def remove_schedule(apps, schema_editor):
    Schedule = apps.get_model('django_q', 'Schedule')
    Schedule.objects.filter(
        func='apps.events.scheduler.expand_all_recurring_events'
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('events', '0002_calendarevent_is_manual'),
        ('django_q', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_schedule, remove_schedule),
    ]