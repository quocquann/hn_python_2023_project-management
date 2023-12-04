from django.urls import path
from . import views


urlpatterns = [
    path("create", views.ProjectCreate.as_view(), name="create-project"),
    path("<int:pk>/update", views.ProjectUpdate.as_view(), name="update-project"),
]
