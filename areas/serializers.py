from rest_framework import serializers

from areas.models import AreaBio, BioEntry


class AreaBioSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AreaBio
        fields = ('name', 'age', 'country', 'id')


class EntrySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BioEntry
        fields = (
            'living_space',
            'number_of_people',
            'year_from',
            'year_to',
            'description',
        )
