import datetime

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.validators import UniqueValidator

from app.models import Stage, UserProject, UserStage, Project, Task
from app.utils import constants
from app.utils.helpers import check_token


class SignUpSerializers(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=30,
        label=_("Username"),
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    email = serializers.EmailField(
        max_length=100,
        label=_("Email"),
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password1 = serializers.CharField(
        max_length=255,
        label=_("Password"),
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        max_length=255,
        label=_("Confirm Password"),
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
        ]

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError(_("Password does not match"))

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password1"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            is_active=False,
        )

        return user


class VerifySerializers(serializers.ModelSerializer):
    pk = serializers.IntegerField(label=_("User ID"))
    verify_token = serializers.CharField(max_length=255, label=_("Verify token"))

    class Meta:
        model = User
        fields = ["pk", "verify_token"]

    def validate(self, data):
        user = User.objects.get(pk=data["pk"])
        if not check_token(user, data["verify_token"]):
            raise serializers.ValidationError(_("Activation link is invalid!"))
        return data

    def update(self, instance, validated_data):
        instance.is_active = True
        instance.save()
        return instance


class StageSerializers(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(many=False, queryset=User.objects.all())

    class Meta:
        model = Stage
        fields = ["name", "start_date", "end_date", "user"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["user"] = UserStage.objects.values("user_id").get(
            stage=instance, role=constants.STAGE_OWNER
        )
        return representation

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError(_("Start date must be before end date"))

        project_id = self.context.get("project_id")
        user_projects = UserProject.objects.filter(
            project_id=project_id, user=data["user"]
        )

        if not user_projects.exists():
            raise serializers.ValidationError(_("User is not in project"))

        return data

    def create(self, validated_data):
        project_id = self.context.get("project_id")
        user = validated_data.pop("user")
        stage = Stage.objects.create(project_id=project_id, **validated_data)
        UserStage.objects.create(user=user, stage=stage, role=constants.STAGE_OWNER)
        UserProject.objects.filter(user=user, project_id=project_id).update(
            role=constants.STAGE_OWNER
        )
        return stage

    def update(self, instance, validated_data):
        project_id = self.context.get("project_id")
        user = validated_data.pop("user")

        instance.name = validated_data.get("name", instance.name)
        instance.start_date = validated_data.get("start_date", instance.start_date)
        instance.end_date = validated_data.get("end_date", instance.end_date)
        instance.save()

        if user:
            UserProject.objects.filter(
                project_id=project_id, role=constants.STAGE_OWNER
            ).update(role=constants.MEMBER)

            UserStage.objects.filter(stage=instance, role=constants.STAGE_OWNER).update(
                role=constants.MEMBER
            )

            try:
                stage_owner = UserStage.objects.get(user=user, stage=instance)
                stage_owner.role = constants.STAGE_OWNER
                stage_owner.save()
            except ObjectDoesNotExist:
                UserStage.objects.create(
                    user=user, stage=instance, role=constants.STAGE_OWNER
                )

        return instance


class TaskSerializers(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["content", "start_date", "end_date", "status"]


class UserStageSerializers(serializers.ModelSerializer):
    pk = serializers.IntegerField(source="user.pk")
    username = serializers.CharField(source="user.username")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = UserStage
        fields = ["pk", "username", "first_name", "last_name", "role"]


class StageListSerializers(serializers.ModelSerializer):
    task_set = TaskSerializers(many=True, read_only=True)
    members = UserStageSerializers(many=True, read_only=True)
    task_count = serializers.SerializerMethodField("get_task_count")

    class Meta:
        model = Stage
        fields = [
            "name",
            "start_date",
            "end_date",
            "status",
            "task_count",
            "task_set",
            "members",
        ]

    def get_task_count(self, instance):
        return Task.objects.filter(stage=instance).count()


class MemberProjectSerializer(serializers.ModelSerializer):
    pk = serializers.SerializerMethodField("get_pk")
    first_name = serializers.SerializerMethodField("get_first_name")
    last_name = serializers.SerializerMethodField("get_last_name")
    email = serializers.SerializerMethodField("get_email")

    class Meta:
        model = UserProject
        fields = ["pk", "first_name", "last_name", "email", "role"]

    def get_pk(self, instance):
        return User.objects.get(pk=instance.user.pk).pk

    def get_first_name(self, instance):
        return User.objects.get(pk=instance.user.pk).first_name

    def get_last_name(self, instance):
        return User.objects.get(pk=instance.user.pk).last_name

    def get_email(self, instance):
        return User.objects.get(pk=instance.user.pk).email


class ProjectSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField("get_task_count")
    stage_count = serializers.SerializerMethodField("get_stage_count")
    stages = StageListSerializers(many=True, read_only=True)
    members = MemberProjectSerializer(many=True, read_only=True)
    pm = serializers.SerializerMethodField("get_pm")

    class Meta:
        model = Project
        fields = [
            "name",
            "describe",
            "end_date",
            "start_date",
            "status",
            "pm",
            "task_count",
            "stage_count",
            "stages",
            "members",
        ]

    def get_pm(self, instance):
        user_project = UserProject.objects.get(
            project=instance, role=constants.PROJECT_MANAGER
        )
        return User.objects.get(pk=user_project.user.pk).username

    def get_stage_count(self, instance):
        return Stage.objects.filter(project=instance.pk).count()

    def get_task_count(self, instance):
        stages = Stage.objects.filter(project=instance.pk)
        return Task.objects.filter(stage__in=stages).count()

    def validate_end_date(self, value):
        if value < datetime.date.today():
            raise serializers.ValidationError(_("Invalid date - end date in past"))
        return value


class ListUserSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField())

    def validate_user_ids(self, value):
        user_not_found = []
        user_existed = []
        for user_id in value:
            try:
                user = User.objects.get(pk=user_id)
                if UserProject.objects.filter(
                    user=user, project=self.context.get("project")
                ):
                    user_existed.append(user_id)
            except ObjectDoesNotExist:
                user_not_found.append(user_id)

        if user_not_found or user_existed:
            detail = {
                "user_ids_not_found": user_not_found,
                "user_ids_existed": user_existed,
                "message": "Users not found or already in project",
            }
            raise serializers.ValidationError(
                detail=detail, code=status.HTTP_404_NOT_FOUND
            )
        return value
