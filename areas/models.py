# -*- coding: utf-8 -*-
import uuid

from django.core.mail import send_mail
from django.db import models
from django.db.models import Max
from django.template.defaultfilters import upper
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from areas.utils import guess_name


class AreaBioManager(models.Manager):
    def published(self):
        return self.filter(published=True)


class AreaBio(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    name = models.CharField(verbose_name=_(u'Name'), max_length=150, null=True)
    age = models.IntegerField(verbose_name=_(u'Age'), null=True)
    country = models.CharField(verbose_name=_(u'Country'), max_length=150, null=True)

    published = models.BooleanField(default=False)
    objects = AreaBioManager()

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
        context = {'name': guess_name(email), 'graph': self}
        send_mail(
            _(u'Deine Flächenbiografie'),
            render_to_string('messages/send_graph.txt', context),
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
        print(years)
        return years > self.age / 0.8

    def normalized_entries(self):

        entries = []
        last_year = 0
        for entry in self.entries.all():
            if last_year and entry.year_from > last_year:
                space = BioEntry(
                    living_space=0,
                    number_of_people=0,
                    year_from=last_year,
                    year_to=entry.year_from
                )
                entries.append(space)
            entries.append(entry)
            last_year = entry.year_to

        return entries

    def get_absolute_url(self):
        return reverse('edit-graph', args=[self.uuid])


class EntryManager(models.Manager):
    use_for_related_fields = True

    def reversed(self):
        return self.order_by('-year_from')


class BioEntry(models.Model):
    living_space = models.IntegerField(verbose_name=_('Living space'))
    number_of_people = models.IntegerField(verbose_name=_('Number of people'))
    year_from = models.IntegerField(verbose_name=_('From'))
    year_to = models.IntegerField(verbose_name=_('To'))
    description = models.CharField(verbose_name=_('Reason'), max_length=142, blank=True, null=True)

    area_bio = models.ForeignKey('areas.AreaBio', related_name='entries')
    objects = EntryManager()

    class Meta:
        ordering = ['year_from']

    def __str__(self):
        return u'{}-{}, {} in {} m²'.format(
            self.year_from, self.year_to, self.number_of_people, self.living_space)

    def __unicode__(self):
        return self.__str__()

    @property
    def years(self):
        diff = self.year_to - self.year_from
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

    def description_percentage(self):

        bar_length = (100 - self.percentage()) / 2 + 5
        return bar_length
