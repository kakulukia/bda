# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('areas', '0015_auto_20170513_0136'),
    ]

    operations = [
        migrations.AddField(
            model_name='bioentry',
            name='construction_year_category',
            field=models.CharField(blank=True, choices=[('pre_1920', 'vor 1920'), ('1920_1945', '1920-1945'), ('1945_1960', '1945-1960'), ('1960_1970', '1960-1970'), ('1970_1980', '1970-1980'), ('1990_2000', '1990-2000'), ('2000_2010', '2000-2010'), ('from_2010', 'ab 2010')], max_length=20, null=True, verbose_name='Baujahr'),
        ),
        migrations.AddField(
            model_name='bioentry',
            name='country_if_not_germany',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Land (falls nicht DE)'),
        ),
        migrations.AddField(
            model_name='bioentry',
            name='location',
            field=models.CharField(blank=True, choices=[('metropolis', 'Metropole (ab 1 Mio)'), ('big_city', 'Großstadt (ab 100.000)'), ('medium_city', 'Mittelstadt (ab 20.000)'), ('small_city', 'Kleinstadt (ab 5.000)'), ('village', 'Dorf'), ('isolated', 'Alleinlage'), ('no_fixed_residence', 'Ohne festen Wohnsitz')], max_length=50, null=True, verbose_name='Lage'),
        ),
        migrations.AddField(
            model_name='bioentry',
            name='owner_category',
            field=models.CharField(blank=True, choices=[('private_person', 'Privatperson'), ('cooperative', 'Genossenschaft'), ('public_housing_company', 'Wohnbaugesellschaft kommunal'), ('private_housing_company', 'Wohnbaugesellschaft privatwirtschaftlich'), ('other_private_actors', 'Andere privatwirtschaftliche Akteure')], max_length=40, null=True, verbose_name='Eigentümerkategorie'),
        ),
        migrations.AddField(
            model_name='bioentry',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Postleitzahl'),
        ),
        migrations.AddField(
            model_name='bioentry',
            name='tenure',
            field=models.CharField(blank=True, choices=[('rent', 'Miete'), ('ownership', 'Eigentum')], max_length=20, null=True, verbose_name='Miete / Eigentum'),
        ),
        migrations.AddField(
            model_name='bioentry',
            name='typology',
            field=models.CharField(blank=True, choices=[('house', 'Haus'), ('dormitory', 'Wohnheim'), ('1_room', '1 Zimmer Wohnung'), ('2_rooms', '2 Zi'), ('3_rooms', '3 Zi'), ('4_rooms', '4 Zi'), ('5_rooms', '5 Zi'), ('more_than_5_rooms', 'Mehr als 5 Zimmer')], max_length=30, null=True, verbose_name='Typologie'),
        ),
    ]
