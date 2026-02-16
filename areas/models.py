# -*- coding: utf-8 -*-
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.db.models import Max
from django.template.defaultfilters import upper
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from areas.utils import guess_name


class AreaBioManager(models.Manager):
    def published(self):
        return self.filter(published=True)


class AreaBio(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='area_bios', null=True, blank=True, verbose_name=_(u'Nutzer'))

    name = models.CharField(verbose_name=_(u'Name'), max_length=150, null=True)
    age = models.IntegerField(verbose_name=_(u'Alter'), null=True)
    country = models.CharField(verbose_name=_(u'Stadt'), max_length=150, null=True)

    published = models.BooleanField(default=False, verbose_name=_(u'Veröffentlicht'))
    objects = AreaBioManager()
    created = models.DateTimeField(auto_now_add=True, null=True, editable=False, verbose_name=_(u'Erstellt'))

    mailed_to = models.CharField(max_length=200, null=True, blank=True, verbose_name=_(u'Per E-Mail versendet an'))

    class Meta:
        verbose_name = u'Flächenbiografie'
        verbose_name_plural = u'Flächenbiografien'
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

    def height(self):
        if hasattr(self, '_height'):
            return self._height

        self._height = 0
        for entry in self.normalized_entries():
            self._height += entry.year_to - entry.year_from

        self._height = max(self._height, 10)
        return self._height

    def axis_height(self):
        return (min(80, self.height() + 3)) / .8

    def show_30(self):
        return 'gray' if self.height() + 7 < 30 else ''

    def show_60(self):
        return 'gray' if self.height() + 7 < 60 else ''

    def send_to(self, email):
        self.mailed_to = email
        self.save()


        send_mail(
            _(u'Deine Flächenbiografie'),
            render_to_string('messages/send_graph.txt', {'name': self.name, 'graph': self}),
            'do-not-reply@pepperz.de',
            [email],
        )

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

        entries = []
        remaining_years = 80
        last_year = self.created.year - self.age if self.age else 0
        for entry in self.entries.all():
            if last_year and entry.year_from > last_year:
                space = BioEntry(
                    living_space=0,
                    number_of_people=0,
                    year_from=last_year,
                    year_to=entry.year_from
                )
                entries.append(space)

            # fix the years
            if entry.num_years > remaining_years:
                entry.year_to = entry.year_from + remaining_years

            entries.append(entry)
            last_year = entry.year_to
            remaining_years -= entry.num_years
            if remaining_years <= 0:
                break  # out of this loop because we hit the wall

        return entries

    def get_absolute_url(self):
        return reverse('view-graph', args=[self.uuid])

    def median_usage(self):
        years = 0
        used = 0

        if not self.entries.all():
            return 0

        for entry in self.entries.all():
            years += entry.num_years
            used += entry.num_years * entry.living_space / entry.number_of_people

        return int(round(float(used) / years))


class EntryManager(models.Manager):
    use_for_related_fields = True

    def reversed(self):
        return self.order_by('-year_from')


