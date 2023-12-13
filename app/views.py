from django.contrib import messages
from django.contrib.auth.decorators import (
    user_passes_test,
    login_required,
)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from projectmanagement.settings import EMAIL_HOST_USER
from .forms import (
    SignupForm,
    TaskForm,
    StageUpdateForm,
    AddUserToProjectForm,
    StageCreateForm,
)
from .models import Task, Stage, Project, UserProject, UserStage
from .utils import constants
from .utils.helpers import (
    check_token,
    is_pm,
    is_in_project,
    is_in_group,
    is_stage_member_or_pm,
    is_pm_or_stage_owner,
    send_mail_verification,
)


def signUp(request):
    form = SignupForm()

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                new_user = form.save()

                send_mail_verification(request, new_user)

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
        stage_active = stages.filter(status=constants.ACTIVE)
        stage_closed = stages.filter(status=constants.CLOSED)
        context["stage_active"] = stage_active
        context["stage_closed"] = stage_closed
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
    form_class = StageCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project_id"] = self.kwargs.get("project_id")
        return kwargs

    def form_valid(self, form):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, pk=project_id)
        user = form.cleaned_data["user"]
        stage = form.save(commit=False)
        stage.project = project
        stage.save()

        UserStage.objects.create(user=user, stage=stage, role=constants.STAGE_OWNER)
        UserProject.objects.filter(user=user, project=project).update(
            role=constants.STAGE_OWNER
        )

        success_url = reverse("project-detail", kwargs={"pk": project_id})
        return redirect(success_url)


class StageDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    def test_func(self):
        return is_stage_member_or_pm(user=self.request.user, stage=self.get_object())

    model = Stage

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_stages"] = UserStage.objects.filter(stage=self.get_object())
        context["tasks"] = Task.objects.filter(stage=self.get_object()).count()
        context["project_id"] = self.kwargs.get("project_id")
        return context


class StageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Stage
    form_class = StageUpdateForm

    def get_success_url(self):
        return reverse_lazy(
            "detail-stage",
            kwargs={"pk": self.object.pk, "project_id": self.kwargs.get("project_id")},
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project_id"] = self.kwargs.get("project_id")
        return kwargs

    def test_func(self):
        return is_pm(self.request.user, self.kwargs.get("project_id"))


@login_required
def delete_stage(request, project_id, pk):
    stage = get_object_or_404(Stage, pk=pk, project_id=project_id)
    if is_pm(user=request.user, project=stage.project):
        stage.delete()

        stage_data = model_to_dict(stage, exclude=["user"])

        num_stages = Stage.objects.filter(
            project=project_id, status=constants.ACTIVE
        ).count()

        return JsonResponse(
            {
                "message": _("Delete successfully"),
                "stage": stage_data,
                "num_stages": num_stages,
            },
            safe=False,
            status=200,
        )

    return JsonResponse(
        {
            "message": _("You don't have permission to delete this stage"),
        },
        safe=False,
        status=403,
    )


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


class StageMemberListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UserStage

    def test_func(self):
        stage = get_object_or_404(Stage, pk=self.kwargs.get("pk"))
        return is_stage_member_or_pm(user=self.request.user, stage=stage)

    def get_queryset(self):
        return UserStage.objects.filter(stage=self.kwargs.get("pk")).select_related(
            "user"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_id"] = self.kwargs.get("project_id")
        context["stage_id"] = self.kwargs.get("pk")


class MemberListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "app/member_list.html"
    context_object_name = "list_member"

    def test_func(self):
        project_pk = self.kwargs.get("project_pk")
        project = get_object_or_404(Project, pk=project_pk)
        return is_in_project(user=self.request.user, project=project)

    def get_queryset(self):
        project_pk = self.kwargs.get("project_pk")
        project = get_object_or_404(Project, pk=project_pk)
        user_projects = (
            UserProject.objects.filter(project=project)
            .order_by("role")
            .select_related("user")
        )
        return user_projects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_pk"] = self.kwargs.get("project_pk")
        return context


@login_required
def add_member_to_stage(request, project_id, pk):
    project = get_object_or_404(Project, pk=project_id)
    if not is_pm_or_stage_owner(user=request.user, stage=pk, project=project):
        messages.error(request, _("You don't have permission to do this"))
        return redirect("stage-member", project_id=project_id, pk=pk)

    user_in_project = UserProject.objects.filter(
        project=project,
        role=constants.MEMBER,
    )

    users_in_stage_list = (
        UserStage.objects.filter(stage=pk)
        .select_related("user")
        .values_list("user", flat=True)
    )
    user_in_project_ex = user_in_project.exclude(user__in=users_in_stage_list)

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, pk=user_id)
        stage = get_object_or_404(Stage, pk=pk)
        UserStage.objects.create(user=user, stage=stage, role=constants.MEMBER)

        mail_subject = "Add to stage"
        mail_message = _(
            f"User have been already added to stage {stage.name} of project {project} by {request.user}"
        )
        from_email = EMAIL_HOST_USER
        send_mail(
            mail_subject,
            mail_message,
            from_email,
            [user.email],
            fail_silently=False,
        )
        return JsonResponse(
            {
                "message": _("Add successfully"),
            },
            safe=False,
            status=200,
        )

    context = {
        "user_in_project": user_in_project_ex,
        "project_id": project_id,
        "stage_id": pk,
    }

    return render(request, "app/add_member_to_stage.html", context)


@login_required
def delete_member_from_project(request, project_pk, user_pk):
    user = get_object_or_404(User, pk=user_pk)
    project = get_object_or_404(Project, pk=project_pk)
    user_project = get_object_or_404(UserProject, user=user, project=project)

    if is_pm(user=request.user, project=project) and (
        not is_pm(user=user, project=project)
    ):
        stages = Stage.objects.filter(project=project)
        user_stage = UserStage.objects.filter(stage__in=stages, user=user)
        user_stage.delete()
        user_project.delete()
        return HttpResponse(_("Delete successfully"))
    else:
        raise PermissionDenied()
