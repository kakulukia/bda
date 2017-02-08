from django.contrib import admin

# Register your models here.
from .models import AreaBio, BioEntry


@admin.register(AreaBio)
class AreaBioAdmin(admin.ModelAdmin):
    pass


@admin.register(BioEntry)
class BioEntryAdmin(admin.ModelAdmin):
    pass
