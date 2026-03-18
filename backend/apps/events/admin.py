from django.contrib import admin
from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'item', 'date', 'event_type', 'recurrence']
    list_filter = ['event_type', 'recurrence']
    search_fields = ['title', 'item__name']
    date_hierarchy = 'date'
