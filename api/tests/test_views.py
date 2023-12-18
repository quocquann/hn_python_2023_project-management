from django.urls import reverse
from rest_framework import status

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
