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
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.models import Project, UserProject, Stage, Task
from app.utils import constants
from app.utils.helpers import send_mail_verification
from .permissions import IsPM
from .serializers import (
    SignUpSerializers,
    VerifySerializers,
    ProjectSerializer,
    StageSerializers,
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


class StageList(APIView):
    permission_classes = [IsAuthenticated, IsPM]

    @extend_schema(
        request=StageSerializers,
        responses={
            201: StageSerializers,
        },
    )
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
    permission_classes([IsAuthenticated, IsPM])

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
