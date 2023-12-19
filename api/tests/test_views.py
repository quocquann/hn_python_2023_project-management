from django.urls import reverse

from api.tests.test_setup import TestSetUp


class LoginTest(TestSetUp):
    def test_login(self):
        data = {"username": "user1", "password": "user1"}
        response = self.client.post(
            path=reverse("token_obtain_pair"), data=data, format="json"
        )

        self.assertEqual(response.status_code, 200)
