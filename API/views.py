import json
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
    project = Project.objects.filter(name=project_name, owner=request.user).first()
    if project:
        return get_project(request, project)
    return JsonResponse({'error': "No project found"})


@csrf_exempt
@either_login_required
def get_full_project_by_id(request, project_id):
    project = Project.objects.filter(id=project_id, owner=request.user).first()
    if project:
        return get_project(request, project)
    return JsonResponse({'error': "No project found"})


def get_project(request, project: Project):
    return JsonResponse({
        'error': 0,
        'project_name': project.name,
        'project_id': project.id,
        'nodes': project.nodes_json_format,
        'nodeTypes': project.node_types_json_format,
        'ruleTypes': project.rule_types_json_format,

    })


@csrf_exempt
@either_login_required
def save_project(request):
    try:
        if request.POST:
            data: typing.Dict = request.POST
        else:
            data_encoded = request.body.decode("utf-8")
            data: typing.Dict = json.loads(data_encoded)
    except UnicodeDecodeError:
        return JsonResponse({'error': 'Invalid Data'}, status=400)
    except json.decoder.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    project: Project

    try:
        if data.get('project_name'):
            project = Project.objects.filter(name=data['project_name']).first()
            if not project:
                return JsonResponse({'error': 'Project not found'}, status=404)
        elif data.get('project_id'):
            project = Project.objects.filter(id=int(data['project_id'])).first()
            if not project:
                return JsonResponse({'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Something went wrong, check project id or name'}, status=500)

    if not project:
        return JsonResponse({'error': 'Missing parameter "project_name" or "project_id"'}, status=400)



    saving_nodes = data.get('nodes')
    if not saving_nodes:
        return JsonResponse({'error': 'Missing parameter "nodes"'}, status=400)

    nodes = project.nodes.all()
    nodes_for_delete = list(map(lambda x: x.id, nodes))

    node_types = {i.code: i.id for i in project.get_avalaible_node_types()}

    modified = 0

    try:
        for node in saving_nodes:
            node_entity: Node = Node.objects.filter(id=int(node["id"])).first()
            if node_entity:
                nodes_for_delete.remove(node["id"])

                if node_entity.get_js_format() != node:
                    modified += 1
                    node_entity.node_type_id = node_types[node["nodeType"]]
                    node_entity.content = node["content"]
                    node_entity.x, node_entity.y = node["location"]["x"], node["location"]["y"]

                    # TODO: save rules

                node_entity.save()
            else:
                node_entity = Node(
                    node_type_id=node_types[node["nodeType"]],
                    content=node["content"],
                    x=node["location"]["x"],
                    y=node["location"]["y"],
                    project=project
                )
                node_entity.save()

        for node in nodes_for_delete:
            node_entity: Node = Node.objects.filter(id=int(node)).first()
            node_entity.delete()


    except Exception as e:
        return JsonResponse({'error': 'Something went wrong'}, status=500)

    project.save()

    return JsonResponse({
        'error': 0,
        "project_name": project.name,
        "deleted": len(nodes_for_delete),
        "modified": modified
    }, status=200)
