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

        bio = attrs['area_bio']

        if bio.to_many_entries():
            raise serializers.ValidationError(u"Die Einträge überschreiten Dein Alter.")

        return attrs
