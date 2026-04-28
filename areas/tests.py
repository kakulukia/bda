from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from areas.models import AreaBio, BioEntry, calculate_age, calculate_birth_year
from areas.svg import FUTURE_FILL, FUTURE_TOTAL_FILL, PERSON_FILL, TOTAL_FILL, _build_segments, render_area_bio_svg


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

    def test_admin_area_bio_form_uses_german_source_labels_without_locales(self):
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
        BioEntry.objects.create(
            area_bio=bio,
            year_from=bio.birth_year,
            year_to=bio.birth_year + 1,
            living_space=80,
            number_of_people=2,
            description='Umzug',
        )
        self.client.force_login(user)

        response = self.client.get(f'/admin/areas/areabio/{bio.pk}/change/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Geburtsjahr')
        self.assertContains(response, 'Stadt')
        self.assertContains(response, 'Wohnfläche')
        self.assertContains(response, 'Personen im Haushalt')
        self.assertContains(response, 'Grund für den Wechsel')
        self.assertContains(response, 'Eigentümerkategorie')
        self.assertNotContains(response, 'Living space')
        self.assertNotContains(response, 'Number of people')
        self.assertNotContains(response, 'Country')

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
        self.assertContains(response, f'href="/graph/{bio.uuid}/export.svg"')
        self.assertContains(response, 'SVG Export')

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
        self.assertContains(response, 'SVG Export')
        self.assertContains(response, f'href="/graph/{bio.uuid}/export.svg"')
        self.assertContains(response, 'class="app bio-index site-graph-page"')
        self.assertContains(response, 'href="/" class="admin-link"')
        self.assertNotContains(response, 'Bearbeiten')

    def test_graph_template_uses_valid_css_decimal_points(self):
        bio = AreaBio.objects.create(
            name='Jessica',
            age=33,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            year_from=bio.birth_year,
            year_to=bio.birth_year + 1,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )

        response = self.client.get(f'/graph/{bio.uuid}/view/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'height: 1.25%;')
        self.assertNotContains(response, 'height: 1,25%;')

    def test_svg_export_view_renders_inline_svg(self):
        user = User.objects.create_user(username='user', password='password')
        bio = AreaBio.objects.create(
            user=user,
            name='Jessica',
            age=33,
            country='Berlin',
        )

        response = self.client.get(f'/graph/{bio.uuid}/export.svg', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml; charset=utf-8')
        self.assertIn('inline; filename="wohnbiografie-jessica-33-berlin-', response['Content-Disposition'])
        self.assertContains(response, '<svg', status_code=200)


class FrontendEditingDisabledTests(TestCase):
    def test_area_bio_list_api_remains_available_for_frontend_filters(self):
        bio = AreaBio.objects.create(
            name='Jessica',
            age=33,
            country='Berlin',
        )

        response = self.client.get('/api/area-bios/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(bio.uuid), status_code=200)

    def test_removed_frontend_editing_routes_are_not_available(self):
        bio = AreaBio.objects.create(
            name='Jessica',
            age=33,
            country='Berlin',
        )

        paths = [
            '/graph/add/',
            '/graph/done/',
            f'/graph/edit/{bio.uuid}/',
        ]

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path, HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 404)

    def test_removed_frontend_editing_api_is_not_available(self):
        bio = AreaBio.objects.create(
            name='Jessica',
            age=33,
            country='Berlin',
        )

        post_response = self.client.post(
            '/api/area-bios/',
            {'name': 'New', 'age': 20, 'country': 'Berlin'},
            HTTP_HOST='localhost',
        )
        put_response = self.client.put(
            f'/api/area-bios/{bio.pk}/',
            {'name': 'Updated', 'age': 33, 'country': 'Berlin'},
            content_type='application/json',
            HTTP_HOST='localhost',
        )
        entries_response = self.client.get(
            f'/api/area-bios/{bio.pk}/entries/',
            HTTP_HOST='localhost',
        )
        compare_response = self.client.get(
            f'/api/area-bios/{bio.pk}/compare/',
            HTTP_HOST='localhost',
        )

        self.assertEqual(post_response.status_code, 405)
        self.assertEqual(put_response.status_code, 405)
        self.assertEqual(entries_response.status_code, 404)
        self.assertEqual(compare_response.status_code, 404)


class AreaBioBirthYearTests(TestCase):
    def test_birth_year_is_calculated_when_age_is_saved(self):
        with patch('areas.models.timezone.localdate', return_value=date(2026, 4, 27)):
            bio = AreaBio.objects.create(
                name='Andy',
                age=45,
                country='Berlin',
            )

        self.assertEqual(bio.birth_year, 1981)

        with patch('areas.models.timezone.localdate', return_value=date(2030, 4, 27)):
            bio.name = 'Andreas'
            bio.save()

        bio.refresh_from_db()
        self.assertEqual(bio.birth_year, 1981)

        with patch('areas.models.timezone.localdate', return_value=date(2030, 4, 27)):
            bio.age = 50
            bio.save()

        bio.refresh_from_db()
        self.assertEqual(bio.birth_year, 1981)

        with patch('areas.models.timezone.localdate', return_value=date(2030, 4, 27)):
            bio.age = 52
            bio.save()

        bio.refresh_from_db()
        self.assertEqual(bio.birth_year, 1978)

    def test_age_is_calculated_when_only_birth_year_is_saved(self):
        with patch('areas.models.timezone.localdate', return_value=date(2026, 4, 27)):
            bio = AreaBio.objects.create(
                name='Andy',
                birth_year=1981,
                country='Berlin',
            )

        self.assertEqual(bio.age, 45)
        self.assertEqual(bio.birth_year, 1981)

    def test_age_is_optional_for_admin_birth_year_entry(self):
        self.assertTrue(AreaBio._meta.get_field('age').blank)

    def test_one_year_difference_between_age_and_birth_year_is_kept(self):
        with patch('areas.models.timezone.localdate', return_value=date(2026, 4, 27)):
            bio = AreaBio.objects.create(
                name='Andy',
                age=45,
                birth_year=1980,
                country='Berlin',
            )

        self.assertEqual(bio.age, 45)
        self.assertEqual(bio.birth_year, 1980)

    def test_birth_year_is_recalculated_when_difference_is_too_large_and_age_changed(self):
        with patch('areas.models.timezone.localdate', return_value=date(2026, 4, 27)):
            bio = AreaBio.objects.create(
                name='Andy',
                age=45,
                birth_year=1975,
                country='Berlin',
            )

        self.assertEqual(bio.age, 45)
        self.assertEqual(bio.birth_year, 1981)

    def test_age_is_recalculated_when_difference_is_too_large_and_birth_year_changed(self):
        with patch('areas.models.timezone.localdate', return_value=date(2026, 4, 27)):
            bio = AreaBio.objects.create(
                name='Andy',
                age=45,
                birth_year=1981,
                country='Berlin',
            )

            bio.birth_year = 1970
            bio.save()

        bio.refresh_from_db()
        self.assertEqual(bio.age, 56)
        self.assertEqual(bio.birth_year, 1970)

    def test_age_and_birth_year_helpers_use_current_year(self):
        with patch('areas.models.timezone.localdate', return_value=date(2026, 4, 27)):
            self.assertEqual(calculate_birth_year(45), 1981)
            self.assertEqual(calculate_age(1981), 45)

    def test_normalized_entries_extend_zero_year_changes_to_next_entry(self):
        bio = AreaBio.objects.create(
            name='Andy',
            age=15,
            country='Berlin',
        )
        birth_year = bio.birth_year
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year,
            year_to=birth_year + 1,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year + 1,
            year_to=birth_year + 2,
            living_space=124,
            number_of_people=3,
            description='Umzug',
        )
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year + 2,
            year_to=birth_year + 2,
            living_space=124,
            number_of_people=4,
            description='Schwester',
        )
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year + 3,
            year_to=birth_year + 7,
            living_space=123,
            number_of_people=4,
            description='Haus',
        )

        entries = list(bio.normalized_entries())

        self.assertEqual((entries[2].year_from, entries[2].year_to), (birth_year + 2, birth_year + 3))
        self.assertNotIn(
            (birth_year + 2, birth_year + 3, 0),
            [(entry.year_from, entry.year_to, entry.living_space) for entry in entries],
        )


