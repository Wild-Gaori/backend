from django.db import models
from django.contrib.auth.models import User
from docent.models import Docent

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=100, blank=True, null=True)
    birthdate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    clothing = models.CharField(max_length=100, blank=True, null=True)
    hairstyle = models.CharField(max_length=100, blank=True, null=True)
    selected_docent = models.ForeignKey(Docent, on_delete=models.SET_DEFAULT, default=1, related_name='user_profiles')

    def __str__(self):
        return self.nickname
