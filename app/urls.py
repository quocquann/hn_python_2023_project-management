from django.urls import path
from . import views


urlpatterns = [path("create", views.ProjectCreate.as_view(), name="create-project")]
