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

# 로그인 함수
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        # request.data를 사용해 POST 데이터 처리 (DRF에서 제공)
        username = request.data.get('username')
        password = request.data.get('password')

        # 필수 값 확인
        if not username or not password:
            return Response({'error': 'Please provide both username and password.'}, status=status.HTTP_400_BAD_REQUEST)

        # 유저 인증 시도
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            # 인증 성공 시 로그인 처리
            auth.login(request, user)
            return Response({'message': 'Login successful', 'redirect_url': 'home'}, status=status.HTTP_200_OK)
        else:
            # 인증 실패 시 오류 반환
            return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def get(self, request):
        # GET 요청일 경우 (예: 로그인 폼이 필요한 경우)
        return Response({'message': 'Login page'}, status=status.HTTP_200_OK)
    
#회원가입 함수   
@method_decorator(csrf_exempt, name='dispatch')
class SignupView(APIView):
    """
    Handles both username check and user registration based on action in request.
    """

    def post(self, request):
        action = request.data.get('action')  # 'check_username' or 'signup'
        username = request.data.get('username')

        # 아이디 중복 확인
        if action == 'check_username':
            if User.objects.filter(username=username).exists():
                return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'message': 'Username is available.'}, status=status.HTTP_200_OK)

        # 회원가입 로직
        if action == 'signup':
            password = request.data.get('password')
            password_confirm = request.data.get('password_confirm')
            email = request.data.get('email')

            # 입력 필드 확인
            if not username or not password or not password_confirm or not email:
                return Response({'error': 'Please fill out all fields.'}, status=status.HTTP_400_BAD_REQUEST)

            # 비밀번호 일치 확인
            if password != password_confirm:
                return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

            # 비밀번호 길이 검증 (4자리 이상)
            if len(password) < 4:
                return Response({'error': 'Password must be at least 4 characters long.'}, status=status.HTTP_400_BAD_REQUEST)

            # 사용자 생성
            user = User.objects.create_user(username=username, password=password, email=email)
            return Response({'message': 'Signup completed successfully.'}, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)


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
        user_profile.nickname = request.POST.get('nickname')
        user_profile.birthdate = request.POST.get('birthdate')
        user_profile.gender = request.POST.get('gender')
        user_profile.clothing = request.POST.get('clothing')
        user_profile.hairstyle = request.POST.get('hairstyle')
        user_profile.save()

        return redirect('home')

    return render(request, 'enteruserinfo.html')


