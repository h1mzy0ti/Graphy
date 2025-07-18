from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login,logout, authenticate,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User 
from django.conf import settings
from django.contrib import messages
from .utils import get_user_storage_usage
from django.utils.encoding import smart_str
from graphycore.graphy_engine import read_file, clean_dataframe, detect_and_plot
from django.http import FileResponse,Http404


import os
import datetime

# Create your views here.
def home(request):

    return render(request,"home.html")

@login_required(login_url='/login/')
def files(request):
    if request.session.get('file_uploaded', False):
        return redirect('dashboard')
    
    used = get_user_storage_usage(request.user)
    percent_used = round((used / 50) * 100)

    return render(request, "files.html", {
        'storage_used': used,
        'storage_total': 50,
        'storage_percent': percent_used
    })


# === Handle File Upload (no Django form) ===
from .models import UploadedFile  # your model class

@login_required(login_url='/login/')
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # Create user-based directory under /media/uploads/
        user_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', request.user.username)
        os.makedirs(user_dir, exist_ok=True)

        file_path = os.path.join(user_dir, uploaded_file.name)

        # Save uploaded file to disk
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Save file metadata in database
        UploadedFile.objects.create(
            user=request.user,
            name=uploaded_file.name,
            file=f'uploads/{request.user.username}/{uploaded_file.name}'  # relative to MEDIA_ROOT
        )

        # Mark session flag
        request.session['file_uploaded'] = True

        return redirect('dashboard')

    return redirect('files')



# === Show Dashboard After Upload ===
@login_required(login_url='/login/')
def dashboard_view(request):
    if not request.session.get('file_uploaded', False):
        return redirect('files')  # Prevent direct dashboard access

    used = get_user_storage_usage(request.user)
    percent_used = round((used / 50) * 100)


    return render(request, 'dashboard.html', {
    'file_uploaded': True,
    'user': request.user,
    'report_month': 'April, 2025',
    'storage_used': used,
    'storage_total': 50,
    'storage_percent': percent_used
    })



@login_required
def analytics_view(request):
    user = request.user
    files = UploadedFile.objects.filter(user=user)

    file_id = request.GET.get("analyze")
    file_to_analyze = None
    chart_files = []
    output_folder = os.path.join(settings.MEDIA_ROOT, 'charts', user.username)

    used = get_user_storage_usage(request.user)
    percent_used = round((used / 50) * 100)

    if file_id:
        try:
            file_to_analyze = UploadedFile.objects.get(id=file_id, user=user)
            file_path = os.path.join(settings.MEDIA_ROOT, file_to_analyze.file.name)

            # Make a unique folder for this file's charts (based on file name)
            base_name = os.path.splitext(file_to_analyze.name)[0]
            file_output_folder = os.path.join(output_folder, base_name)

            # If charts already exist, reuse them
            if not os.path.exists(file_output_folder) or not os.listdir(file_output_folder):
                os.makedirs(file_output_folder, exist_ok=True)

                # Process file and generate charts
                dfs = read_file(file_path)
                for sheet_name, df in dfs.items():
                    df = clean_dataframe(df)
                    detect_and_plot(df, output_folder=file_output_folder, sheet_name=sheet_name)

            # List existing charts
            chart_files = sorted([
                f for f in os.listdir(file_output_folder)
                if f.endswith((".png", ".html"))
            ])

        except UploadedFile.DoesNotExist:
            file_to_analyze = None

    return render(request, 'analytics.html', {
        'section': 'analytics',
        'files': files,
        'analyzed_file': file_to_analyze,
        'chart_files': chart_files,
        'media_url': settings.MEDIA_URL,
        'chart_folder': base_name if file_id else '',
        'user': user,
        'storage_used': used,
        'storage_total': 50,
        'storage_percent': percent_used
    })
