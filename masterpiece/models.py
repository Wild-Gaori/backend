from django.db import models
from django.contrib.auth.models import User
from docent.models import Docent  # Docent 모델을 참조하기 위해 import

# 작가 정보를 저장하는 모델
class Artist(models.Model):
    name = models.CharField(max_length=255)
    style = models.CharField(max_length=255)

    def __str__(self):
        return self.name
        
# 명화 정보를 저장하는 모델
class Artwork(models.Model):
    title = models.CharField(max_length=255) # 제목
    artist = models.CharField(max_length=255) # 작가
    artist_fk= models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='artwork', default=1)  # 작가
    year = models.IntegerField() # 제작연도
    description= models.TextField() # 작품 설명
    hook = models.TextField() # 짧은 설명
    rag_path = models.CharField(max_length=255, default="")  # rag 활용할 텍스트 파일 경로 저장
    image_url = models.URLField(blank=True, null=True) # 이미지 url 입력
    image_path = models.CharField(max_length=255, default="")  # 이미지 파일 저장

    def __str__(self):
        return self.title
    
# 채팅 세션을 저장하는 모델 (감상했던 명화 별로 관리)
class ArtworkChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)  # 해당 채팅에서 사용된 명화
    created_at = models.DateTimeField(auto_now_add=True)  # 채팅 세션 생성 시각
    chat_history = models.JSONField(default=list)  # 대화 기록을 JSON 형식으로 저장
    docent_at_chat = models.ForeignKey(Docent, on_delete=models.SET_DEFAULT, default=1)  # 대화 당시의 도슨트 정보

    def __str__(self):
        return f"Session with {self.user.username} on '{self.artwork.title}'"
    
class ChatSession(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),           # 생성 대기 중
        #('IN_PROGRESS', 'In Progress'),   # 생성 중
        ('COMPLETED', 'Completed'),       # 생성 완료
        ('FAILED', 'Failed')              # 생성 실패
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 사용자
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)  # 해당 채팅에서 사용된 명화
    created_at = models.DateTimeField(auto_now_add=True)  # 채팅 세션 생성 시각
    chat_history = models.JSONField(default=list)  # 대화 기록을 JSON 형식으로 저장
    docent_at_chat = models.ForeignKey(Docent, on_delete=models.SET_DEFAULT, default=1)  # 대화 당시의 도슨트 정보
    imggen_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')  # 그림 생성 상태

    def __str__(self):
        return f"Session with {self.user.username} on '{self.artwork.title}'"
