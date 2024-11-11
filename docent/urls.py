# docent/urls.py

from django.urls import path
from .views import GetSelectedDocent,UpdateSelectedDocent

urlpatterns = [
    path('get-selected-docent/', GetSelectedDocent.as_view(), name='get_selected_docent'),
    path('update-selected-docent/', UpdateSelectedDocent.as_view(), name='update_selected_docent'),
]
