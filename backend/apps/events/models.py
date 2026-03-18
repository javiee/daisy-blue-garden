from django.db import models


class CalendarEvent(models.Model):
    RECURRENCE_CHOICES = [
        ('once', 'Once'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    EVENT_TYPE_CHOICES = [
        ('watering', 'Watering'),
        ('fertilizing', 'Fertilizing'),
        ('pruning', 'Pruning'),
        ('other', 'Other'),
    ]
    item = models.ForeignKey(
        'garden.GardenItem',
        on_delete=models.CASCADE,
        related_name='events',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='once')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='other')
    is_manual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} - {self.date}"
