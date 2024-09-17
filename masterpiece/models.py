from django.db import models
from django.contrib.auth.models import User

# 명화 정보를 저장하는 모델
class Artwork(models.Model):
    title = models.CharField(max_length=255) # 제목
    artist = models.CharField(max_length=255) # 작가
    year = models.IntegerField() # 제작연도
    description= models.TextField() # 작품 설명
    hook = models.TextField() # 짧은 설명
    image_url = models.URLField()  # 이미지 링크
    #image = models.ImageField(upload_to='artworks/')  # 이미지 파일 저장

    def __str__(self):
        return self.title

# 채팅 세션을 저장하는 모델
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)  # 해당 채팅에서 사용된 명화
    created_at = models.DateTimeField(auto_now_add=True) # 채팅 세션 생성 시각

# 하나의 채팅 메시지 저장 모델 : 사용자 메시지나 GPT가 응답한 assistant 메시지를 저장
class Message(models.Model):
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE) # 메세지 속한 채팅 세션 참조
    role = models.CharField(max_length=10)  # 메세지 주체 : 'user' 또는 'assistant'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."