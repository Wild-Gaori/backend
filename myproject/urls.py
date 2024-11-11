from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')), # 로그인,회원가입
    path('masterpiece/', include('masterpiece.urls')),  # 명화 감상 앱
    path('imagegen/', include('imagegen.urls')), # 이미지 생성 앱 
] 
