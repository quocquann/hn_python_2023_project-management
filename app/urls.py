from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project"),
    path("<int:pk>", views.ProjectDetail.as_view(), name="project-detail"),
    path("create", views.ProjectCreate.as_view(), name="create-project"),
    path("<int:pk>/update", views.ProjectUpdate.as_view(), name="update-project"),
    path("<int:pk>/delete", views.project_delete, name="delete-project"),
    path("tasks/", views.render_all_task, name="tasks"),
    path("stage/tasks/<int:stage_id>", views.render_task_by_stage, name="task-stage"),
    path("task/create", views.create_task, name="create_task"),
    path("signup/", views.signUp, name="signup"),
    path("verify/<uidb64>/<str:token>/", views.verify, name="verify"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/signin.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("delete_task/<int:pk>", views.delete_task, name="delete_task"),
    path(
        "<int:project_id>/stages/create/",
        views.StageCreateView.as_view(),
        name="create-stage",
    ),
    path(
        "<int:project_id>/stages/<int:pk>/",
        views.StageDetailView.as_view(),
        name="detail-stage",
    ),
    path(
        "<int:project_id>/stages/<int:pk>/update/",
        views.StageUpdateView.as_view(),
        name="update-stage",
    ),
    path(
        "<int:project_id>/stages/<int:pk>/delete/",
        views.delete_stage,
        name="delete-stage",
    ),
    path("<int:pk>/addUser", views.AddUserToProject, name="add-user-to-project"),
    path(
        "<int:project_id>/stages/<int:pk>/member/",
        views.StageMemberListView.as_view(),
        name="stage-member",
    ),
    path(
        "<int:project_id>/stages/<int:pk>/member/add/",
        views.add_member_to_stage,
        name="add-member-to-stage",
    ),
]
