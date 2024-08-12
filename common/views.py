from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth import get_user_model
from .models import UserProfile

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

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            return render(request, "login.html", {
                'error': '아이디 또는 비밀번호가 잘못되었습니다.',
            })
    else:
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

#def enter_user_info(request):
#    return render(request, "enteruserinfo.html")
