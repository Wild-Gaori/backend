## 🖥️About This Repository

이 리포지토리에는 QnArt 앱의 Django 기반 백엔드 소스 코드를 포함합니다. 이 리포지토리는 account, docent, imagegen, masterpiece 등 여러 앱을 포함하고 있습니다:

#### 주요 APP의 역할

- **`account/`**: 로그인, 회원 가입, 사용자 정보 관리
- **`docent/`**: 도슨트 정보 반환/변경
- **`imagegen/`**: 사용자의 프롬프트로 DALL-E 그림 창작
- **`masterpiece/`**: 오늘의 명화 카드 생성, 도슨트와의 감상 대화 생성/저장

## 🔨How to build

1. Ubuntu 서버 접속</br>
AWS에서 ec2 인스턴스를 생성한 후, 프로젝트를 실행할 서버에 SSH로 접속합니다.

```bash
ssh -i "your-key-pair.pem" ubuntu@ec2-your-public-IPv4-DNS.ap-northeast-2.compute.amazonaws.com
```

2. Python, 필수 패키지 설치</br>

```bash
sudo apt-get update
sudo apt-get install build-essential
sudo apt-get install python3
sudo apt-get install python3-pip
```

3. 소스 코드 클론</br>

```bash
git clone https://github.com/Wild-Gaori/backend.git</br>
 cd backend
```

4. 가상환경 설치 및 실행</br>

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
OpenAI API Key 생성 후, 루트 디렉토리의 `.env` 파일에 저장합니다.

```bash
OPENAI_API_KEY=PASTE_YOUR_API_KEY
```

2. 데이터베이스 업데이트 후, 정적파일을 서버에 수집

```bash
python manage.py migrate
python manage.py collectstatic
```

3. uwsgi 설치 후, uwsgi.ini 파일 생성</br>
uwsgi : Django 애플리케이션과 WSGI(Web Server Gateway Interface)를 통해 연결되는 애플리케이션 서버입니다.</br>

```bash
pip install uwsgi
vi uwsgi.ini
```
uwsgi.ini 파일 내용
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

4. nginx 설치 후, nginx.conf, default 파일의 내용 편집</br>
nginx : HTTP 요청을 받아 애플리케이션 서버(uWSGI)로 전달하고 정적 파일 요청을 처리하는 리버스 프록시 서버입니다.</br>

```bash
sudo apt-get install nginx
sudo vi /etc/nginx/nginx.conf
```
nginx.conf 파일에 아래 내용 추가 삽입
```bash
user ubuntu;
...
http {
 upstream django {
   server unix:/home/ubuntu/backend/uwsgi.sock;       
 }
}
```
default 파일 생성
```bash
sudo vi /etc/nginx/sites-enabled/default
```
default 파일에서 아래 내용 삭제
```bash
location {
    try_files $url $url/ =404;
}
```
default 파일에 아래 내용 추가 삽입
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

5. 서버 실행

```bash
python manage.py runserver 0.0.0.0:8000
sudo service nginx restart
```

## 📜How to test

- 프론트엔드,백엔드가 통합된 apk 테스트 : [QnArt-frontend](https://github.com/Wild-Gaori/frontend) README 참고
    
- 백엔드 테스트 : 로컬 서버에서 실행 후, </br>
   [API 명세서](https://hushed-sardine-663.notion.site/951413190ccb4976a5d74707ea56c233?v=48fdce11fcc94a1b8af216018b539e62) : 각 기능의 url로 접속해 예시 입력값으로 테스트합니다.</br>
```bash
python manage.py runserver 0.0.0.0:8000
```

### About Sample Data

- 이미지 파일 : [QnArt-Image](https://github.com/Wild-Gaori/Image)
- 이미지, 작가, 도슨트 정보 sql파일 :  [QnArt-DB](https://github.com/Wild-Gaori/DB)

## Stack
<img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/django-092E20?style=for-the-badge&logo=django&logoColor=white">
<img src="https://img.shields.io/badge/amazonaws-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white">
<img src="https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=MySQL&logoColor=white"/></a> &nbsp 

## 🌐Used Open Source
- https://openai.com/
- https://www.langchain.com/langchain
