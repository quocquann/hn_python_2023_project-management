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

    @staticmethod
    def setup_user():
        User = get_user_model()

        return User.objects.create_user(
            username="user1", password="user1", email="user1@mail.com"
        )
