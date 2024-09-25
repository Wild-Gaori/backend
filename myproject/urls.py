
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('account.urls')), # 로그인,회원가입
    path('masterpiece/', include('masterpiece.urls')),  # 명화 감상 앱
    path('imagegen/', include('imagegen.urls')), # 이미지 생성 앱 
]

# 개발 환경에서 미디어 파일 제공
#if settings.DEBUG:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
