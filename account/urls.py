from django.contrib import admin
from django.urls import path, include
from .views import LoginView, SignupView, UpdateUserProfileView
from . import views



urlpatterns = [
    path('', LoginView.as_view(), name='login'), #로그인
    path('signup/', SignupView.as_view(), name='signup'), #회원가입
    path('update-profile/', UpdateUserProfileView.as_view(), name='update_profile'),
]  