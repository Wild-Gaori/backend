# QnArt : 초등학생 대상, 대화와 그림 창작 기반 - 미술 작품 감상 서비스

![Frame 1](https://github.com/user-attachments/assets/e1113e6f-f32e-497d-a8f5-620144925e95)

## 🎨Introduction

QnArt는 주입식 설명 위주의 수동적인 미술작품 감상, 어려운 드로잉 창작 위주의 수업으로 미술에 흥미를 잃은 초등학생에게 즐겁고 주체적인 미술작품 감상 경험을 제공하는 애플리케이션입니다.<br>

#### 💬 AI 도슨트와 대화하며 작품 감상

명화 작품 데이터를 가진 AI 도슨트와 채팅 또는 음성으로 대화하며 작품을 감상합니다. AI 도슨트는 미술 교육 이론에 기반하여 사용자에게 작품에 관한 질문을 던지고, 사용자는 질문에 답하며 작품을 깊게 감상합니다.

#### 🖌️ 이미지 생성 AI로 그림 창작

대화 감상이 끝나면, 감상에서 떠올린 자신의 경험이나 상상을 말로 표현합니다. 이미지 생성 AI로 다양한 방식으로 그림을 창작합니다.

## 🖥️About This Repository

이 리포지토리는 QnArt 앱의 Django 기반 백엔드 소스 코드를 포함합니다. 이 리포지토리는 account, docent, imagegen, masterpiece 등 여러 앱을 포함하고 있습니다:

#### 주요 APP의 역할

- **`account/`**: 로그인, 회원 가입, 사용자 정보 관리
- **`docent/`**: 도슨트 정보 반환/변경
- **`imagegen/`**: 사용자의 프롬프트로 DALL-E 그림 창작
- **`masterpiece/`**: 오늘의 명화 카드 생성, 도슨트와의 감상 대화 생성/저장

## 🔨How to build

1. Ubuntu 서버 접속</br>
AWS에서 EC2 인스턴스를 생성한 후, 아래 명령어를 통해 서버에 접속합니다:

```bash
ssh -i "your-key-pair.pem" ubuntu@ec2-your-public-IPv4-DNS.ap-northeast-2.compute.amazonaws.com
```

2. Python 및 필수 패키지 설치</br>
다음 명령어를 실행하여 Python과 필수 패키지를 설치합니다:

```bash
sudo apt-get update
sudo apt-get install build-essential python3 python3-pip
```

3. 소스 코드 클론</br>
프로젝트 소스 코드를 클론한 후 해당 디렉토리로 이동합니다:

```bash
git clone https://github.com/Wild-Gaori/backend.git</br>
cd backend
```

4. 가상환경 생성 및 활성화</br>

```bash
sudo apt-get install virtualenv
virtualenv -p python3 venv
source venv/bin/activate
```

5. 종속성 설치</br>

```bash
pip install -r requirements.txt
```

## 🤖How to install

1. 환경변수 설정 </br>
OpenAI API Key를 생성한 후, 루트 디렉토리에 .env 파일을 생성하여 다음과 같이 설정합니다:

```bash
OPENAI_API_KEY=PASTE_YOUR_API_KEY
```

2. 데이터베이스 업데이트 및 정적파일 수집

```bash
python manage.py migrate
python manage.py collectstatic
```

3. uwsgi 설치 및 설정</br>

```bash
pip install uwsgi
vi uwsgi.ini
```
- uWSGI 설정 파일 예시:
```bash
[uwsgi]
chdir=/home/ubuntu/backend
module=myproject.wsgi:application
master=True
pidfile=/tmp/project-master.pid
vacuum=True
max-requests=5000
daemonize=/home/ubuntu/backend/django.log
home=/home/ubuntu/backend/venv
virtualenv=/home/ubuntu/backend/venv
socket=/home/ubuntu/backend/uwsgi.sock
chmod-socket=666
```

4. nginx 설치 및 설정

```bash
sudo apt-get install nginx
sudo vi /etc/nginx/nginx.conf
sudo vi /etc/nginx/sites-enabled/default
```
- nginx.conf - 아래 내용 추가 삽입
```bash
user ubuntu;
...
http {
 upstream django {
   server unix:/home/ubuntu/backend/uwsgi.sock;       
 }
}
```
- default - 아래 내용 삭제
```bash
location {
    try_files $url $url/ =404;
}
```
- default - 아래 내용 추가 삽입
```bash
location {
        include /etc/nginx/uwsgi_params;
                uwsgi_pass django;
}
location /static/ {
        alias /home/ubuntu/backend/staticfiles/;
}
location /media/ {
        alias /home/ubuntu/backend/media/;
}
```

5. 서버 실행 후 재시작

```bash
python manage.py runserver 0.0.0.0:8000
sudo service nginx restart
```

## 📜How to test

1. APK 테스트</br>
프론트엔드와 백엔드가 통합된 APK 테스트는 [QnArt-frontend](https://github.com/Wild-Gaori/frontend)의 README를 참고해주세요.
    
2. 백엔드 테스트 </br>
로컬 서버에서 실행한 후, [API 명세서](https://hushed-sardine-663.notion.site/951413190ccb4976a5d74707ea56c233?v=48fdce11fcc94a1b8af216018b539e62)에 명시된 기능별 URL로 접속하여 예시 입력값으로 테스트를 진행합니다.
```bash
python manage.py runserver 0.0.0.0:8000
```

## 📊Used Data

**데이터베이스**: mySQL Database를 사용합니다. 
- [QnArt-Image](https://github.com/Wild-Gaori/Image) : 명화 작품 png 파일
- [QnArt-DB](https://github.com/Wild-Gaori/DB) : 명화 작품, 작가, 도슨트 정보 sql파일
![QnArt_DB2](https://github.com/user-attachments/assets/0efc1b74-af4d-40c0-8736-2524742c1383)

## 🛠️Stack
<img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/django-092E20?style=for-the-badge&logo=django&logoColor=white">
<img src="https://img.shields.io/badge/amazonaws-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white">
<img src="https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=MySQL&logoColor=white"/></a> &nbsp

## 🌐Used Open Source
이 프로젝트는 다음과 같은 오픈소스 라이브러리를 사용합니다:
- https://openai.com/
- https://www.langchain.com/langchain
