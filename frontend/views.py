from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
def app(request, project_id=None):
    return render(request, "frontend/dialobild-app.html")