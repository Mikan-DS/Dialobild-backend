from django.urls import path

from . import views

urlpatterns = [
    path('', views.app, name='app'),
    path('projects/<int:project_id>/', views.app, name='app'),
]
