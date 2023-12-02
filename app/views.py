from .models import Project, UserProject
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin


# Create your views here.


class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    fields = ["name", "describe", "end_date", "status"]

    def form_valid(self, form):
        project = form.save(commit=True)
        UserProject.objects.create(user=self.request.user, project=project, role=0)
        pm_group = Group.objects.get(name="PM")
        user = User.objects.get(pk=self.request.user.pk)
        user.groups.add(pm_group)
        return HttpResponseRedirect(reverse_lazy("project"))


class ProjectUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Project
    fields = ["name", "describe", "end_date", "status"]
    permission_required = "app.project.can_change_project"
    success_url = reverse_lazy("project")
