from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse_lazy

from app.utils import constants
import datetime


class Project(models.Model):
    name = models.CharField(_("Project name"), max_length=50)
    describe = models.CharField(_("Describe"), max_length=500)
    start_date = models.DateField(_("Start date"), auto_now_add=True)
    end_date = models.DateField(_("End date"))
    status = models.IntegerField(
        _("Status"),
        choices=constants.PROJECT_STATUS_CHOICES,
        default=constants.PROJECT_STATUS_DEFAULT,
    )
    deleted_at = models.DateTimeField(_("Deleted at"), null=True)
    user = models.ManyToManyField(User, verbose_name=_("User"), through="UserProject")

    def __str__(self):
        return self.name

    def delete(self):
        self.status = constants.CLOSED
        self.deleted_at = datetime.datetime.now()
        self.save()


class UserProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.IntegerField(
        _("Role"),
        choices=constants.ROLE_USERPROJECT_CHOICES,
        default=constants.ROLE_USERPROJECT_DEFAULT,
    )


class Stage(models.Model):
    name = models.CharField(_("Name"), max_length=50)
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    user = models.ManyToManyField(User, verbose_name=_("User"), through="UserStage")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)


class UserStage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    role = models.IntegerField(
        _("Role"),
        choices=constants.ROLE_USERSTAGE_CHOICES,
        default=constants.ROLE_USERSTAGE_DEFAULT,
    )


class Task(models.Model):
    content = models.CharField(_("Content"), max_length=200)
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    status = models.IntegerField(
        _("Status"),
        choices=constants.TASK_STATUS_CHOICES,
        default=constants.TASK_STATUS_DEFAULT,
    )
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    user = models.ManyToManyField(User, verbose_name=_("User"), through="UserTask")


class UserTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)


class Report(models.Model):
    content = models.CharField(_("Content"), max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, verbose_name=_("Project"), on_delete=models.CASCADE
    )
