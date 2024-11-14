from django.db import models
from django.contrib.auth.models import User
from masterpiece.models import ArtworkChatSession

# 이미지 생성 기록 저장
class ImageGeneration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자와 연결
    session = models.ForeignKey(ArtworkChatSession, on_delete=models.CASCADE, null=True, blank=True)  # 채팅 세션과 연결 (null 허용)
    prompt = models.TextField(null=True, blank=True)  # 이미지 생성에 사용된 프롬프트 (null 허용)
    image_png = models.ImageField(upload_to='generated_images/', null=True, blank=True)  # 생성된 이미지의 PNG 파일 (null 허용)
    image_url = models.URLField()  # 생성된 이미지의 URL
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각

    def __str__(self):
        return f"Image generated for {self.user.username} in session {self.session.id if self.session else 'N/A'}"
