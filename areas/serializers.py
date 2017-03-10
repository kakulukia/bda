# -*- coding: utf-8 -*-
from rest_framework import serializers

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


        if bio.to_many_entries(exclude=self.instance, add=attrs['year_to']-attrs['year_from']):
            raise serializers.ValidationError(u"Die Einträge überschreiten Dein Alter.")

        return attrs
