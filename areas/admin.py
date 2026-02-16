from django.contrib import admin

# Register your models here.
from .models import AreaBio, BioEntry

admin.site.enable_nav_sidebar = False


class BioEntryInline(admin.StackedInline):
    model = BioEntry
    extra = 0
    fields = [
        (
            'year_from',
            'year_to',
            'living_space',
            'number_of_people',
            'display_living_space_per_person',
            'description',
        ),
        (
            'location',
            'postal_code',
            'typology',
            'tenure',
            'owner_category',
            'construction_year_category',
            'country_if_not_germany',
        ),
    ]
    readonly_fields = ['display_living_space_per_person']
    ordering = ['year_from']

    @admin.display(description='Platz pro person')
    def display_living_space_per_person(self, obj):
        if not obj or not obj.pk:
            return '-'
        value = obj.living_space_per_person
        if value is None:
            return '-'
        return '{:.2f} m²/person'.format(value)


@admin.register(AreaBio)
class AreaBioAdmin(admin.ModelAdmin):
    list_display = ['created', '__str__', 'entries_count', 'published']
    list_filter = ['published', 'country']
    inlines = [BioEntryInline]
    actions = None

    search_fields = ['country', 'entries__location', 'entries__postal_code', 'name']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(user=request.user)

    @admin.display(description='Anzahl Einträge')
    def entries_count(self, obj):
        return obj.entries.count()

    def has_add_permission(self, request):
        return False
