from django.apps import apps
from django.contrib.auth.models import User
from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from django.test.client import RequestFactory
from django.test import TestCase, override_settings
from django.contrib.sessions.middleware import SessionMiddleware

from areas.admin import AreaBioAdmin, BioEntryInline
from areas.models import AreaBio, BioEntry
from areas.svg import (
    FUTURE_FILL,
    FUTURE_TOTAL_FILL,
    LABEL_FONT_SIZE,
    PERSON_FILL,
    TOTAL_FILL,
    _build_segments,
    render_area_bio_svg,
)


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

    def test_home_page_renders_bios_with_invalid_median_entries(self):
        user = User.objects.create_user(username='user', password='password')
        zero_people_bio = AreaBio.objects.create(
            user=user,
            name='Zero People',
            age=30,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=zero_people_bio,
            age_from=0,
            age_to=10,
            living_space=100,
            number_of_people=0,
            description='Geburt',
        )
        zero_years_bio = AreaBio.objects.create(
            user=user,
            name='Zero Years',
            age=30,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=zero_years_bio,
            age_from=20,
            age_to=20,
            living_space=100,
            number_of_people=3,
            description='Umzug',
        )
        self.client.force_login(user)

        response = self.client.get('/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ZERO PEOPLE, 30, BERLIN')
        self.assertContains(response, 'ZERO YEARS, 30, BERLIN')


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
            age_from=0,
            age_to=1,
            living_space=80,
            number_of_people=2,
            description='Umzug',
        )
        self.client.force_login(user)

        response = self.client.get(f'/admin/areas/areabio/{bio.pk}/change/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
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
        self.assertContains(response, f'href="/?graph={bio.uuid}"')
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
        self.client.force_login(user)

        response = self.client.get(f'/?graph={bio.uuid}', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jessica, 33, Berlin')
        self.assertContains(response, 'SVG Export')
        self.assertContains(response, 'Bearbeiten')
        self.assertContains(response, f'href="/graph/{bio.uuid}/export.svg"')
        self.assertContains(response, f'"admin_url": "/admin/areas/areabio/{bio.pk}/change/"')
        self.assertNotContains(response, 'download=""')
        self.assertContains(response, 'class="app bio-index"')
        self.assertContains(response, 'id="initial-graph-state"')
        self.assertContains(response, 'class="graph-image"')
        rendered = response.content.decode('utf-8')
        self.assertLess(rendered.index('Legende'), rendered.index('SVG Export'))
        self.assertLess(rendered.index('SVG Export'), rendered.index('Bearbeiten'))
        self.assertNotContains(response, 'bar-container')

    def test_frontend_popup_uses_export_image_source(self):
        user = User.objects.create_user(username='user', password='password')
        bio = AreaBio.objects.create(
            user=user,
            name='Jessica',
            age=33,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=0,
            age_to=1,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )
        self.client.force_login(user)

        response = self.client.get(f'/?graph={bio.uuid}', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'"/graph/{bio.uuid}/export.svg"')
        self.assertContains(response, 'class="graph-image"')

    def test_removed_frontend_detail_routes_are_not_available(self):
        bio = AreaBio.objects.create(
            name='Jessica',
            age=33,
            country='Berlin',
        )

        paths = [
            f'/graph/{bio.uuid}/view/',
            f'/view-graph/{bio.uuid}/',
        ]

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path, HTTP_HOST='localhost')
                self.assertEqual(response.status_code, 404)

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
    def test_area_bio_list_api_rejects_anonymous_users(self):
        bio = AreaBio.objects.create(
            name='Jessica',
            age=33,
            country='Berlin',
        )

        response = self.client.get('/api/area-bios/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, str(bio.uuid), status_code=403)

    def test_area_bio_list_api_remains_available_for_authenticated_frontend_filters(self):
        user = User.objects.create_user(username='user', password='password')
        bio = AreaBio.objects.create(
            user=user,
            name='Jessica',
            age=33,
            country='Berlin',
        )
        self.client.force_login(user)

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
        user = User.objects.create_user(username='user', password='password')
        bio = AreaBio.objects.create(
            user=user,
            name='Jessica',
            age=33,
            country='Berlin',
        )
        self.client.force_login(user)

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


class AuthTokenRemovedTests(TestCase):
    def test_rest_framework_auth_tokens_are_not_installed_or_registered_in_admin(self):
        admin_app_labels = {model._meta.app_label for model in site._registry}

        self.assertFalse(apps.is_installed('rest_framework.authtoken'))
        self.assertNotIn('authtoken', admin_app_labels)


class AreaBioModelTests(TestCase):
    def test_bio_entry_validation_rejects_zero_values_and_empty_age_range(self):
        bio = AreaBio.objects.create(
            name='Franzi',
            age=24,
            country='München',
        )
        entry = BioEntry(
            area_bio=bio,
            age_from=20,
            age_to=20,
            living_space=0,
            number_of_people=0,
            description='Wohnungssuche',
        )

        with self.assertRaises(ValidationError) as context:
            entry.full_clean()

        errors = context.exception.message_dict
        self.assertEqual(errors['living_space'], ['Wohnfläche muss größer als 0 sein.'])
        self.assertEqual(errors['number_of_people'], ['Personen im Haushalt muss größer als 0 sein.'])
        self.assertEqual(errors['age_to'], ['Bis-Alter muss größer als Von-Alter sein.'])

    def test_median_usage_returns_zero_without_valid_people_count(self):
        bio = AreaBio.objects.create(
            name='Zero People',
            age=30,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=0,
            age_to=10,
            living_space=100,
            number_of_people=0,
            description='Geburt',
        )

        self.assertEqual(bio.median_usage(), 0)

    def test_median_usage_returns_zero_without_measurable_years(self):
        bio = AreaBio.objects.create(
            name='Zero Years',
            age=30,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=20,
            age_to=20,
            living_space=100,
            number_of_people=3,
            description='Umzug',
        )

        self.assertEqual(bio.median_usage(), 0)

    def test_normalized_entries_extend_zero_year_changes_to_next_entry(self):
        bio = AreaBio.objects.create(
            name='Andy',
            age=15,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=0,
            age_to=1,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=1,
            age_to=2,
            living_space=124,
            number_of_people=3,
            description='Umzug',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=2,
            age_to=2,
            living_space=124,
            number_of_people=4,
            description='Schwester',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=3,
            age_to=7,
            living_space=123,
            number_of_people=4,
            description='Haus',
        )

        entries = list(bio.normalized_entries())

        self.assertEqual((entries[2].age_from, entries[2].age_to), (2, 3))
        self.assertNotIn(
            (2, 3, 0),
            [(entry.age_from, entry.age_to, entry.living_space) for entry in entries],
        )

    def test_bare_entries_include_future_projection_for_startpage_graphs(self):
        bio = AreaBio.objects.create(
            name='Andy',
            age=15,
            country='Berlin',
            gender=AreaBio.Gender.MALE,
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=0,
            age_to=20,
            living_space=123,
            number_of_people=4,
            description='Haus',
        )

        entries = list(bio.bare_entries())

        self.assertIn(
            (20, 78, 123),
            [(entry.age_from, entry.age_to, entry.living_space) for entry in entries],
        )
        self.assertTrue(any(entry.is_projection for entry in entries))

    def test_complete_manager_includes_graphs_without_gender(self):
        complete_bio = AreaBio.objects.create(
            name='Andy',
            age=15,
            country='Berlin',
            gender=AreaBio.Gender.MALE,
        )
        BioEntry.objects.create(
            area_bio=complete_bio,
            age_from=0,
            age_to=15,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )
        incomplete_bio = AreaBio.objects.create(
            name='Jess',
            age=15,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=incomplete_bio,
            age_from=0,
            age_to=15,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )

        complete_ids = set(AreaBio.objects.complete().values_list('pk', flat=True))

        self.assertIn(complete_bio.pk, complete_ids)
        self.assertIn(incomplete_bio.pk, complete_ids)

    def test_complete_manager_still_excludes_incomplete_graphs(self):
        complete_bio = AreaBio.objects.create(
            name='Andy',
            age=15,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=complete_bio,
            age_from=0,
            age_to=15,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )
        incomplete_bio = AreaBio.objects.create(
            name='Jess',
            age=15,
            country='Berlin',
        )

        complete_ids = set(AreaBio.objects.complete().values_list('pk', flat=True))

        self.assertIn(complete_bio.pk, complete_ids)
        self.assertNotIn(incomplete_bio.pk, complete_ids)


class BioEntryInlineAdminTests(TestCase):
    def test_inline_formset_rejects_zero_values_and_empty_age_range(self):
        user = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@example.com',
        )
        bio = AreaBio.objects.create(
            user=user,
            name='Franzi',
            age=24,
            country='München',
        )
        request = RequestFactory().get('/')
        request.user = user

        inline = BioEntryInline(AreaBio, site)
        formset_class = inline.get_formset(request, bio)
        prefix = formset_class.get_default_prefix()
        formset = formset_class(
            data={
                f'{prefix}-TOTAL_FORMS': '1',
                f'{prefix}-INITIAL_FORMS': '0',
                f'{prefix}-MIN_NUM_FORMS': '0',
                f'{prefix}-MAX_NUM_FORMS': '1000',
                f'{prefix}-0-id': '',
                f'{prefix}-0-age_from': '20',
                f'{prefix}-0-age_to': '20',
                f'{prefix}-0-living_space': '0',
                f'{prefix}-0-number_of_people': '0',
                f'{prefix}-0-description': 'Wohnungssuche',
            },
            instance=bio,
            prefix=prefix,
        )

        self.assertFalse(formset.is_valid())
        errors = formset.forms[0].errors
        self.assertEqual(errors['living_space'], ['Wohnfläche muss größer als 0 sein.'])
        self.assertEqual(errors['number_of_people'], ['Personen im Haushalt muss größer als 0 sein.'])
        self.assertEqual(errors['age_to'], ['Bis-Alter muss größer als Von-Alter sein.'])

    def test_empty_inline_prefills_from_last_entry(self):
        user = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@example.com',
        )
        bio = AreaBio.objects.create(
            user=user,
            name='Andy',
            age=15,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=0,
            age_to=12,
            living_space=80,
            number_of_people=2,
            description='Umzug',
            location=BioEntry.Location.BIG_CITY,
            typology=BioEntry.Typology.TWO_ROOMS,
            tenure=BioEntry.Tenure.RENT,
        )

        request = RequestFactory().get('/')
        request.user = user

        inline = BioEntryInline(AreaBio, site)
        formset_class = inline.get_formset(request, bio)
        formset = formset_class(instance=bio)
        empty_form = formset.empty_form

        self.assertEqual(empty_form.initial['age_from'], 12)
        self.assertIsNone(empty_form.initial['age_to'])
        self.assertEqual(empty_form.initial['living_space'], 80)
        self.assertEqual(empty_form.initial['number_of_people'], 2)
        self.assertEqual(empty_form.initial['description'], '')
        self.assertEqual(empty_form.initial['location'], BioEntry.Location.BIG_CITY)
        self.assertEqual(empty_form.initial['typology'], BioEntry.Typology.TWO_ROOMS)
        self.assertEqual(empty_form.initial['tenure'], BioEntry.Tenure.RENT)

    def test_change_view_only_requests_scroll_after_save_and_continue(self):
        user = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@example.com',
        )
        bio = AreaBio.objects.create(
            user=user,
            name='Andy',
            age=15,
            country='Berlin',
        )

        request = RequestFactory().get('/')
        request.user = user
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request.session['areas_areabio_scroll_to_last_inline'] = True

        admin = AreaBioAdmin(AreaBio, site)
        response = admin.change_view(request, str(bio.pk))

        self.assertTrue(response.context_data['scroll_to_last_inline_after_save'])
        self.assertNotIn('areas_areabio_scroll_to_last_inline', request.session)


