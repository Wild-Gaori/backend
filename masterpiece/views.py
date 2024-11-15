import json
from account.models import UserProfile 
from docent.models import Docent
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.conf import settings
from .services import get_random_artwork, create_artwork_chat_session, artwork_chat_with_gpt
from .models import Artwork,ArtworkChatSession, ChatSession
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from langchain.memory import ConversationBufferMemory
from django.db.models import Q


# 랜덤 명화 정보를 반환하는 API
@api_view(['POST'])
def random_artwork_view(request):
    user_pk = request.data.get('user_pk')
    excluded_artwork_ids = request.data.get('excluded_artwork_ids', [])

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

    # 제외할 명화가 있을 경우 필터링
    artwork_queryset = Artwork.objects.exclude(id__in=excluded_artwork_ids)
    if not artwork_queryset.exists():
        return Response({"error": "No artworks available after exclusion."}, status=status.HTTP_404_NOT_FOUND)

    # 필터링된 명화 중 하나를 랜덤으로 가져오기
    artwork = artwork_queryset.order_by('?').first()

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

    # 대화 당시의 도슨트 정보 저장
    session.docent_at_chat = docent
    session.save()

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

# 그림 그리러 가기 버튼으로 채팅 종료 후 채팅 세션 복사하는 API
@api_view(['POST'])
def copy_artwork_chat_session(request):
    # 프론트에서 ArtworkChatSession의 세션 ID를 입력받음
    artwork_chat_session_id = request.data.get('session_id')

    # 세션 ID가 없으면 에러 반환
    if not artwork_chat_session_id:
        return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    # ArtworkChatSession 객체 가져오기
    artwork_chat_session = get_object_or_404(ArtworkChatSession, id=artwork_chat_session_id)

    # ChatSession에 복사
    chat_session = ChatSession.objects.create(
        user=artwork_chat_session.user,
        artwork=artwork_chat_session.artwork,
        created_at=artwork_chat_session.created_at,
        chat_history=artwork_chat_session.chat_history,
        docent_at_chat=artwork_chat_session.docent_at_chat,
        imggen_status='PENDING'  # 초기 상태 설정
    )

    # 복사 완료 메시지 반환
    return Response({
        'message': 'Session copied successfully.',
        'session_id': chat_session.id,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def artwork_chat_history_view(request):
    # 사용자 pk와 액션을 요청 데이터에서 가져오기
    user_pk = request.data.get('user_pk')
    action = request.data.get('action')  # 액션: 'all' 또는 'completed' 중 하나

    # 사용자 pk가 없을 경우 에러 반환
    if not user_pk:
        return Response({'error': 'User pk is required'}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 조회
    user = get_object_or_404(User, pk=user_pk)

    # 액션에 따른 필터 조건 설정
    if action == 'completed':
        # imggen_status가 COMPLETED인 세션만 가져오기
        chat_sessions = ChatSession.objects.filter(user=user, imggen_status='COMPLETED').order_by('-created_at')
    else:
        # 모든 세션 가져오기
        chat_sessions = ChatSession.objects.filter(user=user).order_by('-created_at')

    # 채팅 기록을 저장할 리스트
    history = []

    for session in chat_sessions:
        chat_history = json.loads(session.chat_history) if session.chat_history else []
        # 각 세션의 정보 추가
        history.append({
            "session_id": session.id,
            "artwork": {
                "title": session.artwork.title,
                "artist": session.artwork.artist,
                "image_path": request.build_absolute_uri(settings.STATIC_URL + session.artwork.image_path)
            },
            "docent_id": session.docent_at_chat_id,
            "imggen_status": session.imggen_status,
            "messages": chat_history
        })

    return Response(history, status=status.HTTP_200_OK)

# 사용자의 전시 작품 감상 여부 확인 API
@api_view(['POST'])
def completed_artworks_for_user(request):
    user_pk = request.data.get('user_pk')
    artwork_ids = request.data.get('artwork_ids', None)

    # 필수 필드가 있는지 확인
    if not user_pk:
        return Response({"error": "User pk가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 작품 ID가 없으면 백엔드에서 기본값 설정
    if not artwork_ids:
        # 기본적으로 조회할 ID 리스트 (필요시 변경 가능)
        artwork_ids = [ 5, 6, 7]
        

    # artwork_ids가 리스트가 아니거나 비어있는 경우 에러 반환
    if not isinstance(artwork_ids, list) or len(artwork_ids) == 0:
        return Response({'error': 'A valid list of artwork IDs is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 확인
    user = get_object_or_404(User, pk=user_pk)

    # 해당 사용자의 imggen_status가 'COMPLETED'인 ChatSession 가져오기
    completed_sessions = ChatSession.objects.filter(user=user, imggen_status='COMPLETED')

    # 완료된 세션에서 입력받은 artwork_ids와 일치하는 작품 ID 필터링
    completed_artwork_ids = [
        session.artwork.id
        for session in completed_sessions
        if session.artwork.id in artwork_ids
    ]

    # 일치하는 artwork_id 리스트 반환
    return Response({"completed_artwork_ids": completed_artwork_ids}, status=status.HTTP_200_OK)


# 미술관 전시 작품 정보 반환 API
@api_view(['POST'])
def get_gallery_artworks_list(request):
    # 프론트엔드에서 전달된 작품 ID 리스트
    artwork_ids = request.data.get('artwork_ids', None)

    # 작품 ID가 없으면 백엔드에서 기본값 설정
    if not artwork_ids:
        # 기본적으로 조회할 ID 리스트 (필요시 변경 가능)
        artwork_ids = [5, 6, 7] 

    # artwork_ids가 리스트가 아니거나 비어있는 경우 에러 반환
    if not isinstance(artwork_ids, list) or len(artwork_ids) == 0:
        return Response({'error': 'A valid list of artwork IDs is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # ID에 해당하는 Artwork 객체 가져오기
        artworks = Artwork.objects.filter(id__in=artwork_ids)

        # 해당하는 Artwork가 없을 경우 처리
        if not artworks.exists():
            return Response({'error': 'No artworks found for the given IDs.'}, status=status.HTTP_404_NOT_FOUND)

        # Artwork 정보 구성
        artwork_data = [
            {
                'id': artwork.id,
                'title': artwork.title,
                'artist': artwork.artist,
                'year': artwork.year,
                'description': artwork.description,
                'hook': artwork.hook,
                'image_url': artwork.image_url,
                'image_path': request.build_absolute_uri(settings.STATIC_URL + artwork.image_path),
            }
            for artwork in artworks
        ]

        return Response({'artworks': artwork_data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# 미술관 전시 작품 기반 대화 세션을 처리하는 API
@api_view(['POST'])
def create_artwork_chat_session_view(request):
    user_pk = request.data.get('user_pk')
    artwork_id = request.data.get('artwork_id')

    # 필수 값 검증
    if not user_pk:
        return Response({'error': 'User pk is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not artwork_id:
        return Response({'error': 'Artwork ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 사용자 조회
        user = get_object_or_404(User, pk=user_pk)

        # 명화 조회
        artwork = get_object_or_404(Artwork, id=artwork_id)

        # 사용자 프로필 조회
        user_profile = get_object_or_404(UserProfile, user=user)

        # UserProfile에서 selected_docent_id 가져오기
        selected_docent_id = user_profile.selected_docent_id

        # Docent 정보 가져오기
        docent = get_object_or_404(Docent, pk=selected_docent_id)

        # 새로운 세션 생성
        session = ArtworkChatSession.objects.create(
            user=user,
            artwork=artwork,
            docent_at_chat=docent
        )

        # 응답 데이터 반환
        return Response({
            'session_id': session.id,
            'selected_docent_id': selected_docent_id,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

