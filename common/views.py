from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login as auth_login
from django.views import View
from .models import UserProfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator



@csrf_exempt
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

# 로그인 함수
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        # request.data를 사용해 POST 데이터 처리 (DRF에서 제공)
        username = request.data.get('username')
        password = request.data.get('password')

        # 필수 값 확인
        if not username or not password:
            return Response({'error': '아이디와 비밀번호를 모두 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        # 유저 인증 시도
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            # 인증 성공 시 로그인 처리
            auth.login(request, user)
            return Response({'message': '로그인 성공', 'redirect_url': 'home'}, status=status.HTTP_200_OK)
        else:
            # 인증 실패 시 오류 반환
            return Response({'error': '아이디 또는 비밀번호가 잘못되었습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def get(self, request):
        # GET 요청일 경우 (예: 로그인 폼이 필요한 경우)
        return Response({'message': '로그인 페이지'}, status=status.HTTP_200_OK)

@csrf_exempt
def home(request):
    return render(request, 'home.html')

@csrf_exempt
def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        return redirect('home')
    return render(request, 'login.html')

@csrf_exempt
def letter(request):
    return render(request, 'letter.html')

@csrf_exempt
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


