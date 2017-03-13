from django.contrib import admin

# Register your models here.
from .models import AreaBio, BioEntry


@admin.register(AreaBio)
class AreaBioAdmin(admin.ModelAdmin):
    list_display = ['created', 'id', '__str__', 'entries_count', 'published']
    list_editable = ['published']
    list_filter = ['country', 'published']

    def entries_count(self, obj):
        return obj.entries.count()

    def has_add_permission(self, request):
        return False


@admin.register(BioEntry)
class BioEntryAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'description', 'area_bio']
    actions = None
    search_fields = ['area_bio__name']
