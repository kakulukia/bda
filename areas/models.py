# -*- coding: utf-8 -*-
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.template.defaultfilters import upper
from django.template.loader import render_to_string
from django.urls import reverse

from areas.rendering import build_timeline_entries, graph_end_age as shared_graph_end_age, graph_life_expectancy


class AreaBioManager(models.Manager):
    def complete(self):
        return (
            self.filter(
                name__isnull=False,
                age__isnull=False,
                country__isnull=False,
                entries__isnull=False,
            )
            .exclude(name='')
            .exclude(country='')
            .distinct()
        )


class AreaBio(models.Model):
    class Gender(models.TextChoices):
        FEMALE = 'female', 'Weiblich'
        MALE = 'male', 'Männlich'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='area_bios', null=True, blank=True, verbose_name=u'Nutzer')

    name = models.CharField(verbose_name=u'Name', max_length=150, null=True)
    age = models.IntegerField(verbose_name=u'Alter', null=True, blank=True)
    country = models.CharField(verbose_name=u'Stadt', max_length=150, null=True)
    gender = models.CharField(
        verbose_name=u'Geschlecht',
        max_length=10,
        choices=Gender.choices,
        null=True,
        help_text=u'Wird für die Lebenserwartungs-Projektion verwendet.',
    )

    objects = AreaBioManager()
    created = models.DateTimeField(auto_now_add=True, null=True, editable=False, verbose_name=u'Erstellt')

    class Meta:
        verbose_name = u'Wohnbiografie'
        verbose_name_plural = u'Wohnbiografien'
        ordering = ['-created']

    def __str__(self):
        return u'{}, {}, {}'.format(self.name, self.age, self.country)

    def __unicode__(self):
        return self.__str__()

    def max_space(self, stretched=False):
        if hasattr(self, '_max_space'):
            return self._max_space

        if stretched:
            max_space_all = BioEntry.objects.all().aggregate(Max('living_space'))['living_space__max']
            max_space_self = self.entries.aggregate(Max('living_space'))['living_space__max']

            capped_max = min(max_space_all, 300)
            max_space = max(max_space_self, capped_max)

        else:
            max_space = self.entries.aggregate(Max('living_space'))['living_space__max'] or 0

        if max_space:
            self._max_space = max_space
        return max_space

    def bare_display(self, stretched=False):
        self._stretched = stretched
        self.bare = True
        return render_to_string('partials/bare_graph.pug', {'graph': self})

    def bare_display_stretched(self):
        return self.bare_display(stretched=True)

    def description(self):
        desc = self.name
        if self.name and self.age:
            desc += u', {}'.format(self.age)
        if self.age and self.country:
            desc += u', {}'.format(self.country)
        return upper(desc)

    def life_expectancy(self):
        return graph_life_expectancy(self)

    def graph_end_age(self):
        return shared_graph_end_age(self)

    def height(self):
        if hasattr(self, '_height'):
            return self._height

        self._height = 0
        for entry in self.normalized_entries():
            self._height += entry.age_to - entry.age_from

        self._height = max(self._height, 10)
        return self._height

    def axis_height(self):
        return (min(80, self.height() + 3)) / .8

    def show_30(self):
        return 'gray' if self.height() + 7 < 30 else ''

    def show_60(self):
        return 'gray' if self.height() + 7 < 60 else ''

    def to_many_entries(self, exclude=None, add=0):
        years = 0
        qs = self.entries.all()
        if exclude:
            qs = qs.exclude(id=exclude.id)
        for entry in qs:
            if entry.years >= 1:
                years += entry.years
        years += add
        return years > self.age

    def normalized_entries(self):
        return build_timeline_entries(self, include_gaps=True, split_current_age=False, project_to_end_age=False)

    def bare_entries(self):
        return build_timeline_entries(self, include_gaps=True, split_current_age=False, project_to_end_age=True)

    def get_absolute_url(self):
        return '{}?graph={}'.format(reverse('index'), self.uuid)

    def get_export_svg_url(self):
        return reverse('export-graph-svg', args=[self.uuid])

    def get_admin_url(self):
        return reverse('admin:areas_areabio_change', args=[self.pk])

    def median_usage(self):
        years = 0
        used = 0

        for entry in self.entries.all():
            people = entry.number_of_people or 0
            if entry.num_years <= 0 or people <= 0:
                continue
            years += entry.num_years
            used += entry.num_years * (entry.living_space or 0) / people

        if not years:
            return 0

        return int(round(float(used) / years))


class EntryManager(models.Manager):
    use_for_related_fields = True

    def reversed(self):
        return self.order_by('-age_from')


