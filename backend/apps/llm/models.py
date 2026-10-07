from django.db import models


class PlantIdentification(models.Model):
    """A photo sent to the LLM for plant identification.

    Created by the identify endpoint (status=pending); the async task
    fills name/type/description/cares on success or error on failure.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
    ]
    TYPE_CHOICES = [
        ('plant', 'Plant'),
        ('tree', 'Tree'),
        ('shrub', 'Shrub'),
        ('other', 'Other'),
    ]
    photo = models.ImageField(upload_to='identify/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error = models.TextField(blank=True)
    name = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True)
    description = models.TextField(blank=True)
    cares = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Identification {self.pk} ({self.status})"
