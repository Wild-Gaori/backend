import os
from openai import OpenAI
from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from .models import ImageGeneration

@api_view(['POST'])
def generate_image(request):

    prompt = request.data.get("prompt")
    if not prompt:
        return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        client = OpenAI()

        # DALL·E 3 API 호출
        response = client.images.generate(
            prompt=prompt,
            n=1,  # 생성할 이미지 개수
            size="1024x1024"  # 이미지 크기
        )

        # 응답에서 이미지 URL 추출
        image_data = response.data[0]  # 첫 번째 이미지 데이터를 추출
        image_url = image_data.url  # 이미지 URL에 접근 

        # 이미지 생성 기록을 DB에 저장
        # user = request.user  # 현재 로그인한 사용자
        # 테스트용 임시 사용자 설정
        user, created = User.objects.get_or_create(username='test_user', defaults={'password': 'testpass'})
        image_generation = ImageGeneration.objects.create(user=user, image_url=image_url)

        return Response({"image_url": image_url}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def get_image_history(request):
    # user = request.user  # 현재 로그인한 사용자
    # 테스트용 임시 사용자 설정
    user, created = User.objects.get_or_create(username='test_user', defaults={'password': 'testpass'})
    
    # 사용자가 생성한 모든 이미지 조회
    images = ImageGeneration.objects.filter(user=user).order_by('-created_at')

    # 기록을 리스트로 변환
    history = []
    for image in images:
        history.append({
            'image_id': image.id,
            'image_url': image.image_url,
            'created_at': image.created_at,
        })

    return Response(history, status=status.HTTP_200_OK)