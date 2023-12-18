from django.contrib.auth import get_user_model
from django.urls import path, include
from rest_framework.test import APITestCase, URLPatternsTestCase


class TestSetUp(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path("api/", include("api.urls")),
    ]

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.setup_user()
        cls.signup_data = {
            "username": "user2",
            "email": "user2@gmail.com",
            "password1": "user2abcqwe",
            "password2": "user2abcqwe",
            "first_name": "2",
            "last_name": "user",
        }

    @staticmethod
    def setup_user():
        User = get_user_model()

        return User.objects.create_user(
            username="user1", password="user1", email="user1@gmail.com"
        )
