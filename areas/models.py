from django.db import models


class AreaBio(models.Model):
    name = models.CharField(max_length=150)
    age = models.IntegerField()
    country = models.CharField(max_length=150)

    def __str__(self):
        return '{}, {}, {}'.format(self.name, self.age, self.country)


class BioEntry(models.Model):
    living_space = models.IntegerField()
    number_of_people = models.IntegerField()
    year_from = models.IntegerField()
    year_to = models.IntegerField()

    area_bio = models.ForeignKey('areas.AreaBio', related_name='entries')
