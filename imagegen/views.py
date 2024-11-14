import os
import io
import base64
import logging
import requests
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from PIL import Image
from openai import OpenAI
from .models import ImageGeneration
from .serializers import ImageGenerationSerializer
from masterpiece.models import Artwork, Artist, ArtworkChatSession  # 필요한 모델 가져오기
from account.models import UserProfile
from django.core.files.base import ContentFile

# 1,3 경험, 상상 이미지 생성 API
@api_view(['POST'])
def generate_image_method(request):
    action = request.data.get("action")  # 요청에서 'action' 필드 추출
    prompt = request.data.get("prompt")
    artwork_id = request.data.get("artwork_id", None)  # 'imagine' 액션을 위한 artwork_id
    user_pk = request.data.get("user_pk")  # 사용자 pk 값
    session_id = request.data.get("session_id")  # 추가: masterpiece앱에서 생성된 세션 ID

    # 디버깅을 위한 로그 추가
    print(f"Received artwork_id: {artwork_id}, user_pk: {user_pk}, session_id: {session_id}")

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
        elif action == 'imagine':
            if not artwork_id:
                return Response({"error": "Artwork ID is required for 'imagine' action"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 'imagine' 액션: artwork 정보를 기반으로 프롬프트 수정
            artwork = get_object_or_404(Artwork, id=artwork_id)
            artist_style = artwork.artist_fk.style  # artist_fk 필드에서 style 접근
            artwork_title = artwork.title
            final_prompt = f"{artist_style} 화풍으로 {prompt} (그려줘)"  # 수정된 프롬프트
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=final_prompt,
                n=1,  # 생성할 이미지 개수
                size="1024x1024"  # 이미지 크기
            )
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        # 이미지 URL 및 바이너리 데이터 처리
        image_data = response.data[0]
        image_url = image_data.url

        # 세션 정보 가져오기
        session = get_object_or_404(ArtworkChatSession, id=session_id)

        # 데이터베이스에 ImageGeneration 저장, 세션ID 및 final_prompt 포함
        user = get_object_or_404(User, pk=user_pk)
        ImageGeneration.objects.create(
            user=user,
            session=session,  # 세션 ID 저장
            prompt=final_prompt,  # 최종 프롬프트 저장
            image_url=image_url,
            image_blob=requests.get(image_url).content  # 원본 바이너리 이미지도 저장
        )

        # masterpiece 앱의 ArtworkChatSession 모델의 imggen_status 필드를 'COMPLETED'로 업데이트
        session.imggen_status = 'COMPLETED'
        session.save()

        # 최종 반환 (PNG 이미지는 제외, image_url과 final_prompt만 반환)
        return Response({
            "image_url": image_url,
            "final_prompt": final_prompt
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 2. 이미지 부분 편집 API
@api_view(['POST'])
def edit_image_with_dalle2(request):
    # 프론트엔드에서 전달된 데이터 추출
    prompt = request.data.get("prompt")  # 프롬프트 텍스트
    artwork_id = request.data.get("artwork_id")  # 편집할 작품의 ID
    mask_image = request.FILES.get("mask_image")  # 마스크 이미지 파일
    user_pk = request.data.get("user_pk")  # 사용자 pk 값
    session_id = request.data.get("session_id")  # 추가: masterpiece앱에서 생성된 세션 ID

    # 필수 데이터 검증
    if not prompt:
        return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not artwork_id:
        return Response({"error": "Artwork ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not mask_image:
        return Response({"error": "Mask image is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not user_pk:
        return Response({"error": "User PK is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not session_id:
        return Response({"error": "Session ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, pk=user_pk)
    session = get_object_or_404(ArtworkChatSession, id=session_id)  # 세션 객체 가져오기

    client = OpenAI()

    # 프롬프트 번역
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates text from Korean to English."},
                {"role": "user", "content": f"Translate the following text to English: {prompt}"}
            ]
        )
        translated_prompt = completion.choices[0].message.content  # 번역된 텍스트 추출
    except Exception as e:
        return Response({"error": f"Failed to translate prompt: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # artwork_id로 Artwork 객체 조회
    artwork = get_object_or_404(Artwork, id=artwork_id)
    original_image_path = os.path.join(settings.BASE_DIR, 'masterpiece', 'static', artwork.image_path)

    # 원본 이미지 파일 존재 여부 확인
    if not os.path.exists(original_image_path):
        return Response({"error": "Original image not found"}, status=status.HTTP_404_NOT_FOUND)

    # 원본 이미지 PNG 포맷으로 변환 및 크기 조정
    try:
        original_image_pil = Image.open(original_image_path)

        # 이미지 크기 조정 (정사각형으로 맞추기)
        width, height = original_image_pil.size
        if width != height:
            new_size = min(width, height)
            original_image_pil = original_image_pil.crop(((width - new_size) // 2, (height - new_size) // 2, (width + new_size) // 2, (height + new_size) // 2))

        original_image_pil = original_image_pil.resize((1024, 1024), Image.LANCZOS)
        original_image_pil = original_image_pil.convert("RGBA")  # PNG 포맷 변환
        original_image_io = io.BytesIO()
        original_image_pil.save(original_image_io, format="PNG")
        original_image_io.seek(0)
    except Exception as e:
        return Response({"error": f"Failed to process original image: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # 마스크 이미지 PNG 포맷으로 변환 및 크기 조정
    try:
        mask_image_pil = Image.open(mask_image)

        # 파일 크기 체크
        if mask_image.size > 4 * 1024 * 1024:
            return Response({"error": "Mask image must be less than 4MB"}, status=status.HTTP_400_BAD_REQUEST)

        # 이미지 포맷 체크
        if mask_image_pil.format != "PNG":
            return Response({"error": "Mask image must be a PNG format"}, status=status.HTTP_400_BAD_REQUEST)

        # 이미지 크기 조정 (정사각형으로 맞추기)
        width, height = mask_image_pil.size
        if width != height:
            new_size = min(width, height)
            mask_image_pil = mask_image_pil.crop(((width - new_size) // 2, (height - new_size) // 2, (width + new_size) // 2, (height + new_size) // 2))

        mask_image_pil = mask_image_pil.resize((1024, 1024), Image.LANCZOS)
        mask_image_pil = mask_image_pil.convert("RGBA")  # PNG 포맷 변환
        mask_image_io = io.BytesIO()
        mask_image_pil.save(mask_image_io, format="PNG")
        mask_image_io.seek(0)
    except Exception as e:
        return Response({"error": f"Failed to process mask image: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # DALL-E 2 이미지 편집 요청
    try:
        response = client.images.edit(
            model="dall-e-2",
            image=original_image_io.getvalue(),
            mask=mask_image_io.getvalue(),
            prompt=translated_prompt,
            n=1,
            size="1024x1024"
        )
        # 생성된 이미지 URL 추출
        image_url = response.data[0].url
    except Exception as e:
        # 실패 시 세션의 imggen_status 업데이트
        session.imggen_status = 'FAILED'
        session.save()
        return Response({"error": f"Failed to edit image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 이미지 생성 기록을 DB에 저장, 세션ID 및 원본 prompt 포함
    ImageGeneration.objects.create(
        user=user,
        session=session,  # 세션 ID 저장
        prompt=prompt,  # 원본 프롬프트 저장
        image_url=image_url,
        image_blob=requests.get(image_url).content  # 원본 바이너리 이미지도 저장
    )

    # 성공 시 세션의 imggen_status 업데이트
    session.imggen_status = 'COMPLETED'
    session.save()

    # 응답 반환 (이미지 URL 반환)
    return Response({
        "edited_image_url": image_url,
    }, status=status.HTTP_200_OK)

# 이미지 생성 기록 조회 API
import logging

logger = logging.getLogger(__name__)

import base64
import io
import logging
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import ImageGeneration
from django.contrib.auth.models import User
from masterpiece.models import ArtworkChatSession

logger = logging.getLogger(__name__)

@api_view(['POST'])
def get_image_history(request):
    user_pk = request.data.get('user_pk')
    session_id = request.data.get('session_id')

    if not user_pk:
        return Response({'error': 'User pk is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not session_id:
        return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, pk=user_pk)
    session = get_object_or_404(ArtworkChatSession, id=session_id)

    latest_image = ImageGeneration.objects.filter(user=user, session=session).order_by('-created_at').first()

    if not latest_image:
        logger.error('No images found for this session')
        return Response({'error': 'No images found for this session'}, status=status.HTTP_404_NOT_FOUND)

    image_content = latest_image.image_blob
    if image_content:
        try:
            # base64 데이터를 디코딩하여 PNG 이미지로 변환
            logger.info("Starting base64 decoding of image content")
            image_data = base64.b64decode(image_content)
            image_io = io.BytesIO(image_data)
            image_io.seek(0)
            logger.info("Image decoding successful, preparing FileResponse")

            # FileResponse로 PNG 이미지 반환
            return FileResponse(image_io, as_attachment=True, filename="generated_image.png", content_type="image/png")
        except Exception as e:
            logger.error(f"Failed to decode image content: {e}")
            return Response({'error': 'Image decoding failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        logger.error('Image data not available')
        return Response({'error': 'Image data not available'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
