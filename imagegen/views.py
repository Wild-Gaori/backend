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
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from masterpiece.models import Artwork, Artist  # 필요한 모델 가져오기

logger = logging.getLogger(__name__)

@api_view(['POST'])
def generate_image(request):
    logger.info(f"Request data: {request.data}")  # 로그에 요청 데이터 출력
    # 요청 데이터를 serializer에 전달하여 유효성 검사
    serializer = ImageGenerationSerializer(data=request.data)

    if not serializer.is_valid():
        logger.error(f"Validation failed: {serializer.errors}")  # 유효성 검사 실패 시 로그 출력
        # 유효하지 않은 경우 400 Bad Request와 오류 메시지 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 유효한 경우 prompt 데이터를 추출
    prompt = serializer.validated_data['prompt']
    
    try:
        client = OpenAI()

        # DALL·E 3 API 호출
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",  # 이미지 크기
            quality="standard",
            n=1,
        )

        # 응답에서 이미지 URL 추출
        image_url = response.data[0].url  # 이미지 URL에 접근 

        # 이미지 생성 기록  DB에 저장
        #테스트 사용자
        user, created = User.objects.get_or_create(username='test', defaults={'password': 'test'})

        image_generation = ImageGeneration.objects.create(user=user, image_url=image_url)

        return Response({"image_url": image_url}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from openai import OpenAI
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from PIL import Image
import os
import io
from googletrans import Translator

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

    # 프롬프트 영어로 번역
    try:
        translator = Translator()
        translated_prompt = translator.translate(prompt, src='ko', dest='en').text
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

    try:
        client = OpenAI()

        # DALL-E 2 이미지 편집 요청
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

        # 응답 반환
        return Response({"edited_image_url": image_url}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

@api_view(['POST'])
def generate_image_method(request):
    action = request.data.get("action")  # 요청에서 'action' 필드 추출
    prompt = request.data.get("prompt")
    artwork_id = request.data.get("artwork_id", None)  # 'imagine' 액션을 위한 artwork_id

    if not action:
        return Response({"error": "Action is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if not prompt:
        return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = OpenAI()

        if action == 'experience':
            # 'experience' 액션: 단순 이미지 생성
            final_prompt = prompt  # 이 경우에는 프롬프트 자체를 사용
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
            final_prompt = f"{artist_style} 화풍으로 {artwork_title} 작품에 {prompt}"  # 수정된 프롬프트
            
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
