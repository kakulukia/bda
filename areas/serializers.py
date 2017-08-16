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

    def validate(self, attrs):
        attrs['country'] = attrs['country'].capitalize()
        return attrs


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

        if attrs['year_from'] == attrs['year_to']:
            raise serializers.ValidationError(u'Die Wohndauer bitte immer in vollen Jahren angeben, '
                                              u'gegebenenfalls auf ein volles Jahr aufrunden.')

        bio = attrs['area_bio']
        if not bio.age:
            raise serializers.ValidationError(u'Bitte trage erst Name, Alter und Land ein.')

        # disabled for now .. macht nur aerger
        # if bio.to_many_entries(exclude=self.instance, add=attrs['year_to']-attrs['year_from']):
        #     raise serializers.ValidationError(u"Die Einträge überschreiten Dein Alter.")

        if bio.entries.filter(year_from=attrs['year_from']).exclude(id=self.context['request'].data.get('id')).exists():
            raise serializers.ValidationError(
                u'Mehrere Einträge pro Jahr sind für eine übersichtliche grafische Darstellung der '
                u'Flächenbiografien nicht möglich. Gegebenenfalls Veränderungen auf das folgende Jahr verschieben.')

        return attrs
