import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_chat_id', models.CharField(max_length=100)),
                ('frequency', models.CharField(
                    choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
                    default='weekly',
                    max_length=20,
                )),
                ('days_before', models.IntegerField(default=3, help_text='Notify N days before event')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Notification Config',
                'verbose_name_plural': 'Notification Configs',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_message_id', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')],
                    default='pending',
                    max_length=20,
                )),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('acknowledged', models.BooleanField(default=False)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('next_occurrence_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('config', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='notifications.notificationconfig',
                )),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to='events.calendarevent',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
