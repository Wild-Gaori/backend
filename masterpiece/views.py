import json
from common.models import UserProfile 
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .services import get_random_artwork, create_artwork_chat_session, artwork_chat_with_gpt, add_message_to_session
from .models import ArtworkChatSession
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token


# 랜덤 명화 정보를 반환하는 API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def random_artwork_view(request):
    artwork = get_random_artwork()

    # 현재 요청에서 인증된 사용자 정보 사용
    user = request.user

    # 명화가 주어지면 바로 새로운 대화 세션 생성. 세션 아이디 부여됨
    session = ArtworkChatSession.objects.create(user=user, artwork=artwork)
    
    data = {
        "id": artwork.id,
        "title": artwork.title,
        "artist": artwork.artist,
        "hook" : artwork.hook,
        "image_url": artwork.image_url,
        "session_id": session.id  # 생성된 세션 ID 포함
    }
    return Response(data, status=status.HTTP_200_OK)

# 명화 기반 대화 세션을 처리하는 API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def artwork_chat_view(request):

    # 현재 요청에서 인증된 사용자 정보 사용
    user = request.user

    # 데이터 파싱
    try:
        session_id = request.data.get('session_id')  # JSON 데이터에서 세션 ID 가져오기
        message = request.data.get('message')  # JSON 데이터에서 메시지 가져오기
    except KeyError:
        return Response({'error': 'Invalid data format'}, status=status.HTTP_400_BAD_REQUEST)

    # 세션이 없으면 에러 반환
    if not session_id:
        return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    # 메시지가 비어있는지 확인
    if not message or message.strip() == "":
        return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

    # 세션이 있으면 기존 채팅 세션을 이어감
    try:
        session = ArtworkChatSession.objects.get(id=session_id, user=user)
        artwork = session.artwork  # 세션과 연결된 명화 가져오기
    except ArtworkChatSession.DoesNotExist:
        return Response({'error': 'Session does not exist'}, status=status.HTTP_404_NOT_FOUND)

    add_message_to_session(session, 'user', message)  # 사용자가 입력한 메세지 채팅 세션에 저장
    gpt_response = artwork_chat_with_gpt(session, message)  # gpt가 대화의 맥락을 이해하도록 세션 정보 함께 넘김
    if not gpt_response or gpt_response.strip() == "":
        return Response({'error': 'GPT response is empty'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'response': gpt_response, 'session_id': session.id}, status=status.HTTP_200_OK)

# 명화 기반 대화 기록 보여주는 API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def artwork_chat_history_view(request):
    
    # 현재 요청에서 인증된 사용자 정보 사용
    user = request.user

    # 명화에 대한 사용자의 모든 채팅 세션을 가져옴
    chat_sessions = ArtworkChatSession.objects.filter(user=user).order_by('-created_at') # 사용자의 채팅 세션 최신순으로 불러옴

    history = [] # 사용자가 참여했던 채팅 세션 기록을 저장할 빈 리스트
    for session in chat_sessions:
        messages = session.messages.all().values('role', 'content') 
        history.append({
            "session_id": session.id,
            "artwork": {
                "title": session.artwork.title,
                "artist": session.artwork.artist,
                "image_url": session.artwork.image_url
            },
            "messages": list(messages)
        })

    return Response(history, status=status.HTTP_200_OK)
