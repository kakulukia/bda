from django.contrib import admin

# Register your models here.
from .models import AreaBio, BioEntry


@admin.register(AreaBio)
class AreaBioAdmin(admin.ModelAdmin):
    list_display = ['id', '__str__', 'entries_count', 'published']
    list_editable = ['published']
    list_filter = ['country']

    def entries_count(self, obj):
        return obj.entries.count()


@admin.register(BioEntry)
class BioEntryAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'description', 'area_bio']
    actions = None
    search_fields = ['area_bio__name']
