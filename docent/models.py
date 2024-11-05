from django.db import models

class Docent(models.Model):
    docent_prompt = models.TextField()  # 도슨트 대화 프롬프트
    docent_intro = models.TextField()   # 도슨트 소개

    def __str__(self):
        return f"Docent {self.id}"
