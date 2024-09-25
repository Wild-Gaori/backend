from django.contrib import admin
from django.urls import path, include
from .views import LoginView, SignupView, UserProfileUpdateView
from . import views



urlpatterns = [
    path('', LoginView.as_view(), name='login'), #로그인
    path('signup/', SignupView.as_view(), name='signup'), #회원가입
    path('update-userprofile/', UserProfileUpdateView.as_view(), name='update-userprofile'),
    path('auth/', include('djoser.urls')),  # Djoser 기본 URL
    
]  