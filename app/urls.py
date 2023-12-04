from django.urls import path
from . import views


urlpatterns = [
    path("create", views.ProjectCreate.as_view(), name="create-project"),
    path("<int:pk>/update", views.ProjectUpdate.as_view(), name="update-project"),
    path('tasks/', views.render_all_task, name='tasks'),     
    path('stage/tasks/<int:stage_id>', views.render_task_by_stage, name='task-stage'),   
    path('task/create', views.create_task, name='create_task'),  
    ]
