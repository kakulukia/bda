# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


def assign_existing_area_bios_to_user_1(apps, schema_editor):
    AreaBio = apps.get_model('areas', 'AreaBio')
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(app_label, model_name)

    user = User.objects.filter(pk=1).first()
    if user is None:
        username_field = getattr(User, 'USERNAME_FIELD', None)
        user_kwargs = {}
        if username_field:
            user_kwargs[username_field] = 'user1'
        user = User(pk=1, **user_kwargs)
        user.save()

    AreaBio.objects.filter(user__isnull=True).update(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('areas', '0017_alter_areabio_id_alter_bioentry_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='areabio',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='area_bios', to=settings.AUTH_USER_MODEL, verbose_name='Nutzer'),
        ),
        migrations.RunPython(assign_existing_area_bios_to_user_1, migrations.RunPython.noop),
    ]
