from django.urls import path
from .views import random_artwork_view, artwork_chat_view, artwork_chat_history_view, copy_artwork_chat_session
from .views import completed_artworks_for_user, create_artwork_chat_session_view, get_gallery_artworks_list
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('random/', random_artwork_view, name='random_artwork'),  # 랜덤 명화 불러오기
    path('chat/', artwork_chat_view, name='chat'),  # GPT와 채팅
    path('chat/history/', artwork_chat_history_view, name='chat_history'),  # 채팅 기록 조회
    path('chat/copy_session/', copy_artwork_chat_session, name='copy_artwork_chat_session'),  # 채팅 세션 복사

    path('completed/', completed_artworks_for_user, name='completed_artworks_for_user'),  # 전시 작품 감상 여부
    path('gallery/create_session/', create_artwork_chat_session_view, name='create_artwork_chat_session_view'),  # 미술관 전시 작품 채팅
    path('gallery/list/', get_gallery_artworks_list, name='get_gallery_artworks_list'),  # 미술관 작품 정보 불러오기
]
