from django.contrib.auth.models import User
from django.test import TestCase


class HomePageLoginAccessTests(TestCase):
    def test_home_page_redirects_anonymous_users_to_login(self):
        response = self.client.get('/', HTTP_HOST='localhost')

        self.assertRedirects(
            response,
            '/login/?next=/',
            fetch_redirect_response=False,
        )

    def test_login_page_renders(self):
        response = self.client.get('/login/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anmelden')

    def test_home_page_allows_authenticated_users(self):
        user = User.objects.create_user(username='user', password='password')
        self.client.force_login(user)

        response = self.client.get('/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
