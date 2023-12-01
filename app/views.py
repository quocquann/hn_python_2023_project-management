from .models import Project, UserProject
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.models import Group, User


# Create your views here.


class ProjectCreate(CreateView):
    model = Project
    fields = ["name", "describe", "end_date", "status"]

    def form_valid(self, form):
        project = form.save(commit=True)
        UserProject.objects.create(user=self.request.user, project=project, role=0)
        pm_group = Group.objects.get(name="PM")
        user = User.objects.get(pk=self.request.user.pk)
        user.groups.add(pm_group)
        return HttpResponseRedirect("project")