@login_required
@require_POST
def clean_analyzed_data(request):
    user = request.user
    file_id = request.POST.get("file_id")  # optional for per-file cleanup
    chart_base_path = os.path.join(settings.MEDIA_ROOT, 'charts', user.username)

    if file_id:
        try:
            file_obj = UploadedFile.objects.get(id=file_id, user=user)
            folder_name = os.path.splitext(file_obj.name)[0]
            folder_path = os.path.join(chart_base_path, folder_name)

            if os.path.exists(folder_path):
                for f in os.listdir(folder_path):
                    os.remove(os.path.join(folder_path, f))
                os.rmdir(folder_path)  # remove folder itself if empty
                messages.success(request, f"Charts for '{file_obj.name}' cleaned.")
        except UploadedFile.DoesNotExist:
            messages.error(request, "File not found.")
    else:
        # Clean all chart folders for user
        if os.path.exists(chart_base_path):
            for subfolder in os.listdir(chart_base_path):
                sub_path = os.path.join(chart_base_path, subfolder)
                if os.path.isdir(sub_path):
                    for f in os.listdir(sub_path):
                        os.remove(os.path.join(sub_path, f))
                    os.rmdir(sub_path)
            messages.success(request, "All analyzed charts cleaned.")

    return redirect('analytics')

@login_required
def delete_file(request, file_id):
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)
        file_path = os.path.join(settings.MEDIA_ROOT, str(uploaded_file.file))

        # Delete from disk
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete from DB
        uploaded_file.delete()
        messages.success(request, "File deleted successfully.")
    except UploadedFile.DoesNotExist:
        messages.error(request, "File not found or already deleted.")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('uploaded')


@login_required
def uploaded(request):
    user = request.user
    files = UploadedFile.objects.filter(user=user)

    used = get_user_storage_usage(request.user)
    percent_used = round((used / 50) * 100)

    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        allowed_extensions = ['.csv', '.xls', '.xlsx']
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

        if file_ext not in allowed_extensions:
            messages.error(request, "Only CSV and Excel files (.csv, .xls, .xlsx) are allowed.")
            return redirect('uploaded')

        # Create user-specific upload directory
        user_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', user.username)
        os.makedirs(user_dir, exist_ok=True)

        file_path = os.path.join(user_dir, uploaded_file.name)

        # Save file to disk
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Save metadata to DB
        UploadedFile.objects.create(
            user=user,
            name=uploaded_file.name,
            file=f'uploads/{user.username}/{uploaded_file.name}'
        )

        messages.success(request, "File uploaded successfully.")
        request.session['file_uploaded'] = True
        return redirect('uploaded')

    return render(request, "uploaded.html", {
        'files': files,
        'storage_used': used,
        'storage_total': 50,
        'storage_percent': percent_used
    })

@login_required
def download_file(request, file_id):
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)
        file_path = os.path.join(settings.MEDIA_ROOT, str(uploaded_file.file))

        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=smart_str(uploaded_file.name))
            return response
        else:
            raise Http404("File not found")

    except UploadedFile.DoesNotExist:
        raise Http404("File does not exist or you don't have permission.")
    
@login_required
def search_view(request):
    query = request.GET.get('q', '')
    results = []

    used = get_user_storage_usage(request.user)
    percent_used = round((used / 50) * 100)

    if query:
        path = os.path.join(settings.MEDIA_ROOT, 'uploads', request.user.username)
        if os.path.exists(path):
            results = [f for f in os.listdir(path) if query.lower() in f.lower()]
    return render(request, 'search.html', {
        'section': 'search',
        'results': results,
        'query': query,
        'storage_used': used,
        'storage_total': 50,
        'storage_percent': percent_used
    })
@login_required
def logs_view(request):
    path = os.path.join(settings.MEDIA_ROOT, 'uploads', request.user.username)
    file_logs = []

    used = get_user_storage_usage(request.user)
    percent_used = round((used / 50) * 100)

    if os.path.exists(path):
        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            file_logs.append({
                'name': f,
                'uploaded_on': datetime.datetime.fromtimestamp(os.path.getctime(full_path))
            })

    return render(request, 'logs.html', {
        'section': 'logs',
        'storage_used': used,
        'storage_total': 50,
        'storage_percent': percent_used,
        'logs': sorted(file_logs, key=lambda x: x['uploaded_on'], reverse=True)
    })

def about(request):

    return render(request,"about.html")
def docs(request):
    return render(request,"docs.html")
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

@login_required
def logout_view(request):
    logout(request)
    return redirect("home")

@login_required
def profile_view(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")

        user = request.user
        user.set_password(new_password)
        update_session_auth_hash(request, user)
        


    return render(request,"profile.html")

