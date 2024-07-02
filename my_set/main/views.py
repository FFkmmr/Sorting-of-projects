from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from .models import Project, Technology, Industry, MySets, User
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .forms import CreateUserForm, CreateProjectForm, CreateProjectSet
from django.db import transaction
import json
import csv

def register_page(request):
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
def login_page(request):
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
def logout_user(request):
    logout(request)
    return redirect('login')
@login_required(login_url='login')
def index(request):
    technologies = Technology.objects.filter(project__user=request.user).distinct()
    industries = Industry.objects.filter(project__user=request.user).distinct()
    projects = Project.objects.filter(user=request.user)
    context = {
        'technologies': technologies,
        'industries': industries,
        'projects': projects,
    }
    return render(request, 'main/index.html', context)

@csrf_exempt
@login_required(login_url='login')
def project_filter_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_industries = data.get('industries', [])
            selected_technologies = data.get('technologies', [])
            active_button = data.get('active_button', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        filters = {'user': request.user}
        
        if selected_industries:
            filters['industries__name__in'] = selected_industries
        if selected_technologies:
            filters['technologies__name__in'] = selected_technologies
        if active_button == 'Public':
            filters['is_private'] = False
        elif active_button == 'Private':
            filters['is_private'] = True

        projects = Project.objects.filter(**filters)
        sets = MySets.objects.all()
        context = {
            'sets': sets,
            'projects': projects,
        }
        print(filters)
        if active_button == 'MySets':
            html = render_to_string('main/sets.html', context)
        else:
            html = render_to_string('main/projects.html', context)
        return JsonResponse({'html': html})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required( login_url = 'login' )
def import_csv_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        fs = FileSystemStorage()
        filename = fs.save(csv_file.name, csv_file)
        file_path = fs.path(filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                with transaction.atomic():
                    for row in reader:
                        project = Project(
                            title=row['title'],
                            url=row['url'],
                            description=row['description'].strip(),
                            user=request.user,
                        )
                        project.save()
                        tech_names = row['technologies'].split(',')
                        industry_names = row['industries'].split(',')
                        technologies = []
                        for tech_name in tech_names:
                            technology, created = Technology.objects.get_or_create(name=tech_name.strip())
                            technologies.append(technology)
                        industries = []
                        for industry_name in industry_names:
                            industry, created = Industry.objects.get_or_create(name=industry_name.strip())
                            industries.append(industry)
                        project.technologies.set(technologies)
                        project.industries.set(industries)
            return redirect('home')
        except Exception as e:
            return HttpResponse(f"Error: {e}")
    return render(request, 'import_csv.html')


@login_required(login_url='login')
def add_project(request):
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
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    if request.method == 'POST':
        project.delete()
        return redirect('home')
    return render(request, 'delete_project.html', {'project': project})


@login_required(login_url='login')
def edit_project(request, project_id):
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
def add_set(request):
    if request.method == 'POST':
        form = CreateProjectSet(request.POST)
        if form.is_valid():
            set = form.save(commit=False)
            set.user = request.user
            set.save()
            form.save_m2m()
            return redirect('home')
    else:
        form = CreateProjectSet()
    return render(request, 'add_set.html', {'form': form})

@login_required(login_url='login')
def edit_project_set(request, set_id):
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
def project_set(request, set_id):
    set_instance = get_object_or_404(MySets, id=set_id, user=request.user)
    projects = set_instance.projects.filter(user=request.user)
    handler = set_instance.name

    context = {
        'projects': projects,
        'set': set_instance,
        'handler': handler,
    }
    return render(request, "main/one_set.html", context)
def success(request):
    return render(request, 'main/success.html')

def error(request):
    return render(request, 'main/error.html')



















