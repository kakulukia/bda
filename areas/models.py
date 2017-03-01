# -*- coding: utf-8 -*-
import uuid

from django.db import models
from django.db.models import Max
from django.template.defaultfilters import upper
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _


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

    def max_space(self):
        return self.entries.aggregate(Max('living_space'))['living_space__max']

    def bare_display(self):
        return render_to_string('partials/bare_graph.pug', {'graph': self})

    def description(self):
        print(self.name, self.age, self.country)
        desc = self.name
        if self.name and self.age:
            desc += u', {}'.format(self.age)
        if self.age and self.country:
            desc += u', {}'.format(self.country)
        return upper(desc)


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

    def years(self):
        diff = self.year_to - self.year_from
        return float(diff) / 0.8

    def percentage(self):
        max_value = self.area_bio.max_space()
        percentage = int(float(self.living_space) / float(max_value) * 100)
        return percentage

    def person_percentage(self):
        return int(float(100) / float(self.number_of_people))
