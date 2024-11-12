from django.contrib import admin
from django.urls import path, include
from .views import LoginView, SignupView, UpdateUserProfileView, GetUserProfileView
from . import views



urlpatterns = [
    path('login', LoginView.as_view(), name='login'), #로그인
    path('signup/', SignupView.as_view(), name='signup'), #회원가입
    path('update-profile/', UpdateUserProfileView.as_view(), name='update_profile'), #사용자 정보 생성, 수정
    path('get-user-profile/', GetUserProfileView.as_view(), name='get_user_profile'), #기존 사용자 정보 반환
]  
