from datetime import date, timedelta
from django.db import models
from django.utils import timezone


class NotificationConfig(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    telegram_chat_id = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    days_before = models.IntegerField(default=3, help_text="Notify N days before event")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Notification Config'
        verbose_name_plural = 'Notification Configs'

    def __str__(self):
        return f"Config for chat {self.telegram_chat_id} ({self.frequency})"


class Notification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    event = models.ForeignKey(
        'events.CalendarEvent',
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    config = models.ForeignKey(
        NotificationConfig,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notifications',
    )
    telegram_message_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    next_occurrence_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.event.title} ({self.status})"

    def acknowledge(self):
        self.acknowledged = True
        self.acknowledged_at = timezone.now()
        self.next_occurrence_date = self._calculate_next_occurrence()
        self.save()

    def _calculate_next_occurrence(self) -> date | None:
        today = date.today()
        recurrence = self.event.recurrence
        if recurrence == 'once':
            return None
        elif recurrence == 'weekly':
            return today + timedelta(weeks=1)
        elif recurrence == 'monthly':
            month = today.month + 1
            year = today.year
            if month > 12:
                month = 1
                year += 1
            return today.replace(year=year, month=month)
        elif recurrence == 'yearly':
            return today.replace(year=today.year + 1)
        return None
