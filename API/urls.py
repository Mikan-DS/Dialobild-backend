from django.urls import path

from . import views

urlpatterns = [
    path('projects/', views.projects, name='projects'),
    path('create_project/<str:project_name>/', views.create_project, name='create_project'),
    path('create_project/', views.create_project, name='create_project_with_param'),
    path('project/id/<int:project_id>/', views.get_full_project_by_id, name='get_full_project_by_id'),
    path('project/name/<str:project_name>/', views.get_full_project_by_name, name='get_full_project_by_name'),
    path('project/save/', views.save_project, name='save_project'),
    path('project/add_raw_nodes/', views.add_raw_nodes, name='add_raw_nodes'),
]
