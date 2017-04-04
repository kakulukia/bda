# -*- coding: utf-8 -*-
from django.utils.translation import activate
from rest_framework import serializers
from django_countries import countries

from areas.models import AreaBio, BioEntry


class AreaBioSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AreaBio
        fields = (
            'name',
            'age',
            'country',
            'id',
            'uuid',
            'published',
        )

    def validate(self, data):
        country = data['country'].capitalize()
        data['country'] = country
        if not country in dict(countries).values():
            activate('en')
            if not country in dict(countries).values():
                raise serializers.ValidationError('Das Land ist unbekannt.')
            else:
                for code, name in dict(countries).iteritems():
                    if name == country:
                        activate('de')
                        print(dict(countries)[code])
                        data['country'] = dict(countries)[code]

        return data


class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BioEntry
        fields = (
            'id',
            'living_space',
            'number_of_people',
            'year_from',
            'year_to',
            'description',
            'area_bio',
        )
    def validate(self, attrs):

        if attrs['year_from'] > attrs['year_to']:
            raise serializers.ValidationError(u'Der Zeitraum ist ungültig.')

        bio = attrs['area_bio']
        if not bio.age:
            raise serializers.ValidationError(u'Bitte trage erst Name, Alter und Land ein.')

        # disabled for now .. macht nur aerger
        # if bio.to_many_entries(exclude=self.instance, add=attrs['year_to']-attrs['year_from']):
        #     raise serializers.ValidationError(u"Die Einträge überschreiten Dein Alter.")

        return attrs
