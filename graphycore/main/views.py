from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
# Create your views here.
def home(request):

    return render(request,"home.html")

@login_required(login_url='/login/')
def files(request):

    return render(request,"files.html")

def about(request):

    return render(request,"about.html")

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)
def pricing(request):
    return render(request,"pricing.html")
def user_signup(request):
    if request.user.is_authenticated:
        return redirect("files") 
    uname_exists = None  
    email_exists = None 
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")

        if User.objects.filter(username=username).exists():
            uname_exists = "Username is taken, try a different one"
        if User.objects.filter(email=email).exists():
            email_exists = "The email is already registered with us"

        user = User.objects.create_user(username=username,password=password,email=email)
        user.save()

        login(request,user)
        return redirect("files")
    return render(request,"signup.html",{"uname_exists": uname_exists, "email_exists": email_exists})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("files") 
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,username,password)

        if user is not None:
            login(request,user)
            return redirect("files")
        return render(request,"signup.html",{"error":"No user found"})
    return render (request,"login.html")
