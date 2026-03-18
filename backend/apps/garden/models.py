from django.db import models


class GardenItem(models.Model):
    TYPE_CHOICES = [
        ('plant', 'Plant'),
        ('tree', 'Tree'),
        ('shrub', 'Shrub'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='plant')
    description = models.TextField(blank=True)
    cares = models.TextField(blank=True)
    photo = models.ImageField(upload_to='garden/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.type})"
