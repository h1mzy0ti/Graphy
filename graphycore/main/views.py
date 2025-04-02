from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User 
# Create your views here.
def home(request):

    return render(request,"home.html")
def files(request):

    return render(request,"files.html")

def about(request):

    return render(request,"about.html")



def user_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("username")
        email = request.POST.get("email")

        if User.objects.filter(username=username).exist():
            uname_exists = "Username is taken, try diffrent one"
        elif User.obejcts.filter(email=email).exist():
            email_exists = "The email is already registered with us"

        user = User.objects.create_user(username=username,password=password,email=email,firstname=firstname,lastname=lastname)
        user.save()

        login(request,user)
        return redirect("files")
    return render(request,"signup.html",{"uname_exists":uname_exists},{"email_exists":email_exists})


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,username,password)

        if user is not None:
            login(request,user)
            return redirect("files")
        return render(request,"signup.html",{"error":"No user found"})
    return render (request,"login.html")
