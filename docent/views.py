# docent/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from account.models import UserProfile  # UserProfile 모델을 account 앱에서 가져옵니다.
from django.contrib.auth.models import User
from docent.models import Docent
from rest_framework.permissions import IsAuthenticated

#현재 도슨트 정보 반환 함수
class GetSelectedDocent(APIView):
    #permission_classes = [IsAuthenticated]  # 인증(로그인)된 사용자만 접근 가능

    def post(self, request):
        user_pk = request.data.get('user_pk')

        if not user_pk:
            return Response({"error": "user_pk is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # UserProfile을 user_pk로 조회
            user_profile = UserProfile.objects.get(user__pk=user_pk)
            selected_docent_id = user_profile.selected_docent_id
            return Response({"selected_docent_id": selected_docent_id}, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
#도슨트 변경 함수
class UpdateSelectedDocent(APIView):
    #permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def post(self, request):
        user_pk = request.data.get('user_pk')
        selected_docent_id = request.data.get('selected_docent_id')

        if not user_pk or not selected_docent_id:
            return Response({"error": "user_pk and selected_docent_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # UserProfile을 user_pk로 조회
            user_profile = UserProfile.objects.get(user__pk=user_pk)
            
            # 새로운 도슨트를 selected_docent_id로 설정
            new_docent = Docent.objects.get(pk=selected_docent_id)
            user_profile.selected_docent = new_docent
            user_profile.save()

            # 변경된 도슨트의 docent_intro 반환
            docent_intro = new_docent.docent_intro

            return Response({"message": "Selected docent updated successfully.", "docent_intro": docent_intro}, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response({"error": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)

        except Docent.DoesNotExist:
            return Response({"error": "Docent not found."}, status=status.HTTP_404_NOT_FOUND)
