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
from masterpiece.models import Artwork
from account.models import UserProfile
from masterpiece.models import Artwork, Artist  # 필요한 모델 가져오기
from django.http import HttpResponse
import requests

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



from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from PIL import Image
import os
import io
from openai import OpenAI


@api_view(['POST'])
def edit_image_with_dalle2(request):
    # 프론트엔드에서 전달된 데이터 추출
    prompt = request.data.get("prompt")  # 프롬프트 텍스트
    artwork_id = request.data.get("artwork_id")  # 편집할 작품의 ID
    mask_image = request.FILES.get("mask_image")  # 마스크 이미지 파일
    user_pk = request.data.get("user_pk")  # 사용자 pk 값

    # 필수 데이터 검증
    if not prompt:
        return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not artwork_id:
        return Response({"error": "Artwork ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not mask_image:
        return Response({"error": "Mask image is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not user_pk:
        return Response({"error": "User PK is required"}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, pk=user_pk)

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
        return Response({"error": f"Failed to edit image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 이미지 생성 기록을 DB에 저장
    ImageGeneration.objects.create(user=user, image_url=image_url)

    # 응답 반환
    return Response({"edited_image_url": image_url}, status=status.HTTP_200_OK)





import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
from .models import ImageGeneration
from masterpiece.models import ArtworkChatSession
from account.models import UserProfile
from django.contrib.auth.models import User
from masterpiece.models import Artwork
from django.core.files.base import ContentFile

@api_view(['POST'])
def generate_image_method(request):
    action = request.data.get("action")  # 요청에서 'action' 필드 추출
    prompt = request.data.get("prompt")
    artwork_id = request.data.get("artwork_id", None)  # 'imagine' 액션을 위한 artwork_id
    user_pk = request.data.get("user_pk")  # 사용자 pk 값
    session_id = request.data.get("session_id")  # 세션 ID 값

    # 필수 입력값 체크
    if not action or not prompt or not user_pk or not session_id:
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = OpenAI()

        # DALL-E 3 API 호출로 이미지 생성
        if action == 'experience':
            # 프롬프트 생성 및 API 요청 처리
            # ... 기존의 프롬프트 생성 및 응답 처리 로직 포함 ...

        elif action == 'imagine':
            # 프롬프트 생성 및 API 요청 처리
            # ... 기존의 프롬프트 생성 및 응답 처리 로직 포함 ...

        # 이미지 URL로부터 이미지 다운로드
        image_data = response.data[0]
        image_url = image_data.url
        image_response = requests.get(image_url)
        image = Image.open(BytesIO(image_response.content))

        # 이미지를 바이너리로 변환하여 데이터베이스에 저장
        image_blob = BytesIO()
        image.save(image_blob, format="PNG")
        image_blob_data = image_blob.getvalue()  # 바이너리 데이터로 변환

        # 이미지 생성 기록을 데이터베이스에 저장
        user = get_object_or_404(User, pk=user_pk)
        image_generation = ImageGeneration.objects.create(
            user=user,
            session_id=session_id,
            prompt=prompt,
            image_url=image_url,
            image_blob=image_blob_data  # 이미지 데이터를 BLOB 필드에 저장
        )

        # 프론트엔드로 PNG 이미지 응답 생성
        response = HttpResponse(image_blob_data, content_type="image/png")
        response['Content-Disposition'] = 'inline; filename="generated_image.png"'
        return response

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def get_image_history(request):
    # 요청에서 사용자 pk 값 가져오기
    user_pk = request.data.get('user_pk')
    
    # 사용자 pk 값이 없는 경우 오류 반환
    if not user_pk:
        return Response({'error': 'User pk is required'}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 pk에 해당하는 사용자 가져오기
    user = get_object_or_404(User, pk=user_pk)
    
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
