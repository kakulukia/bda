from django.db import migrations


def convert_calendar_years_to_ages(apps, schema_editor):
    AreaBio = apps.get_model('areas', 'AreaBio')
    BioEntry = apps.get_model('areas', 'BioEntry')

    for bio in AreaBio.objects.filter(birth_year__isnull=False):
        birth_year = bio.birth_year
        for entry in BioEntry.objects.filter(area_bio=bio):
            if entry.year_from > 1900:
                entry.year_from = entry.year_from - birth_year
                entry.year_to = entry.year_to - birth_year
                entry.save()


class Migration(migrations.Migration):

    dependencies = [
        ('areas', '0023_alter_areabio_options'),
    ]

    operations = [
        migrations.RunPython(convert_calendar_years_to_ages, migrations.RunPython.noop),
        migrations.RenameField(
            model_name='bioentry',
            old_name='year_from',
            new_name='age_from',
        ),
        migrations.RenameField(
            model_name='bioentry',
            old_name='year_to',
            new_name='age_to',
        ),
        migrations.AlterModelOptions(
            name='bioentry',
            options={
                'ordering': ['age_from'],
                'verbose_name': 'Biografieeintrag',
                'verbose_name_plural': 'Biografieeinträge',
            },
        ),
        migrations.RemoveField(
            model_name='areabio',
            name='birth_year',
        ),
    ]
