from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from app.models import Project, UserProject, Stage
from app.utils import constants
from api.serializers import ProjectSerializer

from api.tests.test_setup import TestSetUp


class LoginTest(TestSetUp):
    def test_login(self):
        data = {"username": "user1", "password": "user1"}
        response = self.client.post(
            path=reverse("token_obtain_pair"), data=data, format="json"
        )

        self.assertEqual(response.status_code, 200)


class SignUpTest(TestSetUp):
    def test_signup(self):
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        res_data = response.data.get("user")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data.get("message"),
            "Please check your email to verify your account.",
        )
        self.assertEqual(res_data["username"], self.signup_data["username"])
        self.assertEqual(res_data["email"], self.signup_data["email"])
        self.assertEqual(res_data["first_name"], self.signup_data["first_name"])
        self.assertEqual(res_data["last_name"], self.signup_data["last_name"])

    def test_username_blank(self):
        self.signup_data["username"] = ""
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["username"][0], "This field may not be blank.")

    def test_username_exists(self):
        self.signup_data["username"] = "user1"
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["username"][0], "This field must be unique.")

    def test_email_blank(self):
        self.signup_data["email"] = ""
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "This field may not be blank.")

    def test_email_exists(self):
        self.signup_data["email"] = "user1@gmail.com"
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "This field must be unique.")

    def test_email_invalid(self):
        self.signup_data["email"] = "user2"
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["email"][0], "Enter a valid email address.")

    def test_password1_blank(self):
        self.signup_data["password1"] = ""
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["password1"][0], "This field may not be blank.")

    def test_password1(self):
        self.signup_data["password1"] = "aaa"
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["password1"],
            [
                "This password is too short. It must contain at least 8 characters.",
                "This password is too common.",
            ],
        )

    def test_password1_common(self):
        self.signup_data["password1"] = "aaaaaaaa"
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["password1"][0], "This password is too common.")

    def test_password2_blank(self):
        self.signup_data["password2"] = ""
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["password2"][0], "This field may not be blank.")

    def test_password_not_match(self):
        self.signup_data["password2"] = "aaa"
        response = self.client.post(
            path=reverse("signup"), data=self.signup_data, format="json"
        )
        self.assertEqual(
            response.data["non_field_errors"][0], "Password does not match"
        )


class APIViewListDetailProjectTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        project = Project.objects.create(
            name="Project 1",
            describe="Describe",
            start_date="2021-01-01",
            end_date="2021-01-02",
            status=0,
        )

        user = User.objects.create_user(
            username="user",
            password="123456",
            first_name="Quan",
            last_name="Nguyen",
            email="quan.ng.quoc@gmail.com",
        )

        project.user.add(user, through_defaults={"role": constants.PROJECT_MANAGER})

    def setUp(self):
        data = {"username": "user", "password": "123456"}
        res = self.client.post(
            path=reverse("token_obtain_pair"),
            data=data,
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + res.data["access"])

    def test_get_project_by_user_view_result(self):
        response = self.client.get(reverse("project_list"))
        user = User.objects.get(username="user")
        projects = Project.objects.filter(user=user)
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(response.data["results"], serializer.data)

    def test_get_project_by_user_view_status_code(self):
        response = self.client.get(reverse("project_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_detail_status_code(self):
        response = self.client.get(reverse("project_detail", kwargs={"project_id": 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_detail_result(self):
        response = self.client.get(reverse("project_detail", kwargs={"project_id": 1}))
        project = Project.objects.get(pk=1)
        stages = Stage.objects.filter(project=project)
        users = UserProject.objects.filter(project=project)
        project.stages = stages
        project.members = users
        serializer = ProjectSerializer(project, many=False)
        self.assertEqual(response.data, serializer.data)
