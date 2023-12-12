import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.utils import constants


class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verify_token = models.CharField(_("Verify token"), max_length=255, null=True)


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
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)
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

    class Meta:
        unique_together = (("user", "project"),)


class Stage(models.Model):
    name = models.CharField(_("Name"), max_length=50)
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    user = models.ManyToManyField(User, verbose_name=_("User"), through="UserStage")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    status = models.IntegerField(
        _("Status"),
        choices=constants.STAGE_STATUS_CHOICES,
        default=constants.STAGE_STATUS_DEFAULT,
    )
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.status = constants.CLOSED
        self.deleted_at = datetime.datetime.now()
        self.save()


class UserStage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    role = models.IntegerField(
        _("Role"),
        choices=constants.ROLE_USERSTAGE_CHOICES,
        default=constants.ROLE_USERSTAGE_DEFAULT,
    )

    class _Meta:
        unique_together = ["user", "stage"]


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
    user = models.ForeignKey(User,on_delete=models.SET_NULL, null=True )




class Report(models.Model):
    content = models.CharField(_("Content"), max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, verbose_name=_("Project"), on_delete=models.CASCADE
    )
