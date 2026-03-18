from django.contrib import admin
from .models import GardenItem


@admin.register(GardenItem)
class GardenItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'created_at', 'updated_at']
    list_filter = ['type']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
