from django.urls import path
from . import views

urlpatterns = [
    path('generate-care/<int:item_id>/', views.generate_care, name='generate-care'),
    path('providers/', views.list_providers, name='list-providers'),
]
