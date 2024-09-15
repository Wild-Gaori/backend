import os
from openai import OpenAI
from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

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

        return Response({"image_url": image_url}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)