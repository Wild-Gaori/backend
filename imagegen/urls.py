from django.urls import path
from .views import generate_image, get_image_history

urlpatterns = [
    path('generate/', generate_image, name='generate_image'),
    path('history/', get_image_history, name='image_history'),
]
