import json
from common.models import UserProfile # 사용자 정보 가져오기 
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .services import get_random_artwork, create_chat_session, chat_with_gpt, add_message_to_session
from .models import ChatSession
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view


# 랜덤 명화 정보를 반환하는 API
@api_view(['GET'])
@permission_classes([AllowAny])
def random_artwork_view(request):
    artwork = get_random_artwork()
    data = {
        "id": artwork.id,
        "title": artwork.title,
        "artist": artwork.artist,
        "hook" : artwork.hook,
        "image_url": artwork.image_url
    }
    return Response(data, status=status.HTTP_200_OK)

# 사용자와 GPT 간의 대화 세션을 처리하는 API
@api_view(['POST'])
@permission_classes([AllowAny])
def chat_view(request):
    # UserProfile을 기반으로 사용자 가져오기(수미 부분 나중에 연결 예정)
    # if request.user.is_authenticated:
    #    user_profile = get_object_or_404(UserProfile, user=request.user)  # 로그인한 사용자의 프로필 가져오기
    # else:
    #    return JsonResponse({'error': 'User must be logged in'}, status=403) 
    
    # 테스트용 임시 사용자 설정
    # user, created = User.objects.get_or_create(username='test_user', defaults={'password': 'testpass'})
    
    # 데이터 파싱
    try:
        session_id = request.data.get('session_id')  # JSON 데이터에서 세션 ID 가져오기
        message = request.data.get('message')  # JSON 데이터에서 메시지 가져오기
        print(f"Received session_id: {session_id}, message: {message}")  # 로그 추가
    except KeyError:
        return Response({'error': 'Invalid data format'}, status=status.HTTP_400_BAD_REQUEST)


    # 메시지가 비어있는지 확인
    if not message or message.strip() == "":
        return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

    # 세션이 있으면 기존 채팅 세션을 이어감
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return Response({'error': 'Session does not exist'}, status=status.HTTP_404_NOT_FOUND)
    else: 
        # 새로운 세션 생성
        artwork = get_random_artwork()  # 랜덤 명화 선택
        session = create_chat_session(user, artwork)  # 사용자와 명화를 기반으로 새로운 채팅 세션 생성

    # 사용자 메시지 저장 
    add_message_to_session(session, 'user', message)  # 사용자가 입력한 메세지 채팅 세션에 저장

    # GPT와의 대화
    gpt_response = chat_with_gpt(session, message)  # gpt가 대화의 맥락을 이해하도록 세션 정보 함께 넘김
    # GPT 응답이 비어있는지 확인
    if not gpt_response or gpt_response.strip() == "":
        return Response({'error': 'GPT response is empty'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # GPT 응답 저장
    add_message_to_session(session, 'assistant', gpt_response)
    return Response({'response': gpt_response, 'session_id': session.id}, status=status.HTTP_200_OK)

@permission_classes([AllowAny])
@api_view(['GET'])
def chat_history_view(request):
    # UserProfile을 기반으로 사용자 가져오기(수미 부분 연결)
    # if request.user.is_authenticated:
    #    user_profile = get_object_or_404(UserProfile, user=request.user)  # 로그인한 사용자의 프로필 가져오기
    # else:
    #    return JsonResponse({'error': 'User must be logged in'}, status=403)

    # 테스트용 임시 사용자 설정
    # user, created = User.objects.get_or_create(username='test_user', defaults={'password': 'testpass'})

    chat_sessions = ChatSession.objects.filter(user=user).order_by('-created_at') # db에서 사용자가 진행했던 모든 채팅 세션 최신순으로 불러옴

    history = [] # 사용자가 참여했던 채팅 세션 기록을 저장할 빈 리스트. 
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
