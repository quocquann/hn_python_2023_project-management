from django.contrib.auth.models import User
from django.db import transaction
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import filters
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Project, UserProject, Stage, Task, UserStage
from app.utils import constants
from app.utils.helpers import (
    send_mail_verification,
    is_in_project,
    is_pm,
)
from .permissions import IsPM, IsPMOrProjectMember, IsPMOrStageOwner
from .serializers import (
    SignUpSerializers,
    VerifySerializers,
    ProjectSerializer,
    StageSerializers,
    StageListSerializers,
    ListUserSerializer,
    MemberProjectSerializer,
    AddMemberStageSerializers,
    UserStageSerializers,
    TaskSerializer,
)


class SignUp(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SignUpSerializers,
        responses={
            201: {"description": "Please check your email to verify your account."},
        },
    )
    def post(self, request):
        serializer = SignUpSerializers(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                new_user = serializer.instance
                send_mail_verification(request, new_user=new_user)
                data = {
                    "message": _("Please check your email to verify your account."),
                    "user": serializer.data,
                }

                return Response(data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Verify(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        user_dict = model_to_dict(
            user, ["pk", "username", "email", "first_name", "last_name"]
        )
        data = {
            "pk": uid,
            "verify_token": token,
        }
        serializer = VerifySerializers(user, data=data)
        if serializer.is_valid():
            serializer.save()
            data = {
                "message": _(
                    "Thank you for your email confirmation. Now you can login your account."
                ),
                "user": user_dict,
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=ProjectSerializer,
    responses=ProjectSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_project(request):
    serializer = ProjectSerializer(data=request.data)
    if serializer.is_valid():
        project = serializer.save()
        UserProject.objects.create(
            user=request.user, project=project, role=constants.PROJECT_MANAGER
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=ProjectSerializer,
    responses=ProjectSerializer,
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsPM])
def update_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    serializer = ProjectSerializer(project, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskList(APIView):
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticated,)

    def get_object_tasks_by_stage(self, stage_id):
        tasks = Task.objects.filter(stage_id=stage_id)
        return tasks

    def get(self, request, project_id, stage_id):
        project = Project.objects.get(id=project_id)
        tasks = self.get_object_tasks_by_stage(stage_id=stage_id)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(tasks, request)

        if is_in_project(user=request.user, project=project):
            data = TaskSerializer(result_page, many=True).data
            return paginator.get_paginated_response(data)

        return Response(status=status.HTTP_403_FORBIDDEN)


class StageList(APIView, LimitOffsetPagination):
    permission_classes = [IsAuthenticated, IsPMOrProjectMember]

    def get_serializer_class(self):
        return StageSerializers

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="name",
                description="Search stage by name",
                required=False,
                type=str,
            ),
        ],
        responses={
            200: StageListSerializers,
        },
    )
    def get(self, request, project_id):
        name = self.request.query_params.get("name", "")
        stages = Stage.objects.filter(project_id=project_id, name__icontains=name)
        result_page = self.paginate_queryset(stages, request, view=self)
        data = StageListSerializers(result_page, many=True).data

        return self.get_paginated_response(data)

    def post(self, request, project_id):
        serializer = StageSerializers(
            data=request.data, context={"project_id": project_id}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsPM])
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if Stage.objects.filter(project=project, status=constants.ACTIVE):
        return Response(
            {"detail": "Can not delete project - Project already has stage"},
            status.HTTP_400_BAD_REQUEST,
        )
    project.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class StageDetail(APIView):
    permission_classes = [IsAuthenticated, IsPMOrProjectMember]

    @extend_schema(
        request=StageListSerializers,
        responses={
            200: StageListSerializers,
        },
    )
    def get(self, request, project_id, stage_id):
        stage = get_object_or_404(Stage, pk=stage_id, project_id=project_id)
        user_stage = UserStage.objects.filter(stage=stage).select_related("user")
        stage.members = user_stage
        serializer = StageListSerializers(stage)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=StageSerializers,
        responses={
            201: StageSerializers,
        },
    )
    def put(self, request, project_id, stage_id):
        stage = get_object_or_404(Stage, pk=stage_id)
        serializer = StageSerializers(
            stage, data=request.data, context={"project_id": project_id}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, project_id, stage_id):
        stage = get_object_or_404(Stage, pk=stage_id)
        tasks = Task.objects.filter(
            stage=stage, status__in=[constants.TASK_NEW, constants.TASK_IN_PROGRESS]
        )
        if tasks:
            return Response(
                {
                    "detail": "Can not delete stage - Stage already has task in progress or new"
                },
                status.HTTP_400_BAD_REQUEST,
            )

        stage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectList(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    @extend_schema(
        parameters=[OpenApiParameter(name="search", required=False, type=str)]
    )
    def get(self, request):
        return super().get(self, request)

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)


