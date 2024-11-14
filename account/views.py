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
            return Response({'message': 'Login successful', 'redirect_url': 'home', 'user_pk': user.pk}, status=status.HTTP_200_OK)
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
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import UserProfile
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class UpdateUserProfileView(APIView):
    def post(self, request):
        user_pk = request.data.get('user_pk')
        profile_data = request.data.get('profile_data')

        # 필수 값 확인
        if not user_pk or not profile_data:
            return Response({'error': 'Please provide both user_pk and profile_data.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 사용자 검색
            user = User.objects.get(pk=user_pk)
            user_profile, created = UserProfile.objects.get_or_create(user=user)

            # 프로필 업데이트
            nickname = profile_data.get('nickname')
            birthdate = profile_data.get('birthdate')
            gender = profile_data.get('gender')
            clothing = profile_data.get('clothing')
            hairstyle = profile_data.get('hairstyle')

            if nickname is not None:
                user_profile.nickname = nickname
            if birthdate is not None:
                user_profile.birthdate = birthdate
            if gender is not None:
                user_profile.gender = gender
            if clothing is not None:
                user_profile.clothing = clothing
            if hairstyle is not None:
                user_profile.hairstyle = hairstyle

            # 프로필 저장
            user_profile.save()

            return Response({'message': 'User profile updated successfully.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#저장된 사용자 프로필 정보 불러오는 함수
@method_decorator(csrf_exempt, name='dispatch')
class GetUserProfileView(APIView):
    def post(self, request):
        user_pk = request.data.get('user_pk')

        # 필수 값 확인
        if not user_pk:
            return Response({'error': 'Please provide user_pk.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 사용자 검색
            user = User.objects.get(pk=user_pk)
            try:
                user_profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                user_profile = None

            # 프로필 정보 반환
            response_data = {
                'nickname': user_profile.nickname if user_profile and user_profile.nickname is not None else '',
                'birthdate': user_profile.birthdate if user_profile and user_profile.birthdate is not None else '',
                'gender': user_profile.gender if user_profile and user_profile.gender is not None else '',
                'clothing': user_profile.clothing if user_profile and user_profile.clothing is not None else '',
                'hairstyle': user_profile.hairstyle if user_profile and user_profile.hairstyle is not None else '',
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
