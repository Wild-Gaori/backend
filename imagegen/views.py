import os
from openai import OpenAI
from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import ImageGeneration
from .serializers import ImageGenerationSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
def generate_image(request):
    # 요청 데이터를 serializer에 전달하여 유효성 검사
    serializer = ImageGenerationSerializer(data=request.data)

    if not serializer.is_valid():
        # 유효하지 않은 경우 400 Bad Request와 오류 메시지 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST, format='json')

    # 유효한 경우 prompt 데이터를 추출
    prompt = serializer.validated_data['prompt']
    
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

        # 이미지 생성 기록  DB에 저장
        #테스트 사용자
        user, created = User.objects.get_or_create(username='test', defaults={'password': 'test'})

        image_generation = ImageGeneration.objects.create(user=user, image_url=image_url)

        return Response({"image_url": image_url}, status=status.HTTP_200_OK, format='json')

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def get_image_history(request):
    
    #테스트 사용자
    user, created = User.objects.get_or_create(username='test', defaults={'password': 'test'})
    
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
