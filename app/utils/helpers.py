from . import constants
from ..models import UserProject, UserStage


def is_in_group(user):
    return user.groups.filter(name__in=["Stage_Owner", "PM"]).exists()


def check_token(user, token):
    return user.customuser.verify_token == token


def is_in_project(user, project):
    return UserProject.objects.filter(user=user, project=project).exists()


def is_pm(user, project):
    user_project = UserProject.objects.filter(user=user, project=project)
    return user_project[0].role == constants.PROJECT_MANAGER


def is_stage_owner(user, stage):
    user_stage = UserStage.objects.filter(user=user, stage=stage)
    return user_stage[0].role == constants.STAGE_OWNER


def is_stage_member_or_pm(user, stage):
    return UserStage.objects.filter(user=user, stage=stage).exists() or is_pm(
        user, stage.project
    )


def is_pm_or_stage_owner(user, stage, project):
    return is_pm(user, project) or is_stage_owner(user, stage)
