from .models import Project, UserProject
from django.shortcuts import render,redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from .models import Task,Stage,Project
from .forms import TaskForm
from .helper import is_in_group
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


def render_task_by_stage(request,stage_id):
      stage = get_object_or_404(Stage, pk=stage_id)
      tasks = Task.objects.filter(stage_id=stage_id)
      template = loader.get_template('tasks.html')
      context = {
      'stage':stage,
      'tasks': tasks,
      }
      return HttpResponse(template.render(context, request))

def render_all_task(request):
      tasks = Task.objects.all()
      template = loader.get_template('app/tasks.html')
      context = {
            'tasks':tasks,
            }
      return HttpResponse(template.render(context, request))
@user_passes_test(is_in_group)
@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tasks')  
    else:
        form = TaskForm()

    return render(request, 'create_task.html', {'form': form})
