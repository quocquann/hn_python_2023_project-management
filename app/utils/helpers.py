from uuid import uuid4

from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from projectmanagement.settings import EMAIL_HOST_USER
from . import constants
from ..models import UserProject, UserStage, CustomUser


def is_in_group(user):
    return user.groups.filter(name__in=["Stage_Owner", "PM"]).exists()


def check_token(user, token):
    return user.customuser.verify_token == token


def is_in_project(user, project):
    return UserProject.objects.filter(user=user, project=project).exists()


def is_pm(user, project):
    user_project = UserProject.objects.filter(user=user, project=project)
    if user_project.exists():
        return user_project[0].role == constants.PROJECT_MANAGER
    return False


def is_stage_owner(user, stage):
    user_stage = UserStage.objects.filter(user=user, stage=stage)
    return user_stage[0].role == constants.STAGE_OWNER


def is_stage_member_or_pm(user, stage):
    return UserStage.objects.filter(user=user, stage=stage).exists() or is_pm(
        user, stage.project
    )


def is_pm_or_stage_owner(user, stage, project):
    return is_pm(user, project) or is_stage_owner(user, stage)


def send_mail_verification(request, new_user):
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
