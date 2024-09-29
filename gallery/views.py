from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Museum, Exhibition

# 미술관 목록
@api_view(['GET'])
def museum_list_view(request):
    museums = Museum.objects.all()
    museum_data = [{"id": museum.id, "name": museum.name, "location": museum.location, "description": museum.description} for museum in museums]
    return Response(museum_data, status=status.HTTP_200_OK)

# 미술관 전시 정보
@api_view(['GET'])
def exhibition_list_view(request, museum_id):
    museum = Museum.objects.get(id=museum_id)
    exhibitions = museum.exhibitions.all()
    exhibition_data = [{"id": exhibition.id, "title": exhibition.title, "description": exhibition.description, "start_date": exhibition.start_date, "end_date": exhibition.end_date} for exhibition in exhibitions]
    return Response(exhibition_data, status=status.HTTP_200_OK)

# 미술관 전시 기반 대화 세션을 처리하는 API
@api_view(['POST'])
def exhibition_chat_view(request):
    user, created = User.objects.get_or_create(username='test_user', defaults={'password': 'testpass'})

    session_id = request.data.get('session_id')
    message = request.data.get('message')

    if session_id:
        session = ExhibitionChatSession.objects.get(id=session_id, user=user)
    else:
        exhibition = get_random_exhibition()
        session = ExhibitionChatSession.objects.create(user=user, exhibition=exhibition)

    add_message_to_session(session, 'user', message)
    gpt_response = chat_with_gpt(session, message)
    add_message_to_session(session, 'assistant', gpt_response)

    return Response({'response': gpt_response, 'session_id': session.id}, status=status.HTTP_200_OK)