from django.urls import path
from .views import random_artwork_view, artwork_chat_view, artwork_chat_history_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('random/', random_artwork_view, name='random_artwork'),  # 랜덤 명화 불러오기
    path('chat/', artwork_chat_view, name='chat'),  # GPT와 채팅
    path('chat/history/', artwork_chat_history_view, name='chat_history'),  # 채팅 기록 조회
]
