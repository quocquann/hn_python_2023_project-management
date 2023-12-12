import datetime

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from app.models import Stage, UserProject, UserStage, Project
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


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name", "describe", "end_date"]

    def validate_end_date(self, value):
        if value < datetime.date.today():
            raise serializers.ValidationError(_("Invalid date - end date in past"))
        return value


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
