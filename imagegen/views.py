import os
import io
import logging
from PIL import Image
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from openai import OpenAI
from .models import ImageGeneration
from .serializers import ImageGenerationSerializer
from account.models import UserProfile
from masterpiece.models import Artwork, Artist

logger = logging.getLogger(__name__)

@api_view(['POST'])
def edit_image_with_dalle2(request):
    # 프론트엔드에서 전달된 데이터 추출
    prompt = request.data.get("prompt")
    artwork_id = request.data.get("artwork_id")
    mask_image = request.FILES.get("mask_image")
    user_pk = request.data.get("user_pk")

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
        translated_prompt = completion.choices[0].message.content
    except Exception as e:
        return Response({"error": f"Failed to translate prompt: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    artwork = get_object_or_404(Artwork, id=artwork_id)
    original_image_path = os.path.join(settings.BASE_DIR, 'masterpiece', 'static', artwork.image_path)

    if not os.path.exists(original_image_path):
        return Response({"error": "Original image not found"}, status=status.HTTP_404_NOT_FOUND)

    # 원본 이미지 처리
    try:
        original_image_pil = Image.open(original_image_path)
        width, height = original_image_pil.size
        if width != height:
            new_size = min(width, height)
            original_image_pil = original_image_pil.crop(((width - new_size) // 2, (height - new_size) // 2, (width + new_size) // 2, (height + new_size) // 2))

        original_image_pil = original_image_pil.resize((1024, 1024), Image.LANCZOS)
        original_image_pil = original_image_pil.convert("RGBA")
        original_image_io = io.BytesIO()
        original_image_pil.save(original_image_io, format="PNG")
        original_image_io.seek(0)
    except Exception as e:
        return Response({"error": f"Failed to process original image: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # 마스크 이미지 처리
    try:
        mask_image_pil = Image.open(mask_image)
        if mask_image.size > 4 * 1024 * 1024:
            return Response({"error": "Mask image must be less than 4MB"}, status=status.HTTP_400_BAD_REQUEST)
        if mask_image_pil.format != "PNG":
            return Response({"error": "Mask image must be a PNG format"}, status=status.HTTP_400_BAD_REQUEST)

        width, height = mask_image_pil.size
        if width != height:
            new_size = min(width, height)
            mask_image_pil = mask_image_pil.crop(((width - new_size) // 2, (height - new_size) // 2, (width + new_size) // 2, (height + new_size) // 2))

        mask_image_pil = mask_image_pil.resize((1024, 1024), Image.LANCZOS)
        mask_image_pil = mask_image_pil.convert("RGBA")
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
        image_url = response.data[0].url
    except Exception as e:
        return Response({"error": f"Failed to edit image: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ImageGeneration.objects.create(user=user, image_url=image_url)
    return Response({"edited_image_url": image_url}, status=status.HTTP_200_OK)


@api_view(['POST'])
def generate_image_method(request):
    action = request.data.get("action")
    prompt = request.data.get("prompt")
    artwork_id = request.data.get("artwork_id", None)
    user_pk = request.data.get("user_pk")

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
            gender = user_profile.gender or ""
            clothing = user_profile.clothing or "반팔옷"
            hairstyle = user_profile.hairstyle or "짧은 머리"
            final_prompt = f"나는 {gender} 초등학생이고 {clothing} 옷을 입었고 머리는 {hairstyle}(이)야. {prompt}"
            response = client.images.generate(
                model="dall-e-3",
                prompt=final_prompt,
                n=1,
                size="1024x1024"
            )
        elif action == 'imagine':
            if not artwork_id:
                return Response({"error": "Artwork ID is required for 'imagine' action"}, status=status.HTTP_400_BAD_REQUEST)
            
            artwork = get_object_or_404(Artwork, id=artwork_id)
            artist_style = artwork.artist_fk.style
            final_prompt = f"{artist_style} 화풍으로 {prompt} (그려줘)"
            response = client.images.generate(
                model="dall-e-3",
                prompt=final_prompt,
                n=1,
                size="1024x1024"
            )
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        image_data = response.data[0]
        image_url = image_data.url

        # 이미지 다운로드 후 BinaryField에 저장할 준비
        image_content = requests.get(image_url).content
        image = Image.open(io.BytesIO(image_content))
        image_io = io.BytesIO()
        image.save(image_io, format="PNG")

        # ImageGeneration 객체 생성 및 바이너리 이미지 저장
        user = get_object_or_404(User, pk=user_pk)
        image_instance = ImageGeneration.objects.create(
            user=user,
            prompt=prompt,
            image_url=image_url,
            image_png=image_io.getvalue()  # 바이너리 데이터를 직접 저장
        )
        
        # 프론트엔드로 바이너리 데이터를 반환
        return Response({
            "image_url": image_url,
            "image_png": image_instance.image_png  # 바이너리 데이터를 직접 반환
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_image_history(request):
    user_pk = request.data.get('user_pk')
    if not user_pk:
        return Response({'error': 'User pk is required'}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, pk=user_pk)
    images = ImageGeneration.objects.filter(user=user).order_by('-created_at')

    history = []
    for image in images:
        history.append({
            'image_id': image.id,
            'image_url': image.image_url,
            'created_at': image.created_at,
        })

    return Response(history, status=status.HTTP_200_OK)
