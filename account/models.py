from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=100, blank=True, null=True)
    birthdate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    clothing = models.CharField(max_length=100, blank=True, null=True)
    hairstyle = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nickname
