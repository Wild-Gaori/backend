from django.urls import path
from .views import get_image_history,generate_image_method,edit_image_with_dalle2

urlpatterns = [
    path('history/', get_image_history, name='image_history'),
    path('generate/', generate_image_method, name='generate_image_method'), #경험,상상
    path('generate/edit/', edit_image_with_dalle2, name='edit_image_with_dalle2'),
    ]
