## 🖥️About This Repository

이 리포지토리에는 QnArt 앱의 Django 기반 백엔드 소스 코드를 포함합니다. 이 리포지토리는 account, docent, imagegen, masterpiece 등 여러 앱을 포함하고 있습니다:

#### 주요 APP의 역할

- **`account/`**: 로그인, 회원 가입, 사용자 정보 관리
- **`docent/`**: 도슨트 정보 반환/변경
- **`imagegen/`**: 사용자의 프롬프트로 DALL-E 그림 창작
- **`masterpiece/`**: 오늘의 명화 카드 생성, 도슨트와의 감상 대화 생성/저장

## 🔨How to build

1. 저장소 클론</br>

```bash
git clone https://github.com/Wild-Gaori/backend.git</br>
 cd backend
```

2. 프로젝트 실행을 위해 필요한 Python 패키지 설치</br>

```bash
pip install -r requirements.txt
```

3. OpenAI API Key 생성 후, 루트 디렉토리에 `.env` 파일에 저장</br>

```bash
OPENAI_API_KEY=PASTE_YOUR_API_KEY
```

4. Access the app in your web browser at local host : http://localhost:8000/
```bash
python.py runserver
```

## How to install
- 프론트엔드 리포지토리: [QnArt-backend](https://github.com/Wild-Gaori/backend)
  
## How to test

## Stack
<img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/django-092E20?style=for-the-badge&logo=django&logoColor=white">
<img src="https://img.shields.io/badge/amazonaws-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white">
<img src="https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=MySQL&logoColor=white"/></a> &nbsp 

## 🌐Used Open Source
- https://openai.com/
- https://www.langchain.com/langchain
