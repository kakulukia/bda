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
            'id',
            'uuid',
        )


    def validate(self, attrs):
        attrs['country'] = attrs['country'].capitalize()
        return attrs
