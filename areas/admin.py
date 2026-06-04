from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.forms.models import BaseInlineFormSet

# Register your models here.
from .models import AreaBio, BioEntry

admin.site.enable_nav_sidebar = False
admin.site.site_header = 'Wohnbiografien Admin'
admin.site.site_title = 'Wohnbiografien Admin'
admin.site.index_title = 'Website-Verwaltung'


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = DjangoUserAdmin.list_display + ('is_superuser',)
    list_filter = tuple(dict.fromkeys(DjangoUserAdmin.list_filter + ('is_staff', 'is_superuser')))


class BioEntryInline(admin.StackedInline):
    model = BioEntry
    extra = 0
    fields = [
        (
            'age_from',
            'age_to',
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
    ordering = ['age_from']

    @admin.display(description='Platz pro person')
    def display_living_space_per_person(self, obj):
        if not obj or not obj.pk:
            return '-'
        value = obj.living_space_per_person
        if value is None:
            return '-'
        return '{:.2f} m²/person'.format(value)


class BioEntryInlineFormSet(BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if index is not None and index < self.initial_form_count():
            return kwargs

        copied_initial = self._get_copied_initial()
        if copied_initial:
            kwargs['initial'] = {**kwargs.get('initial', {}), **copied_initial}
        return kwargs

    def _get_copied_initial(self):
        if not getattr(self.instance, 'pk', None):
            return {}

        last_entry = self.instance.entries.order_by('-age_from', '-age_to', '-pk').first()
        if not last_entry:
            return {}

        return {
            'age_from': last_entry.age_to,
            'age_to': None,
            'living_space': last_entry.living_space,
            'number_of_people': last_entry.number_of_people,
            'description': '',
            'location': last_entry.location,
            'postal_code': last_entry.postal_code,
            'typology': last_entry.typology,
            'tenure': last_entry.tenure,
            'owner_category': last_entry.owner_category,
            'construction_year_category': last_entry.construction_year_category,
            'country_if_not_germany': last_entry.country_if_not_germany,
        }


BioEntryInline.formset = BioEntryInlineFormSet


@admin.register(AreaBio)
class AreaBioAdmin(admin.ModelAdmin):
    list_display = ['created', '__str__', 'user', 'entries_count']
    list_filter = ['country', 'gender', 'user']
    @admin.display(description='Nutzer')
    def user_display(self, obj):
        return str(obj.user) if obj.user else '-'

    def get_readonly_fields(self, request, obj=None):
        return ['user_display'] if obj else []

    def get_exclude(self, request, obj=None):
        return ['user']
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

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def response_change(self, request, obj):
        if '_continue' in request.POST:
            request.session['areas_areabio_scroll_to_last_inline'] = True
        return super().response_change(request, obj)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['scroll_to_last_inline_after_save'] = request.session.pop(
            'areas_areabio_scroll_to_last_inline',
            False,
        )
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)
