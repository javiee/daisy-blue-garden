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
    # Null = general garden task (no specific plant/tree), shown in the Tareas section.
    item = models.ForeignKey(
        'garden.GardenItem',
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='once')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='other')
    is_manual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    # Whether the pattern continues in following years. Default True: a
    # 'once' event repeats on the same date each year, and a weekly/monthly
    # series repeats its start->end window each year.
    repeats_yearly = models.BooleanField(default=True)
    parent_event = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='occurrences',
    )
    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} - {self.date}"
