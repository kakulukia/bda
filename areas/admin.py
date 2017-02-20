from django.contrib import admin

# Register your models here.
from .models import AreaBio, BioEntry


@admin.register(AreaBio)
class AreaBioAdmin(admin.ModelAdmin):
    list_display = ['id', '__str__']


@admin.register(BioEntry)
class BioEntryAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'description']
    actions = None
