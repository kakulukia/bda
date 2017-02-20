from django.forms import modelformset_factory
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic import TemplateView
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route

from areas.forms import EmailForm, AreaBioForm, EntryForm
from areas.serializers import AreaBioSerializer
from areas.models import AreaBio, BioEntry


class AreaBioView(TemplateView):
    template_name = 'detail.pug'

    def get(self, request, *args, **kwags):
        context = {}

        return self.render_to_response(context)
    # queryset = AreaBio.data.all()
    #
    # def get_context_data(self, **kwargs):
    #     context = super(AreaBioView, self).get_context_data(**kwargs)
    #
    #     # EMAIL FORM
    #     context['email_form'] = EmailForm(initial=self.request.user.email)
    #
    #     # AREA BIO FORM
    #     context['form'] = AreaBioForm(instance=self.object)
    #
    #     # ENTRY FORMSET
    #     entries = self.object.entries.count()
    #     extra = max(entries, 4) + 1
    #
    #     # noinspection PyPep8Naming
    #     EntryFormSet = modelformset_factory(BioEntry, form=EntryForm, extra=extra)
    #     entry_formset = EntryFormSet(queryset=self.object.entries.all())
    #     context['entry_formset'] = entry_formset
    #
    #     return context
    #
    # def post(self):
    #     context
    #     return render(request, self.template_name, context)


class BioListView(ListView):
    queryset = AreaBio.data.all()
    context_object_name = 'book_list'
    template_name = 'area_list.pug'


def add_bio(request):

    bio_uuid = request.session.get('bio_id')
    if not bio_uuid or True:
        bio = AreaBio()
        bio.save()
        request.session['bio_uuid'] = str(bio.uuid)
        bio_uuid = request.session.get('bio_uuid')

    bio = AreaBio.data.get(uuid=bio_uuid)

    return redirect(reverse('detail', args=[bio.id]))


class AreaBioViewSet(viewsets.ModelViewSet):
    queryset = AreaBio.data.all()
    serializer_class = AreaBioSerializer

    @detail_route(methods=['get',])
    def entries(self, request, pk=None):
        bio = AreaBio.data.get(pk=pk)
        entries = bio.entries.all()

        return