class AreaBioSvgTests(TestCase):
    def test_svg_renderer_uses_scaled_geometry_and_labels(self):
        bio = AreaBio.objects.create(
            name='Julia',
            age=12,
            country='Berlin',
        )
        birth_year = bio.birth_year
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year + 10,
            year_to=birth_year + 15,
            living_space=100,
            number_of_people=4,
            description='Testphase',
        )

        svg = render_area_bio_svg(bio)

        self.assertIn('<svg', svg)
        self.assertIn('@font-face', svg)
        self.assertIn('100 Jahre', svg)
        self.assertIn('100 m²', svg)
        self.assertIn('25 m²', svg)
        self.assertIn(f'fill="{TOTAL_FILL}" data-kind="total" data-age-from="0.00" data-age-to="12.00"', svg)
        self.assertIn(f'fill="{PERSON_FILL}" data-kind="personal" data-age-from="0.00" data-age-to="12.00"', svg)
        self.assertIn(f'fill="{FUTURE_TOTAL_FILL}" data-kind="total" data-age-from="12.00" data-age-to="15.00"', svg)
        self.assertIn(f'fill="{FUTURE_FILL}" data-kind="personal" data-age-from="12.00" data-age-to="15.00"', svg)
        self.assertIn('data-kind="description" data-age="0.00"', svg)
        self.assertNotIn('data-kind="description" data-age="12.00"', svg)
        self.assertIn('width="100.00" height="60.00"', svg)
        self.assertIn('width="25.00" height="60.00"', svg)
        self.assertIn('data-kind="x-axis-total" x1="55.00" y1="525.00" x2="155.00" y2="525.00"', svg)

    def test_svg_renderer_extends_zero_year_changes_to_next_entry(self):
        bio = AreaBio.objects.create(
            name='Andy',
            age=15,
            country='Berlin',
        )
        birth_year = bio.birth_year
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year + 9,
            year_to=birth_year + 10,
            living_space=124,
            number_of_people=3,
            description='Umzug',
        )
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year + 10,
            year_to=birth_year + 10,
            living_space=124,
            number_of_people=4,
            description='Schwester',
        )
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year + 11,
            year_to=birth_year + 15,
            living_space=123,
            number_of_people=4,
            description='Haus',
        )

        svg = render_area_bio_svg(bio)

        self.assertIn('data-kind="total" data-age-from="10.00" data-age-to="11.00"', svg)
        self.assertIn('data-kind="personal" data-age-from="10.00" data-age-to="11.00"', svg)
        self.assertIn('data-kind="description" data-age="10.00"', svg)
        self.assertIn('shape-rendering="crispEdges"', svg)
        segments = _build_segments(bio)
        self.assertEqual(segments[0]['age_from'], 0)
        for previous_segment, next_segment in zip(segments, segments[1:]):
            self.assertEqual(previous_segment['age_to'], next_segment['age_from'])

    def test_svg_renderer_extends_first_entry_to_birth(self):
        bio = AreaBio.objects.create(
            name='Andy',
            age=45,
            country='Berlin',
        )
        birth_year = bio.birth_year
        BioEntry.objects.create(
            area_bio=bio,
            year_from=birth_year + 8,
            year_to=birth_year + 9,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )

        svg = render_area_bio_svg(bio)

        self.assertIn('data-kind="total" data-age-from="0.00" data-age-to="9.00"', svg)
        self.assertIn('data-kind="personal" data-age-from="0.00" data-age-to="9.00"', svg)
        self.assertIn('data-kind="description" data-age="0.00"', svg)
