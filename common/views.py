from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth import get_user_model
from .models import UserProfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json



# Create your views here.
def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # 아이디 중복 확인
        exist_user = get_user_model().objects.filter(username=username)
        if exist_user.exists():
            return render(request, 'signup.html', {'error': '아이디가 이미 존재합니다.'})
        
        # 비밀번호 일치 확인
        if password1 != password2:
            return render(request, 'signup.html', {'error': '비밀번호가 일치하지 않습니다.'})
        
        # 아이디 중복이 없고 비밀번호가 일치할 때 사용자 생성
        user = User.objects.create_user(
            username=username,
            password=password1
        )
        auth.login(request, user)
        return redirect('letter')
    
    return render(request, "signup.html")

@csrf_exempt
def login(request):
    if request.method == "POST":
        # request.POST.get()을 사용하여 필드가 존재하는지 확인
        username = request.POST.get('user_id')
        password = request.POST.get('pw')

        # 필수 값이 없을 경우 에러 메시지 반환
        if not username or not password:
            return render(request, "login.html", {
                'error': '아이디와 비밀번호를 모두 입력해주세요.',
            })

        # 유저 인증 시도
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            # 인증 성공 시 로그인 후 홈으로 리다이렉트
            auth.login(request, user)
            return redirect('home')
        else:
            # 인증 실패 시 에러 메시지 표시
            return render(request, "login.html", {
                'error': '아이디 또는 비밀번호가 잘못되었습니다.',
            })
    else:
        # GET 요청일 경우 로그인 페이지 렌더링
        return render(request, "login.html")

     
def home(request):
    return render(request, 'home.html')

def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        return redirect('home')
    return render(request, 'login.html')

def letter(request):
    return render(request, 'letter.html')

def enteruserinfo(request):
    if request.method == "POST":
        user_profile = request.user.profile
        user_profile.name = request.POST.get('name')
        user_profile.birthdate = request.POST.get('birthdate')
        user_profile.gender = request.POST.get('gender')
        user_profile.clothing = request.POST.get('clothing')
        user_profile.hairstyle = request.POST.get('hairstyle')
        user_profile.save()

        return redirect('home')

    return render(request, 'enteruserinfo.html')