class BioEntry(models.Model):
    class Location(models.TextChoices):
        METROPOLIS = 'metropolis', 'Metropole (ab 1 Mio)'
        BIG_CITY = 'big_city', 'Großstadt (ab 100.000)'
        MEDIUM_CITY = 'medium_city', 'Mittelstadt (ab 20.000)'
        SMALL_CITY = 'small_city', 'Kleinstadt (ab 5.000)'
        VILLAGE = 'village', 'Dorf'
        ISOLATED = 'isolated', 'Alleinlage'
        NO_FIXED_RESIDENCE = 'no_fixed_residence', 'Ohne festen Wohnsitz'

    class Typology(models.TextChoices):
        HOUSE = 'house', 'Haus'
        DORMITORY = 'dormitory', 'Wohnheim'
        ONE_ROOM = '1_room', '1 Zimmer Wohnung'
        TWO_ROOMS = '2_rooms', '2 Zi'
        THREE_ROOMS = '3_rooms', '3 Zi'
        FOUR_ROOMS = '4_rooms', '4 Zi'
        FIVE_ROOMS = '5_rooms', '5 Zi'
        MORE_THAN_FIVE = 'more_than_5_rooms', 'Mehr als 5 Zimmer'

    class Tenure(models.TextChoices):
        RENT = 'rent', 'Miete'
        OWNERSHIP = 'ownership', 'Eigentum'

    class OwnerCategory(models.TextChoices):
        PRIVATE_PERSON = 'private_person', 'Privatperson'
        COOPERATIVE = 'cooperative', 'Genossenschaft'
        PUBLIC_HOUSING_COMPANY = 'public_housing_company', 'Wohnbaugesellschaft kommunal'
        PRIVATE_HOUSING_COMPANY = 'private_housing_company', 'Wohnbaugesellschaft privatwirtschaftlich'
        OTHER_PRIVATE_ACTORS = 'other_private_actors', 'Andere privatwirtschaftliche Akteure'

    class ConstructionYearCategory(models.TextChoices):
        PRE_1920 = 'pre_1920', 'vor 1920'
        YEAR_1920_1945 = '1920_1945', '1920-1945'
        YEAR_1945_1960 = '1945_1960', '1945-1960'
        YEAR_1960_1970 = '1960_1970', '1960-1970'
        YEAR_1970_1980 = '1970_1980', '1970-1980'
        YEAR_1990_2000 = '1990_2000', '1990-2000'
        YEAR_2000_2010 = '2000_2010', '2000-2010'
        FROM_2010 = 'from_2010', 'ab 2010'

    living_space = models.IntegerField(verbose_name='Wohnfläche')
    number_of_people = models.IntegerField(verbose_name='Personen im Haushalt')
    age_from = models.IntegerField(verbose_name='Von (Alter)')
    age_to = models.IntegerField(verbose_name='Bis (Alter)')
    description = models.CharField(verbose_name='Grund für den Wechsel', max_length=35, blank=True, null=True)
    location = models.CharField(verbose_name='Lage', max_length=50, choices=Location.choices, blank=True, null=True)
    postal_code = models.CharField(verbose_name='PLZ', max_length=20, blank=True, null=True)
    typology = models.CharField(verbose_name='Typologie', max_length=30, choices=Typology.choices, blank=True, null=True)
    tenure = models.CharField(verbose_name='Miete / Eigentum', max_length=20, choices=Tenure.choices, blank=True, null=True)
    owner_category = models.CharField(verbose_name='Eigentümerkategorie', max_length=40, choices=OwnerCategory.choices, blank=True, null=True)
    construction_year_category = models.CharField(
        verbose_name='Baujahr',
        max_length=20,
        choices=ConstructionYearCategory.choices,
        blank=True,
        null=True
    )
    country_if_not_germany = models.CharField(verbose_name='Land (falls nicht DE)', max_length=150, blank=True, null=True)

    area_bio = models.ForeignKey('areas.AreaBio', on_delete=models.CASCADE, related_name='entries')
    objects = EntryManager()

    class Meta:
        ordering = ['age_from']
        verbose_name = 'Biografieeintrag'
        verbose_name_plural = 'Biografieeinträge'

    def __str__(self):
        return u'{}-{}, {} in {} m²'.format(
            self.age_from, self.age_to, self.number_of_people, self.living_space)

    def __unicode__(self):
        return self.__str__()

    def clean(self):
        super().clean()
        errors = {}

        if self.living_space is not None and self.living_space <= 0:
            errors['living_space'] = 'Wohnfläche muss größer als 0 sein.'
        if self.number_of_people is not None and self.number_of_people <= 0:
            errors['number_of_people'] = 'Personen im Haushalt muss größer als 0 sein.'
        if self.age_from is not None and self.age_to is not None and self.age_to <= self.age_from:
            errors['age_to'] = 'Bis-Alter muss größer als Von-Alter sein.'

        if errors:
            raise ValidationError(errors)

    def future(self):
        try:
            current_age = self.area_bio.age
        except Exception:
            return ''
        if current_age is None or self.age_from is None:
            return ''
        return 'future' if self.age_from >= current_age else ''

    @property
    def num_years(self):
        return self.age_to - self.age_from

    @property
    def years(self):
        diff = self.num_years
        if diff == 0:
            diff = 0.25
        return float(diff) / 0.8

    def small_entry(self):
        return 'small-entry' if not bool(self.age_to - self.age_from) else ''

    def percentage(self, stretched=False):
        if not self.living_space:
            return 0
        max_value = self.area_bio.max_space(stretched=self.area_bio._stretched)
        percentage = int(float(self.living_space) / float(max_value) * 100)
        return percentage

    def percentage_stretched(self):
        self.percentage(stretched=True)

    def person_percentage(self):
        if self.number_of_people:
            return int(float(100) / float(self.number_of_people))
        return 0

    @property
    def living_space_per_person(self):
        if not self.number_of_people:
            return None
        return float(self.living_space) / float(self.number_of_people)

    def description_percentage(self):
        bar_length = (100 - self.percentage()) / 2 + 5
        return bar_length

    def age(self):
        if self.age_from is None:
            return ''
        return self.age_from or 'Baby'
