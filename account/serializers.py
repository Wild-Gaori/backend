from rest_framework import serializers
from account.models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['nickname', 'birthdate', 'gender', 'clothing', 'hairstyle']