class ProjectDetail(APIView):
    permission_classes = [IsAuthenticated, IsPMOrProjectMember]

    @extend_schema(responses=ProjectSerializer)
    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        stages = Stage.objects.filter(project=project)
        users = UserProject.objects.filter(project=project)
        project.stages = stages
        project.members = users
        serializer = ProjectSerializer(project, many=False)
        return Response(serializer.data, status.HTTP_200_OK)


class MemberListOfProject(APIView):
    permission_classes = [IsAuthenticated, IsPM]

    @extend_schema(request=ListUserSerializer, responses=MemberProjectSerializer)
    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        serializer = ListUserSerializer(data=request.data, context={"project": project})
        if serializer.is_valid():
            members = User.objects.filter(pk__in=serializer.data.get("user_ids"))
            user_projects = [
                UserProject(user=user, project=project, role=constants.MEMBER)
                for user in members
            ]
            user_project_created = UserProject.objects.bulk_create(user_projects)
            serializer = MemberProjectSerializer(user_project_created, many=True)
            return Response(serializer.data, status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class MemberStageList(APIView):
    permission_classes = [IsAuthenticated, IsPMOrStageOwner]

    @extend_schema(
        request=AddMemberStageSerializers,
        responses={
            201: AddMemberStageSerializers,
        },
    )
    def post(self, request, project_id, stage_id):
        serializer = AddMemberStageSerializers(
            data=request.data, context={"project_id": project_id}
        )
        if serializer.is_valid():
            user_id = serializer.validated_data["user"]

            stage = get_object_or_404(Stage, pk=stage_id)
            stage.user.add(*user_id, through_defaults={"role": constants.MEMBER})

            user_stage = UserStage.objects.filter(
                stage_id=stage_id, user_id__in=user_id
            ).select_related("user")
            data = UserStageSerializers(user_stage, many=True).data

            return Response(data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemberStageDetail(APIView):
    perrmision_class = [IsAuthenticated, IsPMOrStageOwner]

    def delete(self, request, project_id, stage_id, user_id):
        stage_member = UserStage.objects.filter(stage_id=stage_id, user_id=user_id)

        if not stage_member.exists():
            return Response(
                {"message": "User is not member of stage"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stage_owner = UserStage.objects.filter(
            stage_id=stage_id, role=constants.STAGE_OWNER
        )

        if (
            stage_owner[0].user_id == request.user.id
            and stage_owner[0].user_id == user_id
        ):
            return Response(
                {"message": "You are stage owner, can not delete yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Task.objects.filter(
            stage=stage_id,
            user=user_id,
            status__in=[constants.TASK_NEW, constants.TASK_IN_PROGRESS],
        ).exists():
            return Response(
                {"message": "User is working on task"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        stage_member.delete()


class MemberDetailOfProject(APIView):
    permission_classes = [IsAuthenticated, IsPM]

    def delete(self, request, project_id, user_id):
        project = get_object_or_404(Project, pk=project_id)
        user = get_object_or_404(User, pk=user_id)
        if not UserProject.objects.filter(user=user, project=project):
            data = {"message": "User is not in project"}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        if Task.objects.filter(
            user=user, status__in=[constants.TASK_NEW, constants.TASK_IN_PROGRESS]
        ):
            data = {
                "message": "Cannot delete user - User have already assigned to some task"
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        if is_pm(user=user, project=project):
            data = {"message": "Cannot delete PM"}
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        stages = Stage.objects.filter(project=project)
        user_stages = UserStage.objects.filter(
            user=user, stage__in=stages, role=constants.STAGE_OWNER
        ).values("stage")

        if user_stages:
            data = {
                "message": "Cannot delete user - User have already been stage owner of some stage",
                "stages": user_stages,
            }
            return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        UserStage.objects.filter(user=user, stage__in=stages).delete()
        UserProject.objects.filter(user=user, project=project).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
