from django.contrib import admin
from django.urls import path, include
from . import views



urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('', views.login, name='login'),
    path('home/', views.home, name='home'),

    path('logout/', views.logout, name='logout'),
    path('letter/', views.letter, name='letter'),
    path('enteruserinfo/', views.enteruserinfo, name='enteruserinfo'),

    #path('tutorial/', views.tutorial, name='tutorial'),
    path('auth/', include('djoser.urls')),  # Djoser 기본 URL
    path('auth/', include('djoser.urls.authtoken')),  # 토큰 기반 인증 URL
    
]  