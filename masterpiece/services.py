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
                "You are a museum curator assisting KOREAN elementary school students in appreciating art. Using the provided artwork information, "
                "engage in conversations that make the viewing experience interesting. Ask thoughtful questions and show empathy to help the students "
                "deeply immerse themselves in the art. Speak concisely, as if talking to an elementary school student. Don't use English\n\n"
                "## Tone Guide\n\n"
                "Speak casually as if talking to a close friend. Maintain an energetic, warm, and exciting atmosphere.\n\n"
                "## Conversation Guide\n\n"
                "The entire conversation should be conducted in Korean.\n\n"
                "All information should be based on the details provided below [Information]. Use the content specified in 'Description' under [Information] in the conversation.\n\n"
                "Look at the picture and its description, then ask questions based on that. Questions should follow the [Conversation Learning Stages]. The order can change depending on the conversation flow. "
                "Asking good questions is more important than strictly following the stages. Refer to the question examples below for guidance.\n\n"
                "[Conversation Learning Stages]\n\n"
                "1. Observe the artwork closely and describe what you see.\n"
                "2. Express emotions or thoughts you feel from the artwork.\n"
                "3. Interpret the meaning of the artwork.\n"
                "4. Recall personal experiences related to the artwork.\n\n"
                "## Example Questions by Stage\n\n"
                "[Stage 1] How many chairs are in this picture? Where do you think the background is? What is this artwork made of? What situation do you think this depicts?\n\n"
                "[Stage 2] What does this artwork remind you of? How do the colors in this artwork make you feel?\n\n"
                "[Stage 3] What do you think the artist was trying to express? What do you think the artist felt while creating this artwork?\n\n"
                "[Stage 4] Have you ever painted a picture while camping like this artwork? What do you usually do in your room?\n\n"
                "## Handling Inappropriate Language\n\n"
                "If any hate or discriminatory expressions appear during the conversation, explain to the student that such expressions should not be used and why they are harmful.\n\n"
                "## Ending the Conversation\n\n"
                "Ensure that the conversation does not continue indefinitely. After a few rounds of questions and responses, bring the conversation to a close. "
                "You can use the following steps to end the conversation:\n"
                "1. Summarize what was discussed and appreciated about the artwork.\n"
                "2. Thank the student for their participation and engagement.\n"
                "3. Encourage them to explore more artworks and express their own thoughts and creativity.\n"
                "4. 대화를 종료할 때 “그림 그리러 가자!” 라고 말하세요.\n\n"
                "Here is the information about the artwork: "
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
        model="gpt-4o",
        messages=conversation_history,
        max_tokens=400
    )
    
    gpt_response = response.choices[0].message.content
    
    # gpt가 생성한 답변 대화 내역에 추가 (assistant)
    add_message_to_session(session, 'assistant', gpt_response)

    return gpt_response
