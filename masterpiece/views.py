import json
from account.models import UserProfile 
from docent.models import Docent
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.conf import settings
from .services import get_random_artwork, create_artwork_chat_session, artwork_chat_with_gpt
from .models import ArtworkChatSession
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from langchain.memory import ConversationBufferMemory


# 랜덤 명화 정보를 반환하는 API 
@api_view(['POST'])
def random_artwork_view(request):
    user_pk = request.data.get('user_pk')
    
    # 사용자 pk가 없을 경우 에러 반환
    if not user_pk:
        return Response({"error": "User pk is required."}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 조회
    user = get_object_or_404(User, pk=user_pk)

    # UserProfile 조회
    try:
        user_profile = UserProfile.objects.get(user=user)
        selected_docent_id = user_profile.selected_docent.id  # ForeignKey이므로 id를 가져옴
    except UserProfile.DoesNotExist:
        return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)

    # 랜덤으로 명화 가져오기
    artwork = get_random_artwork()

    # 명화가 주어지면 새로운 대화 세션 생성. 세션 아이디 부여됨
    session = create_artwork_chat_session(user, artwork)

    # 이미지 URL 생성 (static 파일 사용)
    image_path = request.build_absolute_uri(settings.STATIC_URL + artwork.image_path)

    # 반환할 데이터 구성
    data = {
        "id": artwork.id,
        "title": artwork.title,
        "artist": artwork.artist,
        "hook": artwork.hook,
        "image_path": image_path,
        "session_id": session.id,  # 생성된 세션 ID 포함
        "selected_docent_id": selected_docent_id  # UserProfile에 저장된 selected_docent_id 값 포함
    }

    return Response(data, status=status.HTTP_200_OK)

# 명화 기반 대화 세션을 처리하는 API

@api_view(['POST'])
def artwork_chat_view(request):
    # 사용자 pk를 요청 데이터에서 가져옴
    user_pk = request.data.get('user_pk')
    session_id = request.data.get('session_id')  # JSON 데이터에서 세션 ID 가져오기
    message = request.data.get('message')  # JSON 데이터에서 메시지 가져오기

    # user_pk, session_id, message가 비어있는지 확인
    if not user_pk:
        return Response({'error': 'User pk is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not session_id:
        return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    if not message or message.strip() == "":
        return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 조회
    user = get_object_or_404(User, pk=user_pk)

    # 사용자 프로필 가져오기
    user_profile = get_object_or_404(UserProfile, user=user)

    # UserProfile에서 selected_docent_id 가져오기
    selected_docent_id = user_profile.selected_docent_id

    # Docent 모델에서 해당 도슨트 가져오기
    docent = get_object_or_404(Docent, pk=selected_docent_id)

    # 도슨트의 프롬프트 가져오기
    docent_prompt = docent.docent_prompt

    # 세션이 있으면 기존 채팅 세션을 이어감
    session = get_object_or_404(ArtworkChatSession, id=session_id, user=user)

    # GPT와 대화 생성 (대화 기록은 자동으로 메모리에 관리됨)
    gpt_response = artwork_chat_with_gpt(session, message, docent_prompt)
    
    if not gpt_response or gpt_response.strip() == "":
        return Response({'error': 'GPT response is empty'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'response': gpt_response,
        'session_id': session.id,
        'selected_docent_id': selected_docent_id,
        'docent_prompt': docent_prompt
    }, status=status.HTTP_200_OK)


# 명화 기반 대화 기록을 보여주는 API
@api_view(['POST'])
def artwork_chat_history_view(request):
    # 사용자 pk를 프론트에서 전달받음
    user_pk = request.data.get('user_pk')
    if not user_pk:
        return Response({'error': 'User pk is required'}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 pk로 사용자 객체 가져오기
    user = get_object_or_404(User, pk=user_pk)

    # 명화에 대한 사용자의 모든 채팅 세션을 가져옴
    chat_sessions = ArtworkChatSession.objects.filter(user=user).order_by('-created_at')  # 사용자의 채팅 세션을 최신순으로 불러옴

    history = []  # 모든 채팅 세션 기록을 저장할 빈 리스트

    for session in chat_sessions:
        chat_history = json.loads(session.chat_history) if session.chat_history else []
        # 각 채팅 세션의 명화 기록 함께 추가
        history.append({
            "session_id": session.id,
            "artwork": {
                "title": session.artwork.title,
                "artist": session.artwork.artist,
                "image_path": request.build_absolute_uri(settings.STATIC_URL + session.artwork.image_path)
            },
            "messages": chat_history
        })

    return Response(history, status=status.HTTP_200_OK)
