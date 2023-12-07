from uuid import uuid4

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.models import User
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import (
    user_passes_test,
    login_required,
)
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail

from projectmanagement.settings import EMAIL_HOST_USER
from .models import Task, Stage, Project, UserProject, CustomUser, UserStage, Report
from .forms import SignupForm, TaskForm, AddUserToProjectForm
from .utils.helpers import (
    check_token,
    is_pm,
    is_in_project,
    is_in_group,
    is_stage_member_or_pm,
)
from .utils import constants
from django.core.exceptions import PermissionDenied


def signUp(request):
    form = SignupForm()

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                new_user = form.save()

                verify_token = uuid4()
                CustomUser.objects.create(user=new_user, verify_token=verify_token)
                mail_subject = "Activate your account."
                verify_url = reverse(
                    "verify",
                    kwargs={
                        "uidb64": urlsafe_base64_encode(force_bytes(new_user.pk)),
                        "token": str(verify_token),
                    },
                )
                mail_message = (
                    f"Hi {new_user.username}, Please use this link to verify your account\n"
                    f"{request.build_absolute_uri(verify_url)}"
                )
                from_email = EMAIL_HOST_USER
                send_mail(
                    mail_subject,
                    mail_message,
                    from_email,
                    [new_user.email],
                    fail_silently=False,
                )

            return HttpResponse(
                _("Please confirm your email address to complete the registration")
            )

    context = {
        "form": form,
    }

    return render(request, "registration/signup.html", context)


def verify(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse(
            _("Thank you for your email confirmation. Now you can login your account.")
        )
    else:
        return HttpResponse(_("Activation link is invalid!"))


class ProjectCreate(LoginRequiredMixin, CreateView):
    model = Project
    fields = ["name", "describe", "end_date", "status"]

    def form_valid(self, form):
        project = form.save(commit=True)
        UserProject.objects.create(
            user=self.request.user, project=project, role=constants.PROJECT_MANAGER
        )
        return HttpResponseRedirect(reverse_lazy("project"))


class ProjectUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    fields = ["name", "describe", "end_date", "status"]
    success_url = reverse_lazy("project")

    def test_func(self):
        return is_pm(self.request.user, self.get_object())


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


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if is_pm(user=request.user, project=project):
        project.delete()
        return HttpResponse(_("Delete successfully"))
    else:
        raise PermissionDenied()


class ProjectListView(ListView):
    model = Project
    queryset = Project.objects.filter(status=constants.ACTIVE)
    context_object_name = "project_list"
    template_name = "app/project_list.html"


class ProjectDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        return is_in_project(user=self.request.user, project=self.get_object())

    model = Project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_projects"] = UserProject.objects.filter(project=self.get_object())
        stages = Stage.objects.filter(project=self.get_object())
        context["stages"] = stages
        context["task_count"] = Task.objects.filter(stage__in=stages).count()
        return context


@user_passes_test(is_in_group)
@login_required
def delete_task(request, pk):
    success_url = reverse_lazy("tasks")
    task = get_object_or_404(Task, pk=pk)
    task.delete()
    return HttpResponse(_("Delete successfully"))


class StageCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    def test_func(self):
        return is_pm(self.request.user, self.kwargs.get("project_id"))

    model = Stage
    fields = ["name", "start_date", "end_date", "user"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["user"].label = "Stage Owner"

        return form

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs.get("project_id"))
        user = form.cleaned_data["user"].get()
        stage = form.save(commit=False)
        stage.project = project
        stage.save()

        UserStage.objects.create(user=user, stage=stage, role=constants.STAGE_OWNER)
        return HttpResponseRedirect(
            reverse_lazy("project-detail", kwargs={"pk": project.pk})
        )


class StageDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        return is_stage_member_or_pm(user=self.request.user, stage=self.get_object())

    model = Stage

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_stages"] = UserStage.objects.filter(stage=self.get_object())
        context["tasks"] = Task.objects.filter(stage=self.get_object()).count()
        return context


@login_required
def AddUserToProject(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if is_pm(user=request.user, project=project):
        form = AddUserToProjectForm()
        if request.method == "POST":
            form = AddUserToProjectForm(request.POST)
            if form.is_valid():
                user = get_object_or_404(User, email=form.cleaned_data["email"])

                UserProject.objects.create(
                    user=user, project=project, role=form.cleaned_data["role"]
                )

                mail_subject = "Add to project"
                mail_message = _(
                    f"User have been already added to project {project} by {request.user}"
                )
                from_email = EMAIL_HOST_USER
                send_mail(
                    mail_subject,
                    mail_message,
                    from_email,
                    [user.email],
                    fail_silently=False,
                )
                return HttpResponseRedirect(
                    reverse_lazy("project-detail", kwargs={"pk": pk})
                )
            else:
                form = AddUserToProjectForm(initial={"email": form.email})
        context = {"form": form}
        return render(request, "app/add_user_to_project.html", context=context)
    else:
        raise PermissionDenied()


class MemberListView(ListView):
    template_name = "app/member_list.html"
    context_object_name = "list_member"

    def get_queryset(self):
        project_pk = self.kwargs.get("project_pk")
        project = get_object_or_404(Project, pk=project_pk)
        user_projects = (
            UserProject.objects.filter(project=project)
            .exclude(role=constants.PROJECT_MANAGER)
            .order_by("role")
        )
        return user_projects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_pk"] = self.kwargs.get("project_pk")
        return context


@login_required
def delete_member_from_project(request, project_pk, user_pk):
    user = get_object_or_404(User, pk=user_pk)
    project = get_object_or_404(Project, pk=project_pk)
    user_project = get_object_or_404(UserProject, user=user, project=project)

    if is_pm(user=request.user, project=project):
        stages = Stage.objects.filter(project=project)
        user_stage = UserStage.objects.filter(stage__in=stages)
        user_stage.delete()
        user_project.delete()
        return HttpResponse(_("Delete successfully"))
    else:
        raise PermissionDenied()


class UserUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    def test_func(self):
        return self.request.user.pk == self.get_object().pk

    model = User
    template_name = "app/user_detail.html"
    fields = ["username", "first_name", "last_name", "email"]
    success_url = reverse_lazy("project")


class CreateReport(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Report
    fields = ["content"]

    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs.get("project_pk"))
        return is_in_project(user=self.request.user, project=project)

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs.get("project_pk"))
        Report.objects.create(
            content=form.cleaned_data["content"],
            user=self.request.user,
            project=project,
        )

        user_project = UserProject.objects.filter(
            project=project, role=constants.PROJECT_MANAGER
        )
        pm = User.objects.get(pk=user_project[0].user.pk)

        mail_subject = f"{[project.name]} Report"
        mail_message = _(
            f"{self.request.user} have already created a report\n"
            f"{form.cleaned_data['content']}"
        )
        from_email = EMAIL_HOST_USER
        send_mail(
            mail_subject,
            mail_message,
            from_email,
            [pm.email],
            fail_silently=False,
        )
        return HttpResponseRedirect(reverse_lazy("project"))