@override_settings(LIFE_EXPECTANCY_BY_GENDER={'female': 83, 'male': 78})
class AreaBioSvgTests(TestCase):
    def test_svg_renderer_uses_scaled_geometry_and_labels(self):
        bio = AreaBio.objects.create(
            name='Julia',
            age=12,
            country='Berlin',
            gender=AreaBio.Gender.FEMALE,
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=0,
            age_to=12,
            living_space=100,
            number_of_people=4,
            description='Testphase',
        )

        svg = render_area_bio_svg(bio)

        self.assertIn('<svg', svg)
        self.assertIn('@font-face', svg)
        self.assertIn(f'font-size:{LABEL_FONT_SIZE:.2f}px', svg)
        self.assertIn('fill:#000;', svg)
        self.assertIn('100 m²', svg)
        self.assertIn('25 m²', svg)
        self.assertIn(f'fill="{TOTAL_FILL}" data-kind="total" data-age-from="0.00" data-age-to="12.00"', svg)
        self.assertIn(f'fill="{PERSON_FILL}" data-kind="personal" data-age-from="0.00" data-age-to="12.00"', svg)
        self.assertIn(f'fill="{FUTURE_TOTAL_FILL}" data-kind="total" data-age-from="12.00" data-age-to="83.00"', svg)
        self.assertIn(f'fill="{FUTURE_FILL}" data-kind="personal" data-age-from="12.00" data-age-to="83.00"', svg)
        self.assertIn('data-kind="description" data-age="0.00"', svg)
        self.assertNotIn('data-kind="axis-grid" data-age="0.00"', svg)
        self.assertNotIn('data-kind="description" data-age="12.00"', svg)
        self.assertIn('width="100.00" height="355.00"', svg)
        self.assertIn('width="25.00" height="60.00"', svg)
        self.assertNotIn('data-kind="x-axis-total"', svg)
        self.assertNotIn('data-kind="x-axis-personal"', svg)
        self.assertIn('data-kind="area-measure-total-label"', svg)
        self.assertIn('>100 m²</text>', svg)
        self.assertIn('data-kind="area-measure-personal-line"', svg)
        self.assertIn('x1="92.50" y1="454.60" x2="117.50" y2="454.60"', svg)
        self.assertIn('data-kind="area-measure-personal-label"', svg)
        self.assertIn('>25 m²</text>', svg)
        self.assertIn('x2="50.00"', svg)
        self.assertNotIn('data-kind="axis-grid" data-age="12.00"', svg)
        self.assertNotIn('data-kind="axis-grid" data-age="83.00"', svg)
        self.assertNotIn('83 Jahre', svg)
        self.assertLess(
            svg.index('data-kind="axis-tick"'),
            svg.index(f'fill="{TOTAL_FILL}" data-kind="total" data-age-from="0.00"'),
        )
        self.assertNotIn('ges. 100 m² / max. 25 m²', svg)
        self.assertNotIn('ges.', svg)
        self.assertNotIn('max.', svg)

    def test_svg_renderer_stops_future_projection_after_actual_age_for_older_people(self):
        bio = AreaBio.objects.create(
            name='Julia',
            age=90,
            country='Berlin',
            gender=AreaBio.Gender.FEMALE,
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=0,
            age_to=90,
            living_space=100,
            number_of_people=4,
            description='Testphase',
        )

        svg = render_area_bio_svg(bio)

        self.assertNotIn('90 Jahre', svg)
        self.assertIn('data-kind="total" data-age-from="0.00" data-age-to="90.00"', svg)
        self.assertIn('data-kind="personal" data-age-from="0.00" data-age-to="90.00"', svg)
        self.assertNotIn(FUTURE_TOTAL_FILL, svg)
        self.assertNotIn(FUTURE_FILL, svg)
        self.assertIn('data-kind="area-measure-total-label"', svg)
        self.assertIn('data-kind="area-measure-personal-line"', svg)
        self.assertNotIn('ges. 100 m² / max. 25 m²', svg)

    def test_svg_renderer_extends_zero_year_changes_to_next_entry(self):
        bio = AreaBio.objects.create(
            name='Andy',
            age=15,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=9,
            age_to=10,
            living_space=124,
            number_of_people=3,
            description='Umzug',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=10,
            age_to=10,
            living_space=124,
            number_of_people=4,
            description='Schwester',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=11,
            age_to=15,
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

    def test_svg_renderer_offsets_duplicate_description_ages(self):
        bio = AreaBio.objects.create(
            name='Andy',
            age=15,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=9,
            age_to=10,
            living_space=100,
            number_of_people=2,
            description='Umzug',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=10,
            age_to=10,
            living_space=100,
            number_of_people=4,
            description='Schwester',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=10,
            age_to=11,
            living_space=100,
            number_of_people=3,
            description='Haus',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=11,
            age_to=15,
            living_space=100,
            number_of_people=3,
            description='Spaeter',
        )

        svg = render_area_bio_svg(bio)

        self.assertIn('data-kind="description" data-age="10.00" x="169.00" y="51.73">Schwester</text>', svg)
        self.assertIn('data-kind="description" data-age="10.00" x="169.00" y="57.04">Haus</text>', svg)

    def test_svg_renderer_extends_first_entry_to_birth(self):
        bio = AreaBio.objects.create(
            name='Andy',
            age=45,
            country='Berlin',
        )
        BioEntry.objects.create(
            area_bio=bio,
            age_from=8,
            age_to=9,
            living_space=120,
            number_of_people=3,
            description='Geburt',
        )

        svg = render_area_bio_svg(bio)

        self.assertIn('data-kind="total" data-age-from="0.00" data-age-to="9.00"', svg)
        self.assertIn('data-kind="personal" data-age-from="0.00" data-age-to="9.00"', svg)
        self.assertIn('data-kind="description" data-age="0.00"', svg)
