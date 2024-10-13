from django.urls import path
from .views import generate_image, get_image_history,generate_image_method

urlpatterns = [
    path('generate/method/', generate_image, name='generate_image'),
    path('history/', get_image_history, name='image_history'),
    path('generate/', generate_image_method, name='generate_image_method'),
    path('generate/edit/', edit_image_with_dalle2, name='edit_image_with_dalle2'),
]
