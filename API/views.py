import json
import typing
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import QuerySet
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.decorators import protected_resource

from API.models import Project, Node, NodeRule
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
        'defaultRuleType': 'mustHave'

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

    project: typing.Union[Project, None] = None

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
    new_nodes = {}
    if saving_nodes == None:
        return JsonResponse({'error': 'Missing parameter "nodes"'}, status=400)

    nodes = project.nodes.all()
    nodes_for_delete = list(map(lambda x: x.id, nodes))

    node_types = {i.code: i.id for i in project.get_avalaible_node_types()}
    rule_types = {i.code: i.id for i in project.get_avalaible_rule_types()}

    modified = 0

    try:

        rules_after_created = {}

        for node in saving_nodes:
            node_entity: Node = nodes.filter(id=int(node["id"])).first()
            if node_entity:
                try:
                    if node_entity.x == 0 or node_entity.y == 0:
                        continue
                    nodes_for_delete.remove(node["id"])
                except ValueError:
                    pass

                if node_entity.get_js_format() != node:
                    modified += 1
                    node_entity.node_type_id = node_types[node["nodeType"]]
                    node_entity.content = node["content"]
                    node_entity.x, node_entity.y = node["location"]["x"], node["location"]["y"]

                    node_rules: QuerySet = node_entity.node_rules.filter(node=node_entity)
                    rules_for_delete: typing.List[int] = list(map(lambda x: x.id, node_rules))
                    for rule, nodes_links in node['rules'].items():

                        if rule in rule_types.keys():
                            rule_id = rule_types[rule]
                        else:
                            raise Exception('Unknown rule type')

                        for node_link in nodes_links:
                            rule_entity: NodeRule = node_rules.filter(
                                connected_node_id=node_link).first()
                            if rule_entity:
                                try:
                                    rules_for_delete.remove(rule_entity.id)
                                except ValueError:
                                    pass
                                rule_entity.rule_id = rule_id # Обновление правила если между двумя узлами оно уже есть
                                rule_entity.save()
                            else:
                                connected_node: Node = nodes.filter(id=int(node_link)).first()
                                if connected_node:
                                    NodeRule.objects.create(
                                        node=node_entity,
                                        rule_id=rule_id,
                                        connected_node=connected_node
                                    )
                                else:
                                    if not int(node_link) in rules_after_created:
                                        rules_after_created[int(node_link)] = []
                                    rules_after_created[int(node_link)].append((node_entity.id, rule_id))

                    else:
                        for rule_d in rules_for_delete:
                            node_rule: NodeRule = node_rules.filter(id=rule_d).first()
                            if node_rule:
                                node_rule.delete()

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
                new_nodes[int(node["id"])] = node_entity.id

                for rule, nodes_links in node['rules'].items():

                    if rule in rule_types.keys():
                        rule_id = rule_types[rule]
                    else:
                        raise Exception('Unknown rule type')
                    for node_link in nodes_links:
                        # NodeRule.objects.create(node=node_entity, rule_id=rule_id, connected_node_id=node_link)
                        # connected_id = new_nodes[int(node_link)] if int(node_link) in new_nodes else
                        connected_node: Node = nodes.filter(id=int(node_link)).first()
                        if connected_node:
                            NodeRule.objects.create(
                                node=node_entity,
                                rule_id=rule_id,
                                connected_node=connected_node
                            )
                        else:
                            if not int(node_link) in rules_after_created:
                                rules_after_created[int(node_link)] = []
                            rules_after_created[int(node_link)].append((node_entity.id, rule_id))
                if node["id"] in rules_after_created.keys():
                    for node_id, rule_id in rules_after_created[node_entity.id]:
                        NodeRule.objects.create(connected_node=node_entity, rule_id=rule_id, node_id=node_id)
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
        "modified": modified,
        "added": len(new_nodes),
        "new_nodes_ids": new_nodes
    }, status=200)
