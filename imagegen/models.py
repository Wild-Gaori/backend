from django.db import models
from django.contrib.auth.models import User

# 이미지 생성 기록 저장
class ImageGeneration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자와 연결
    image_url = models.URLField()  # 생성된 이미지의 URL
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각
