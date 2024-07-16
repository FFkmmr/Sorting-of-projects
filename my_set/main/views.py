import base64
import json
import requests


from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse, HttpRequest, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .forms import (
    CreateUserForm,
    CreateProjectForm,
    CreateProjectSet,
    PasswordResetRequestForm,
    SetPasswordForm,
)
from .models import Project, Technology, Industry, MySets
from .service import mailgun_api, email_from, import_csv, secret_key, email_message, send_mail, generate_token
import cryptocode



def register_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()
        
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            
            if form.is_valid():
                form.save()
                user = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for ' + user)
                return redirect('login')
            
        context = {'form': form}
        return render(request, 'main/register.html', context)


def login_page(request: HttpRequest) -> HttpResponse:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else: 
                messages.info(request, 'Username OR password is incorrect.')

        context = {}
        return render(request, 'main/login.html', context)


def logout_user(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def index(request: HttpRequest) -> HttpResponse:
    technologies = Technology.objects.filter(project__user=request.user).distinct()
    industries = Industry.objects.filter(project__user=request.user).distinct()
    projects = Project.objects.filter(user=request.user)
    context = {
        'technologies': technologies,
        'industries': industries,
        'projects': projects,
    }
    return render(request, 'main/index.html', context)


@login_required(login_url='login')
def project_filter_view(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_industries = data.get('industries', [])
            selected_technologies = data.get('technologies', [])
            active_button = data.get('active_button', [])
            input_val = data.get('input_val', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        sets_filters = { 'user': request.user }
        filters = {}
        other_filtered_projects = []        


        if selected_industries:
            filters['industries__name__in'] = selected_industries
        
        if selected_technologies:
            filters['technologies__name__in'] = selected_technologies
        
        if active_button == 'Public':
            filters['is_private'] = False
            filters.setdefault('user', request.user)

        if active_button == 'Private':
            filters['is_private'] = True
            filters.setdefault('user', request.user)

        
        projects = Project.objects.filter(**filters).distinct()
        sets = MySets.objects.filter(**sets_filters).distinct()

        
        if active_button == 'Other':
            for project in projects:
                if project.sets.exists():
                    for set in project.sets.all():
                        if request.user in set.allowed_for.all():
                            other_filtered_projects.append(project.id)
                            break
                else: 
                    filters['id__in'] = other_filtered_projects
        projects = Project.objects.filter(**filters).distinct()


        if input_val:
            for term in input_val.split():
                projects = projects.filter(title__icontains=term.strip())

        context = {
            'sets': sets,
            'projects': projects,
        }
        
        if active_button == 'MySets':
            html = render_to_string('main/sets.html', context)
        elif active_button == 'Other':
            html = render_to_string('main/other_projects.html', context)
        else:
            html = render_to_string('main/projects.html', context)
        return JsonResponse({'html': html})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required( login_url = 'login' )
def import_csv_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        fs = FileSystemStorage()
        filename = fs.save(csv_file.name, csv_file)
        file_path = fs.path(filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                import_csv(request.user, file)
            return redirect('home')
        except Exception as e:
            return HttpResponse(f"Error: {e}")
    return render(request, 'import_csv.html')


@login_required(login_url='login')
def add_project(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = CreateProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user  
            project.save()
            form.save_m2m() 

            new_technologies = form.cleaned_data.get('new_technologies')
            if new_technologies:
                tech_list = [tech.strip() for tech in new_technologies.split(',')]

                for tech_name in tech_list:
                    technology, created = Technology.objects.get_or_create(name=tech_name)
                    project.technologies.add(technology)

            new_industries = form.cleaned_data.get('new_industries')
            if new_industries:
                ind_list = [ind.strip() for ind in new_industries.split(',')]

                for ind_name in ind_list:
                    industry, created = Industry.objects.get_or_create(name=ind_name)
                    project.industries.add(industry)

            return redirect('home')
    else:
        form = CreateProjectForm()
    return render(request, 'add_project.html', {'form': form})


@login_required(login_url='login')
def delete_project(request: HttpRequest, project_id: int) -> HttpResponse:
    project = get_object_or_404(Project, id=project_id, user=request.user)

    if request.method == 'POST':
        project.delete()
        return redirect('home')
    return render(request, 'delete_project.html', {'project': project})


@login_required(login_url='login')
def edit_project(request: HttpRequest, project_id: int) -> HttpResponse:
    project = get_object_or_404(Project, id=project_id, user=request.user)

    if request.method == 'POST':
        form = CreateProjectForm(request.POST, instance=project)

        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CreateProjectForm(instance=project)
    return render(request, 'edit_project.html', {'form': form})


@login_required(login_url='login')
def add_set(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = CreateProjectSet(request.POST)

        if form.is_valid():
            set = form.save(commit=False)
            set.user = request.user
            set.save()
            form.save_m2m()

            generate_invitation_token(set.id, 'set', request.user.id)

            return redirect('home')
    else:
        form = CreateProjectSet()
    return render(request, 'add_set.html', {'form': form})


@login_required(login_url='login')
def edit_project_set(request: HttpRequest, set_id: int) -> HttpResponse:
    set_instance = get_object_or_404(MySets, id=set_id, user=request.user)

    if request.method == 'POST':
        form = CreateProjectSet(request.POST, instance=set_instance)

        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CreateProjectSet(instance=set_instance)
    context = {
        'set': set_instance,
        'form': form,
    }
    return render(request, 'edit_set.html', context)


@login_required(login_url='login')
def project_set(request: HttpRequest, set_id: int) -> HttpResponse:
    set_instance = get_object_or_404(MySets, id=set_id)
    if set_instance.is_private and set_instance.user != request.user:
        return HttpResponseForbidden("You do not have access to this set.")

    # Извлекаем переменную accept из сессии
    accept = request.session.get('accept', False)
    # Удаляем переменную из сессии после использования
    if 'accept' in request.session:
        del request.session['accept']

    projects = set_instance.projects.all()
    context = {
        'projects': projects,
        'set': set_instance,
        'handler': set_instance.name,
        'accept': accept,
    }
    return render(request, "main/one_set.html", context)


def generate_invitation_token(request: HttpRequest, set_id: int) -> HttpResponse:
    user_id = request.user.id
    data = {'user_id': user_id, 'set_id': set_id}
    json_data = json.dumps(data)
    encrypted_data = cryptocode.encrypt(json_data, secret_key)
    token_base64 = base64.urlsafe_b64encode(encrypted_data.encode()).decode()
    return render(request, 'share_link.html', {'token': token_base64})


def accept_invitation(request: HttpRequest, token: str) -> HttpResponse:
    try:
        token = base64.urlsafe_b64decode(token).decode()
        decrypted_data = cryptocode.decrypt(token, secret_key)
        data = json.loads(decrypted_data)
        set_id = data['set_id']
        set_instance = get_object_or_404(MySets, id=set_id)
        set_instance.allowed_for.add(request.user)

        request.session['accept'] = True
        
        return redirect('set', set_id=set_id)
    except Exception as e:
        return HttpResponseForbidden(e)


def send_message(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        email = request.POST.get('email')
        link = request.POST.get('link')
        email_send(email, link)
        return redirect('home')
    return render(request, 'template.html')


def email_send(email: str, link: str) -> requests.Response:
  	return email_message(email, link, email_from, mailgun_api)


def change_password_message(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.id))
            token = generate_token(user.id)

            reset_url = request.build_absolute_uri(f'/reset/{uidb64}/{token}/')

            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_url}',
                email_from,
                [email],
                mailgun_api,
            )
            return redirect('login')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'change_password_message.html', {'form': form})


def password_reset_confirm(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    
    if user is not None:
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                user = form.save()
                return redirect('login')
        else:
            form = SetPasswordForm(user)
        return render(request, 'password_reset_confirm.html', {'form': form})
    else:
        return render(request, 'login.html')


def profile(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'profile.html', context)


def edit_name(request):
    user = request.user
    context = { 'user': user }

    return render(request, 'edit_name.html', context)