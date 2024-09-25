from django.contrib.auth.models import User
from django.contrib import auth
from django.views import View
from .models import UserProfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import UserProfileSerializer

# 로그인 함수
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # 필수 값 확인
        if not username or not password:
            return Response({'error': 'Please provide both username and password.'}, status=status.HTTP_400_BAD_REQUEST)

        # 유저 인증 시도
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return Response({'message': 'Login successful', 'redirect_url': 'home'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def get(self, request):
        return Response({'message': 'Login page'}, status=status.HTTP_200_OK)

# 회원가입 함수   
@method_decorator(csrf_exempt, name='dispatch')
class SignupView(APIView):
    def post(self, request):
        action = request.data.get('action')
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

            # 필드 확인
            if not all([username, password, password_confirm, email]):
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

# 프로필 업데이트 함수
class UserProfileUpdateView(APIView):
    def post(self, request):
        user = request.user  # 현재 로그인한 사용자
        user_profile = user.profile  # 이미 생성된 UserProfile 가져오기

        serializer = UserProfileSerializer(user_profile, data=request.data)
        if serializer.is_valid():
            serializer.save()  # 유효성 검사 후 저장
            return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)