from django.urls import path
from . import views

urlpatterns = [
    path('generate-care/<int:item_id>/', views.generate_care, name='generate-care'),
    path('identify/', views.identify_plant, name='identify-plant'),
    path('identify/<int:pk>/', views.identification_detail, name='identification-detail'),
    path('providers/', views.list_providers, name='list-providers'),
]
