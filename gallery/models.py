from django.db import models
from django.contrib.auth.models import User

# 미술관 정보 모델
class Museum(models.Model):
    name = models.CharField(max_length=255) # 미술관 이름
    museum_url = models.URLField()  # 홈페이지 링크

    def __str__(self):
        return self.name
    
# 전시 정보 모델
class Exhibition(models.Model):
    museum = models.ForeignKey(Museum, related_name='exhibitions', on_delete=models.CASCADE)
    title = models.CharField(max_length=255) # 전시 제목
    description = models.TextField() # 전시 소개
    start_date = models.DateField() # 시작일
    end_date = models.DateField() # 종료일
    location = models.TextField() # 전시실 위치

    def __str__(self):
        return self.title
    
# 전시에 대한 채팅 세션을 저장하는 모델
class ExhibitionChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exhibition = models.ForeignKey(Exhibition, on_delete=models.CASCADE) # 해당 채팅에서 사용된 전시
    created_at = models.DateTimeField(auto_now_add=True) # 채팅 세션 생성 시각
    
# 하나의 채팅 메시지 저장 모델 : 사용자 메시지나 GPT가 응답한 assistant 메시지를 저장
class ExhibitionMessage(models.Model):
    session = models.ForeignKey(ExhibitionChatSession, related_name='messages', on_delete=models.CASCADE) # 메세지 속한 채팅 세션 참조
    role = models.CharField(max_length=10)  # 메세지 주체 : 'user' 또는 'assistant'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."