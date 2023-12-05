from uuid import uuid4

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.models import Group, User
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.list import ListView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail

from app.forms import SignupForm
from app.models import CustomUser
from app.utils.helpers import check_token
from projectmanagement.settings import EMAIL_HOST_USER
from .models import Task, Stage, Project, UserProject
from .forms import TaskForm
from .helper import is_in_group


def signUp(request):
    form = SignupForm()

    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                new_user = form.save()

                verify_token = uuid4()
                CustomUser.objects.create(user=new_user, verify_token=verify_token)
                mail_subject = 'Activate your account.'
                verify_url = reverse('verify', kwargs={'uidb64': urlsafe_base64_encode(force_bytes(new_user.pk)),
                                                       'token': str(verify_token)})
                mail_message = f'Hi {new_user.username}, Please use this link to verify your account\n' \
                               f'{request.build_absolute_uri(verify_url)}'
                from_email = EMAIL_HOST_USER
                send_mail(
                    mail_subject,
                    mail_message,
                    from_email,
                    [new_user.email],
                    fail_silently=False
                )

            return HttpResponse(_('Please confirm your email address to complete the registration'))

    context = {
        'form': form,
    }

    return render(request, 'registration/signup.html', context)


def verify(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse(_('Thank you for your email confirmation. Now you can login your account.'))
    else:
        return HttpResponse(_('Activation link is invalid!'))


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


def render_task_by_stage(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    tasks = Task.objects.filter(stage_id=stage_id)
    template = loader.get_template("tasks.html")
    context = {
        "stage": stage,
        "tasks": tasks,
    }
    return HttpResponse(template.render(context, request))


def render_all_task(request):
    tasks = Task.objects.all()
    template = loader.get_template("app/tasks.html")
    context = {
        "tasks": tasks,
    }
    return HttpResponse(template.render(context, request))


@user_passes_test(is_in_group)
@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("tasks")
    else:
        form = TaskForm()

    return render(request, "create_task.html", {"form": form})


class ProjectDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Project
    permission_required = "app.project.can_delete_project"
    success_url = reverse_lazy("project")


class ProjectListView(ListView):
    model = Project
    queryset = Project.objects.all()
    context_object_name = "project_list"
    template_name = "app/project_list.html"
