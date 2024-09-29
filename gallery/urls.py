from django.urls import path
from . import views

urlpatterns = [
    path('museums/', views.museum_list_view, name='museum-list'),
    path('museums/<int:museum_id>/exhibitions/', views.exhibition_list_view, name='exhibition-list'),
]