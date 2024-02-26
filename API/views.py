from urllib.parse import urlencode

from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST, require_GET
from oauth2_provider.decorators import protected_resource

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


@either_login_required
def projects(request):
    # Здесь вы можете обработать данные POST
    user = request.user
    data = {"username": user.username}
    return JsonResponse(data)
