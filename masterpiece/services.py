from typing import Sequence
import os
import json
import base64
import requests
from django.conf import settings
# rag 관련
import bs4
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
# from langchain.vectorstores import Chroma
from urllib.parse import urlparse
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_history_aware_retriever, create_retrieval_chain,LLMChain
from langchain.chains.combine_documents import create_stuff_documents_chain

# 대화 기록 관련
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


from .models import Artwork, ArtworkChatSession

# 환경 변수에서 API 키 가져오기
api_key = os.getenv("OPENAI_API_KEY")

# ChatOpenAI 인스턴스 생성
llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini",temperature=0)

# 명화 랜덤 가져오기
def get_random_artwork():
    return Artwork.objects.order_by('?').first()

# 명화 채팅 세션 생성 함수
def create_artwork_chat_session(user, artwork):
    return ArtworkChatSession.objects.create(user=user, artwork=artwork)

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# 명화와 관련된 추가 정보를 웹에서 로드하고 벡터화
def load_and_retrieve_artwork_data(artwork):
    # 1) 명화 관련된 웹 URL을 artwork db에서 가져와 사용
    web_paths = artwork.rag_url

    # URL 형식이 올바른지 확인
    parsed_url = urlparse(web_paths)
    if not parsed_url.scheme:
        web_paths = 'https://' + web_paths  # 기본적으로 https를 추가

    try:
        loader = WebBaseLoader([web_paths]
        #    web_paths=web_paths,
        #    requests_kwargs={"headers": headers},
        #    bs_kwargs=dict(
        #        parse_only=bs4.SoupStrainer(
        #            "div",
        #            class_=("post-content", "post-title", "post-header")
        #        )
        #    ),
        )        
        docs = loader.load()
        if not docs:
            raise ValueError(f"No documents loaded from the given URL: {web_paths}")
    except Exception as e:
        print(f"Debug: Error while loading URL {web_paths}: {e}")
        raise ValueError(f"Could not load document from URL '{web_paths}': {e}")


    # 2) 텍스트 분할: 검색 성능 향상을 위해 문서를 작은 단위인 청크로 나눔
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    # 3) 벡터 저장소 설정: 문서의 벡터화된 버전을 크로마 벡터에 저장
    try:
        vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})
    except Exception as e:
        print(f"Error creating retriever: {e}")
        raise ValueError("Failed to create a retriever from the documents.")

    return retriever

# 명화 기반 GPT와 대화 생성 (RAG 통합)
def artwork_chat_with_gpt(session, user_message):
    # 명화 데이터 로드 및 검색기 설정
    retriever = load_and_retrieve_artwork_data(session.artwork)
    if retriever is None:
        return "Error: Could not retrieve artwork data. Please check the URL or try again later."

    # 1) Contextualize question(대화 맥락에 맞추어 사용자의 질문 다시 생성)
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    
    # 2) 답변 Chain (사용자가 입력한 질문과 외부 정보 검색하여 질문 답변)

    image_url = session.artwork.image_url
    image_prompt = f"Please describe the artwork shown in this image: {image_url}"
    image_description_result = llm.invoke(image_prompt)
    image_description = image_description_result if isinstance(image_description_result, str) else "No description available."
    

    answer_system_prompt = (
        "You are a museum docent for children, basically generate quenstions using Guides below"
        "and if the child gives a response that requires further explanation, "
        "you can add supplementary information in a way that's simple and easy for them to understand. "
        "Use the following pieces of retrieved context for explanation."
        "Use three sentences maximum and keep the answer concise in KOREAN"
        "\n\n"
        "{context}"
        "\n\n"
        "You are a museum docent assisting KOREAN elementary school students in appreciating art. Using the provided artwork information, "
        "engage in conversations that make the viewing experience interesting. Ask thoughtful questions and show empathy to help the students "
        "deeply immerse themselves in the art. Speak concisely, as if talking to an elementary school student. Don't use English"
        "\n\n"
        "## Tone Guide\n"
        "Speak casually as if talking to a close friend. Maintain an energetic, warm, and exciting atmosphere."
        "\n\n"
        "## Conversation Guide\n"
        "The entire conversation should be conducted in Korean."
        "All information should be based on the details provided below [art info]. Use the content specified in 'Description' under [Information] in the conversation."
        "Look at the picture and its description, then ask questions based on that. Questions should follow the [Conversation Learning Stages]. The order can change depending on the conversation flow."
        "Asking good questions is more important than strictly following the stages. Refer to the question examples below for guidance."
        "\n\n"
        "[Conversation Learning Stages]\n"
        "1. Observe the artwork closely and describe what you see.\n"
        "2. Express emotions or thoughts you feel from the artwork.\n"
        "3. Interpret the meaning of the artwork.\n"
        "4. Recall personal experiences related to the artwork.\n"
        "\n\n"
        "## Example Questions by Stage\n"
        "[Stage 1] How many chairs are in this picture? Where do you think the background is? What is this artwork made of? What situation do you think this depicts?\n"
        "[Stage 2] What does this artwork remind you of? How do the colors in this artwork make you feel?\n"
        "[Stage 3] What do you think the artist was trying to express? What do you think the artist felt while creating this artwork?\n"
        "[Stage 4] Have you ever painted a picture while camping like this artwork? What do you usually do in your room?\n"
        "\n\n"
        "## Handling Inappropriate Language\n"
        "If any hate or discriminatory expressions appear during the conversation, explain to the student that such expressions should not be used and why they are harmful."
        "\n\n"
        "## Ending the Conversation\n"
        "Ensure that the conversation does not continue indefinitely. After a few rounds of questions and responses, bring the conversation to a close. "
        "You can use the following steps to end the conversation:\n"
        "1. Summarize what was discussed and appreciated about the artwork.\n"
        "2. Thank the student for their participation and engagement.\n"
        "3. Encourage them to explore more artworks and express their own thoughts and creativity.\n"
        "4. 대화를 종료할 때 “그림 그리러 가자!” 라고 말하세요.\n\n"
        
        "Here is the information about the artwork:[art info]\n"
        f"Artwork: {session.artwork.title} by {session.artwork.artist}, "
        f"created in {session.artwork.year}. Description: {session.artwork.description} "
        "Please refer to the image_description and provide insights based on what you see in the image.\n\n"
        f"image_decription : {image_description}"
    )
    answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", answer_system_prompt), # 시스템 프롬프트
            MessagesPlaceholder("chat_history"), # 이전 대화 기록
            ("human", "{input}"), # 사용자 입력
    
        ]    
    )
    question_answer_chain = create_stuff_documents_chain(llm, answer_prompt)

    # Create the rag chain (history_aware + qa chain 통합 : 사용자의 질문 맥락에 맞추어 명확화, 필요 정보 검색, 최종 답변 생성!)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    # 현재 세션에 저장된 chat_history 불러오기
    if session.chat_history:
        chat_history = json.loads(session.chat_history)
    else:
        chat_history = []

    # RAG 체인 호출하여 응답 생성
    state = {
        "input": user_message,
        "chat_history": [
            HumanMessage(content=message["content"]) if message["role"] == "user" else AIMessage(content=message["content"])
            for message in chat_history
        ],
        "context": "",
        "answer": "",
    }

    result = rag_chain.invoke(state)
    gpt_response = result["answer"]

    # 대화 기록 업데이트
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": gpt_response})
    # 대화 기록을 문자열로 변환하여 데이터베이스에 저장
    session.chat_history = json.dumps(chat_history)
    session.save()

    return gpt_response