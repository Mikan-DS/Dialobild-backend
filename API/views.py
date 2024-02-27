import typing
from urllib.parse import urlencode

from django.conf import settings
from django.core import serializers
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from oauth2_provider.decorators import protected_resource

from API.models import Project, Node, RuleType
from users.models import User


@protected_resource()
def get_resource_owner(request):
    return request.resource_owner


def either_login_required(func):
    def wrapper(request, *args, **kwargs):
        oauth2_client = get_resource_owner(request)
        if isinstance(oauth2_client, User):
            request.user = oauth2_client
        if request.user.is_authenticated:
            return func(request, *args, **kwargs)
        else:
            query_string = urlencode({'next': request.path})
            url = '{}?{}'.format(settings.LOGIN_URL, query_string)
            return redirect(url)

    return wrapper


@csrf_exempt
@either_login_required
def projects(request):
    # Здесь вы можете обработать данные POST
    user = request.user
    data = dict(map(lambda project: (project.id, project.name), user.projects.all()))
    return JsonResponse(data)


@csrf_exempt
@either_login_required
def create_project(request, project_name=None):
    if project_name is None:
        if request.POST:
            project_name = request.POST.get('project_name')
        if request.GET:
            project_name = request.GET.get('project_name')

    if not project_name:
        return JsonResponse({'error': "Project name not set"})

    user = request.user

    try:  # TODO добавить обработку ситуации когда у пользователя уже есть проект с таким названием
        project = Project(name=project_name, owner=user)
        project.save()
    except Exception as e:
        print(repr(e))
        return JsonResponse({'error': "Something went wrong"})

    return JsonResponse({'error': 0, 'project_name': project.name, 'project_id': project.id})

@csrf_exempt
@either_login_required
def get_full_project_by_name(request, project_name):
    project = Project.objects.filter(name = project_name, owner = request.user).first()
    if project:
        return get_project(request, project)
    return JsonResponse({'error': "No project found"})
@csrf_exempt
@either_login_required
def get_full_project_by_id(request, project_id):
    project = Project.objects.filter(id = project_id, owner = request.user).first()
    if project:
        return get_project(request, project)
    return JsonResponse({'error': "No project found"})


def get_project(request, project: Project):

    return JsonResponse({
        'error': 0,
        'project_name': project.name,
        'nodes': project.nodes_json_format,
        'nodeTypes': project.node_types_json_format,
        'ruleTypes': project.rule_types_json_format,

    })
