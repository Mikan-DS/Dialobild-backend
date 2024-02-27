from django.urls import path
from . import views

urlpatterns = [
    path('projects/', views.projects, name='projects'),
    path('create_project/<str:project_name>/', views.create_project, name='create_project'),
    path('create_project/', views.create_project, name='create_project_with_param'),
    path('project/<str:project_name>/', views.get_full_project_by_name, name='get_full_project_by_name'),
    path('project/<int:project_id>/', views.get_full_project_by_id, name='get_full_project_by_id'),
]
