from django.contrib.auth.models import User
from django.test import TestCase

from areas.models import AreaBio


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
        self.assertNotContains(response, 'href="/admin/"')

    def test_home_page_shows_admin_link_to_staff_users(self):
        user = User.objects.create_user(
            username='staff',
            password='password',
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get('/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/admin/"')


class AdminThemeTests(TestCase):
    def test_admin_uses_custom_theme(self):
        user = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@example.com',
        )
        self.client.force_login(user)

        response = self.client.get('/admin/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wohnbiografien Admin')
        self.assertContains(response, '<div id="site-name"><a href="/">Wohnbiografien Admin</a></div>')
        self.assertContains(response, 'css/admin.css')

    def test_admin_area_bio_form_hides_removed_fields(self):
        user = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@example.com',
        )
        bio = AreaBio.objects.create(
            user=user,
            name='Jessica',
            age=33,
            country='Berlin',
        )
        self.client.force_login(user)

        response = self.client.get(f'/admin/areas/areabio/{bio.pk}/change/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Veröffentlicht')
        self.assertNotContains(response, 'Per E-Mail versendet an')

    def test_admin_view_on_site_links_to_frontend_page(self):
        user = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@example.com',
        )
        bio = AreaBio.objects.create(
            user=user,
            name='Jessica',
            age=33,
            country='Berlin',
        )
        self.client.force_login(user)

        response = self.client.get(f'/admin/areas/areabio/{bio.pk}/change/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="/graph/{bio.uuid}/view/"')

    def test_area_bio_frontend_page_renders(self):
        user = User.objects.create_user(username='user', password='password')
        bio = AreaBio.objects.create(
            user=user,
            name='Jessica',
            age=33,
            country='Berlin',
        )

        response = self.client.get(f'/graph/{bio.uuid}/view/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jessica, 33, Berlin')
        self.assertContains(response, 'Zur Startseite')
        self.assertContains(response, 'class="app bio-index site-graph-page"')
        self.assertContains(response, 'href="/" class="admin-link"')
        self.assertNotContains(response, 'Bearbeiten')
