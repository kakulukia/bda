# -*- coding: utf-8 -*-
from rest_framework import serializers

from areas.models import AreaBio


class AreaBioSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AreaBio
        fields = (
            'name',
            'age',
            'country',
            'gender',
            'id',
            'uuid',
        )


    def validate(self, attrs):
        country = attrs.get('country')
        if country:
            attrs['country'] = country.capitalize()
        return attrs
