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
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from openai import OpenAI
import os
from masterpiece.models import Artwork
from account.models import UserProfile

@api_view(['POST'])
def edit_image_with_dalle2(request):
    # 프론트엔드에서 전달된 데이터 추출
    prompt = request.data.get("prompt")  # 프롬프트 텍스트
    artwork_id = request.data.get("artwork_id")  # 편집할 작품의 ID
    mask_image = request.FILES.get("mask_image")  # 마스크 이미지 파일

    # 필수 데이터 검증
    if not prompt:
        return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not artwork_id:
        return Response({"error": "Artwork ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not mask_image:
        return Response({"error": "Mask image is required"}, status=status.HTTP_400_BAD_REQUEST)

    # artwork_id로 Artwork 객체 조회
    artwork = get_object_or_404(Artwork, id=artwork_id)
    original_image_path = os.path.join(settings.BASE_DIR, 'masterpiece', 'static', artwork.image_path)

    # 원본 이미지 파일 존재 여부 확인
    if not os.path.exists(original_image_path):
        return Response({"error": "Original image not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        client = OpenAI()

        # DALL-E 2 이미지 편집 요청
        with open(original_image_path, "rb") as original_image, mask_image as mask:
            response = client.images.edit(
                model="dall-e-2",
                image=original_image,
                mask=mask,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

        # 생성된 이미지 URL 추출
        image_url = response['data'][0]['url']

        # 응답 반환
        return Response({"edited_image_url": image_url}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#####

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from masterpiece.models import Artwork, Artist  # 필요한 모델 가져오기
from rest_framework.response import Response
from rest_framework import status
from masterpiece.models import Artwork, Artist  # 필요한 모델 가져오기
#from .models import User, ImageGeneration
from openai import OpenAI  # OpenAI 클라이언트 가져오기

@api_view(['POST'])
def generate_image_method(request):
    action = request.data.get("action")  # 요청에서 'action' 필드 추출
    prompt = request.data.get("prompt")
    artwork_id = request.data.get("artwork_id", None)  # 'change' 액션을 위한 artwork_id
    user_pk = request.data.get("user_pk")  # 사용자 pk 값

    # 디버깅을 위한 로그 추가
    print(f"Received artwork_id: {artwork_id}, user_pk: {user_pk}")  # 서버 콘솔에 artwork_id와 user_pk 출력

    if not action:
        return Response({"error": "Action is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if not prompt:
        return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = OpenAI()

        if action == 'experience':
            if not user_pk:
                return Response({"error": "User PK is required for 'experience' action"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = get_object_or_404(User, pk=user_pk)
            user_profile = get_object_or_404(UserProfile, user=user)
            
            # 'experience' 액션: 사용자 프로필 정보를 포함한 프롬프트 생성
            gender = user_profile.gender or ""
            clothing = user_profile.clothing or "반팔옷"
            hairstyle = user_profile.hairstyle or "짧은 머리"
            final_prompt = f"나는 {gender} 초등학생이고 {clothing} 옷을 입었고 머리는 {hairstyle}(이)야. {prompt}"  # 사용자 정보 포함한 프롬프트
            response = client.images.generate(
                model="dall-e-3",
                prompt=final_prompt,
                n=1,  # 생성할 이미지 개수
                size="1024x1024"  # 이미지 크기
            )
        elif action == 'change':
            if not artwork_id:
                return Response({"error": "Artwork ID is required for 'change' action"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 'change' 액션: artwork 정보를 기반으로 프롬프트 수정
            artwork = get_object_or_404(Artwork, id=artwork_id)
            artist_style = artwork.artist_fk.style  # artist_fk 필드에서 style 접근
            artwork_title = artwork.title
            final_prompt = f"{artist_style} 화풍으로 {artwork_title} 작품에서 {prompt}"  # 수정된 프롬프트
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=final_prompt,
                n=1,  # 생성할 이미지 개수
                size="1024x1024"  # 이미지 크기
            )
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        # 응답에서 이미지 URL 추출
        image_data = response.data[0]
        image_url = image_data.url

        # 응답 반환
        return Response({"image_url": image_url, "final_prompt": final_prompt}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#####



##logger = logging.getLogger(__name__)

@api_view(['POST'])
def generate_image(request):
    print(request.data) 
    
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
        # 테스트용 임시 사용자 설정
        user, created = User.objects.get_or_create(username='test_user', defaults={'password': 'testpass'})
        image_generation = ImageGeneration.objects.create(user=user, image_url=image_url)

        return Response({"image_url": image_url}, status=status.HTTP_200_OK)

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
