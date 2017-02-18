from django.db import models
from django.db.models import Max


class AreaBioManager(models.Manager):
    def published(self):
        return self.filter(published=True)


class AreaBio(models.Model):
    name = models.CharField(max_length=150)
    age = models.IntegerField()
    country = models.CharField(max_length=150)

    published = models.BooleanField(default=False)
    data = AreaBioManager()

    def __str__(self):
        return '{}, {}, {}'.format(self.name, self.age, self.country)

    def max_space(self):
        return self.entries.aggregate(Max('living_space'))['living_space__max']


class BioEntry(models.Model):
    living_space = models.IntegerField()
    number_of_people = models.IntegerField()
    year_from = models.IntegerField()
    year_to = models.IntegerField()

    area_bio = models.ForeignKey('areas.AreaBio', related_name='entries')

    class Meta:
        ordering = ['year_from']

    def __str__(self):
        return '{}-{}, {} in {} m²'.format(
            self.year_from, self.year_to, self.number_of_people, self.living_space)

    def years(self):
        return (self.year_to - self.year_from) * 5

    def percentage(self):
        max_value = self.area_bio.max_space()
        percentage = int(float(self.living_space) / float(max_value) * 100)
        return percentage

    def person_percentage(self):
        return int(float(100) / float(self.number_of_people))
