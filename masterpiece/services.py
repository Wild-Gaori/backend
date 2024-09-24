import os
from openai import OpenAI
from .models import Artwork, ArtworkChatSession, ArtworkMessage
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
import random

client = OpenAI()

# 명화 랜덤 가져오기
def get_random_artwork():
    return Artwork.objects.order_by('?').first()

# 명화 채팅 세션 생성 함수
def create_artwork_chat_session(user, artwork):
    return ArtworkChatSession.objects.create(user=user, artwork=artwork)

# 각 세션에서 user, assistant 별 대화 content를 db에 기록
def add_message_to_session(session, role, content):
    ArtworkMessage.objects.create(session=session, role=role, content=content)

# 명화 기반 gpt와 대화
def artwork_chat_with_gpt(session, user_message):
    # 현재 채팅 세션과 관련된 이전 메세지 가져오기. 맥락에 맞게 대화 이어나가기 위함.
    previous_messages = ArtworkMessage.objects.filter(session=session).order_by('timestamp') # 현재 세션에 해당하는 메세지 가져와 메세지 시간순 정렬.
    conversation_history = [
        {"role": msg.role, "content": msg.content} for msg in previous_messages
    ]
    
    # 시스템 메시지가 이미 포함되어 있지 않으면 추가. 시스템 메세지가 대화 세션 처음에만 들어가도록 함.
    if not any(msg['role'] == 'system' for msg in conversation_history):
        # 시스템 메시지: GPT의 역할 설명
        conversation_history.insert(0, {
            "role": "system", 
            "content": (
                "You are an art docent for children, helping them appreciate famous artworks. "
                "Your role is to explain the artwork in a friendly and engaging manner, ask insightful questions, "
                "and guide the user through the artwork's meaning. Make the conversation fun and educational."
                "Artwork_info is as follows : "
            )
        })
        # 명화 정보 
        artwork_info = (
            f"Artwork: {session.artwork.title} by {session.artwork.artist}, "
            f"created in {session.artwork.year}. Description: {session.artwork.description} "
            f"image_url: {session.artwork.image_url}"
        )
        conversation_history.append({"role": "system", "content": artwork_info})

    # 사용자의 메세지를 대화에 추가
    conversation_history.append({"role": "user", "content": user_message})

    # GPT와 대화
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        max_tokens=150
    )
    
    gpt_response = response.choices[0].message.content
    
    # gpt가 생성한 답변 대화 내역에 추가 (assistant)
    add_message_to_session(session, 'assistant', gpt_response)

    return gpt_response