class BioEntry(models.Model):
    class Location(models.TextChoices):
        METROPOLIS = 'metropolis', _('Metropole (ab 1 Mio)')
        BIG_CITY = 'big_city', _('Großstadt (ab 100.000)')
        MEDIUM_CITY = 'medium_city', _('Mittelstadt (ab 20.000)')
        SMALL_CITY = 'small_city', _('Kleinstadt (ab 5.000)')
        VILLAGE = 'village', _('Dorf')
        ISOLATED = 'isolated', _('Alleinlage')
        NO_FIXED_RESIDENCE = 'no_fixed_residence', _('Ohne festen Wohnsitz')

    class Typology(models.TextChoices):
        HOUSE = 'house', _('Haus')
        DORMITORY = 'dormitory', _('Wohnheim')
        ONE_ROOM = '1_room', _('1 Zimmer Wohnung')
        TWO_ROOMS = '2_rooms', _('2 Zi')
        THREE_ROOMS = '3_rooms', _('3 Zi')
        FOUR_ROOMS = '4_rooms', _('4 Zi')
        FIVE_ROOMS = '5_rooms', _('5 Zi')
        MORE_THAN_FIVE = 'more_than_5_rooms', _('Mehr als 5 Zimmer')

    class Tenure(models.TextChoices):
        RENT = 'rent', _('Miete')
        OWNERSHIP = 'ownership', _('Eigentum')

    class OwnerCategory(models.TextChoices):
        PRIVATE_PERSON = 'private_person', _('Privatperson')
        COOPERATIVE = 'cooperative', _('Genossenschaft')
        PUBLIC_HOUSING_COMPANY = 'public_housing_company', _('Wohnbaugesellschaft kommunal')
        PRIVATE_HOUSING_COMPANY = 'private_housing_company', _('Wohnbaugesellschaft privatwirtschaftlich')
        OTHER_PRIVATE_ACTORS = 'other_private_actors', _('Andere privatwirtschaftliche Akteure')

    class ConstructionYearCategory(models.TextChoices):
        PRE_1920 = 'pre_1920', _('vor 1920')
        YEAR_1920_1945 = '1920_1945', _('1920-1945')
        YEAR_1945_1960 = '1945_1960', _('1945-1960')
        YEAR_1960_1970 = '1960_1970', _('1960-1970')
        YEAR_1970_1980 = '1970_1980', _('1970-1980')
        YEAR_1990_2000 = '1990_2000', _('1990-2000')
        YEAR_2000_2010 = '2000_2010', _('2000-2010')
        FROM_2010 = 'from_2010', _('ab 2010')

    living_space = models.IntegerField(verbose_name=_('Wohnfläche'))
    number_of_people = models.IntegerField(verbose_name=_('Personen im Haushalt'))
    year_from = models.IntegerField(verbose_name=_('Von'))
    year_to = models.IntegerField(verbose_name=_('Bis'))
    description = models.CharField(verbose_name=_('Grund für den Wechsel'), max_length=35, blank=True, null=True)
    location = models.CharField(verbose_name=_('Lage'), max_length=50, choices=Location.choices, blank=True, null=True)
    postal_code = models.CharField(verbose_name=_('PLZ'), max_length=20, blank=True, null=True)
    typology = models.CharField(verbose_name=_('Typologie'), max_length=30, choices=Typology.choices, blank=True, null=True)
    tenure = models.CharField(verbose_name=_('Miete / Eigentum'), max_length=20, choices=Tenure.choices, blank=True, null=True)
    owner_category = models.CharField(verbose_name=_('Eigentümerkategorie'), max_length=40, choices=OwnerCategory.choices, blank=True, null=True)
    construction_year_category = models.CharField(
        verbose_name=_('Baujahr'),
        max_length=20,
        choices=ConstructionYearCategory.choices,
        blank=True,
        null=True
    )
    country_if_not_germany = models.CharField(verbose_name=_('Land (falls nicht DE)'), max_length=150, blank=True, null=True)

    area_bio = models.ForeignKey('areas.AreaBio', on_delete=models.CASCADE, related_name='entries')
    objects = EntryManager()

    class Meta:
        ordering = ['year_from']
        verbose_name = 'Biografieeintrag'
        verbose_name_plural = 'Biografieeinträge'

    def __str__(self):
        return u'{}-{}, {} in {} m²'.format(
            self.year_from, self.year_to, self.number_of_people, self.living_space)

    def __unicode__(self):
        return self.__str__()

    def future(self):
        if self.year_from >= self.area_bio.created.year:
            return 'future'
        return ''

    @property
    def num_years(self):
        return self.year_to - self.year_from

    @property
    def years(self):
        diff = self.num_years
        if diff == 0:
            diff = 0.25
        return float(diff) / 0.8

    def small_entry(self):
        return 'small-entry' if not bool(self.year_to - self.year_from) else ''

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
        if self.area_bio.age:
            calculated = self.area_bio.age - (self.area_bio.created.year - self.year_from)
            # might return -1 depending on day of year (pre/post birthday)
            age = max(calculated, 0)
            return age if age else 'Baby'
        return ''
