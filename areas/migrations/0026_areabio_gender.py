from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('areas', '0025_alter_bioentry_age_from_alter_bioentry_age_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='areabio',
            name='gender',
            field=models.CharField(
                choices=[('female', 'Weiblich'), ('male', 'Männlich')],
                help_text='Wird für die Lebenserwartungs-Projektion verwendet.',
                max_length=10,
                null=True,
                verbose_name='Geschlecht',
            ),
        ),
    ]
